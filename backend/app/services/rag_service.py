"""
RAG Service
Orchestrates the complete Retrieval-Augmented Generation pipeline.
"""

from typing import List, Optional
import time
import math
import re
from app.models.schemas import QueryResponse, Citation
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service
from app.services.database import database_service
from app.services.gemini_service import gemini_service
from app.services.storage import storage_service
from app.services.metrics_service import metrics_service
from app.config import get_settings

settings = get_settings()


class RAGService:
    """Orchestrates the complete RAG pipeline"""

    SUMMARY_QUERY_HINTS = (
        "summarize",
        "summary",
        "key findings",
        "compare",
        "overview",
    )
    ANSWER_NOT_FOUND_PATTERNS = (
        "i cannot find this information",
        "not found in the provided context",
        "not available in the provided context",
        "insufficient information in the context",
    )

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {t for t in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(t) > 2}

    @staticmethod
    def _normalize_filename(value: str) -> str:
        if not value:
            return ""
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    def _keyword_overlap_score(self, query: str, chunk_text: str) -> float:
        q = self._tokenize(query)
        c = self._tokenize(chunk_text)
        if not q or not c:
            return 0.0
        common = len(q & c)
        return common / max(1, len(q))

    def _grounding_score(self, answer: str, chunks: List[dict]) -> float:
        answer_tokens = self._tokenize(answer)
        if not answer_tokens:
            return 0.0
        context_tokens = set()
        for chunk in chunks:
            context_tokens |= self._tokenize(chunk.get("text", ""))
        if not context_tokens:
            return 0.0
        covered = len(answer_tokens & context_tokens)
        return round(covered / max(1, len(answer_tokens)), 3)

    def _select_context_chunks(self, chunks: List[dict]) -> List[dict]:
        selected: List[dict] = []
        running_chars = 0

        for chunk in chunks:
            text = chunk.get("text", "")
            if not text:
                continue
            next_size = len(text)
            if selected and running_chars + next_size > settings.max_context_chars:
                break
            selected.append(chunk)
            running_chars += next_size
            if len(selected) >= settings.max_context_chunks:
                break
        return selected

    def _is_answer_found(self, answer: str, citations: List[Citation], grounding_score: float) -> bool:
        normalized = (answer or "").strip().lower()
        if not normalized:
            return False
        if any(pattern in normalized for pattern in self.ANSWER_NOT_FOUND_PATTERNS):
            return False
        if not citations:
            return False
        return grounding_score >= 0.05

    def _build_fallback_answer(self, query: str, chunks: List[dict], citations: List[Citation]) -> str:
        if not citations or not chunks:
            return "I cannot find this information in the document."
        query_tokens = self._tokenize(query)
        candidates: List[tuple[float, str]] = []

        for chunk in chunks[:8]:
            text = chunk.get("text", "")
            if not text:
                continue
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for sentence in sentences:
                cleaned = sentence.strip()
                if len(cleaned) < 40:
                    continue
                overlap = len(query_tokens & self._tokenize(cleaned))
                score = (overlap * 2) + min(len(cleaned), 240) / 240
                candidates.append((score, cleaned))

        candidates.sort(key=lambda x: x[0], reverse=True)
        selected = []
        seen = set()
        for _, sentence in candidates:
            key = sentence.lower()
            if key in seen:
                continue
            selected.append(sentence)
            seen.add(key)
            if len(selected) >= 3:
                break

        if selected:
            return " ".join(selected)

        return (
            citations[0].text_snippet
            if citations
            else "I cannot find this information in the document."
        )

    async def query_document(
        self,
        document_id: str,
        query: str,
        top_k: int = None,
        source_filter: Optional[str] = None,
    ) -> QueryResponse:
        """Execute complete RAG pipeline for a query."""
        start_time = time.perf_counter()
        if top_k is None:
            top_k = settings.top_k_retrieval

        # Ensure DB is ready
        await database_service.initialize()

        # Step 1: Validate document exists and adapt retrieval size for small docs
        doc = await database_service.get_document(document_id)
        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        num_chunks = int(doc.get("num_chunks", 0))
        source_files = [s.strip() for s in (doc.get("filename") or "").split(" | ") if s.strip()]
        num_sources = max(1, len(source_files))

        # Natural-language source selector fallback for queries like "first/second document"
        if not source_filter and source_files:
            q_lower = query.lower()
            ordinal_map = {
                "first": 0,
                "1st": 0,
                "second": 1,
                "2nd": 1,
                "third": 2,
                "3rd": 2,
            }
            for token, idx in ordinal_map.items():
                if f"{token} document" in q_lower and idx < len(source_files):
                    source_filter = source_files[idx]
                    break
        if num_chunks <= 0:
            raise ValueError(f"No indexed chunks found for document: {document_id}")

        adaptive_top_k = min(max(1, top_k), num_chunks)
        query_is_summary = any(hint in query.lower() for hint in self.SUMMARY_QUERY_HINTS)

        # Broaden retrieval only for true cross-document synthesis.
        # When a source filter is active, prefer a tighter candidate set for speed/precision.
        if source_filter:
            if query_is_summary:
                adaptive_top_k = min(max(adaptive_top_k, 8), num_chunks)
            else:
                adaptive_top_k = min(max(adaptive_top_k, 6), num_chunks)
        else:
            adaptive_top_k = min(max(adaptive_top_k, num_sources * 6), num_chunks)
            if query_is_summary:
                adaptive_top_k = min(max(adaptive_top_k, 12), num_chunks)

        # Step 2: Load FAISS index if not already loaded
        if not faiss_service.index_exists(document_id):
            index_path = storage_service.get_faiss_index_path(document_id)
            if not storage_service.faiss_index_exists(document_id):
                raise ValueError(f"FAISS index not found for document: {document_id}")
            faiss_service.load_index(document_id, index_path)

        # Step 3: Generate query embedding
        query_embedding = embedding_service.encode_text(query)

        # Step 4: Search FAISS index
        search_k = min(num_chunks, max(adaptive_top_k * 2, 12))
        distances, indices = faiss_service.search(
            document_id=document_id,
            query_embedding=query_embedding,
            top_k=search_k
        )

        if len(indices) == 0:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            metrics_service.record_query(document_id, {
                "latency_ms": latency_ms,
                "avg_relevance_score": 0.0,
                "num_citations": 0,
                "answer_found": False,
                "grounding_score": 0.0,
            })
            await database_service.insert_query_metric(document_id, latency_ms, 0.0, 0, False, 0.0)
            return QueryResponse(
                answer="I cannot find this information in the document.",
                citations=[],
                document_id=document_id,
                query=query,
                latency_ms=latency_ms,
                grounding_score=0.0,
            )

        # Step 5: Retrieve chunks from database
        raw_indices = [int(idx) for idx in indices.tolist()]
        raw_distances = [float(d) for d in distances.tolist()]
        chunk_indices = [idx for idx in raw_indices if idx >= 0]
        if not chunk_indices:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            metrics_service.record_query(document_id, {
                "latency_ms": latency_ms,
                "avg_relevance_score": 0.0,
                "num_citations": 0,
                "answer_found": False,
                "grounding_score": 0.0,
            })
            await database_service.insert_query_metric(document_id, latency_ms, 0.0, 0, False, 0.0)
            return QueryResponse(
                answer="I cannot find this information in the document.",
                citations=[],
                document_id=document_id,
                query=query,
                latency_ms=latency_ms,
                grounding_score=0.0,
            )

        chunks = await database_service.get_chunks_by_indices(document_id, chunk_indices)
        distance_by_idx = {
            idx: dist for idx, dist in zip(raw_indices, raw_distances) if idx >= 0
        }

        # Sort chunks by relevance (same order as FAISS results)
        chunks_dict = {chunk["chunk_index"]: chunk for chunk in chunks}
        sorted_chunks = [chunks_dict[idx] for idx in chunk_indices if idx in chunks_dict]

        # Hybrid rerank: combine semantic rank with keyword overlap
        ranked = []
        for rank, chunk in enumerate(sorted_chunks):
            distance = distance_by_idx.get(chunk.get("chunk_index"), 1e6)
            semantic_score = 1.0 / (1.0 + max(0.0, distance))
            rank_prior_score = 1.0 / (1.0 + math.log2(rank + 2))
            lexical_score = self._keyword_overlap_score(query, chunk.get("text", ""))
            hybrid_score = (
                (0.55 * semantic_score)
                + (0.30 * lexical_score)
                + (0.15 * rank_prior_score)
            )
            ranked.append((hybrid_score, chunk, distance))
        ranked.sort(key=lambda x: x[0], reverse=True)
        selected_candidates = ranked[:adaptive_top_k]

        if source_filter:
            target_raw = source_filter.strip().lower()
            target_norm = self._normalize_filename(source_filter)

            exact_filtered = [
                candidate for candidate in selected_candidates
                if (candidate[1].get("source_file") or "").strip().lower() == target_raw
            ]
            if exact_filtered:
                selected_candidates = exact_filtered
            else:
                # Fallback for filename variations (spaces, punctuation, accidental truncation)
                fuzzy_filtered = []
                for candidate in selected_candidates:
                    source_name = (candidate[1].get("source_file") or "").strip()
                    source_norm = self._normalize_filename(source_name)
                    if source_norm and (target_norm in source_norm or source_norm in target_norm):
                        fuzzy_filtered.append(candidate)
                selected_candidates = fuzzy_filtered

        sorted_chunks = [candidate[1] for candidate in selected_candidates]

        if not sorted_chunks:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response = QueryResponse(
                answer=f"I could not find matching content for source filter: {source_filter}.",
                citations=[],
                document_id=document_id,
                query=query,
                latency_ms=latency_ms,
                grounding_score=0.0,
            )
            metrics_service.record_query(document_id, {
                "latency_ms": latency_ms,
                "avg_relevance_score": 0.0,
                "num_citations": 0,
                "answer_found": False,
                "grounding_score": 0.0,
            })
            await database_service.insert_query_metric(document_id, latency_ms, 0.0, 0, False, 0.0)
            return response

        # Step 6: Generate answer using Gemini
        context_chunks = self._select_context_chunks(sorted_chunks)
        try:
            answer = gemini_service.generate_answer(
                query=query,
                context_chunks=context_chunks,
                max_context_length=settings.max_context_chars,
            )
        except Exception:
            answer = self._build_fallback_answer(
                query=query,
                chunks=context_chunks,
                citations=self._create_citations(selected_candidates),
            )

        # Step 7: Create citations
        citations = self._create_citations(selected_candidates)

        # Step 8: Return response
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        grounding_score = self._grounding_score(answer, context_chunks)
        answer_found = self._is_answer_found(answer, citations, grounding_score)

        response = QueryResponse(
            answer=answer,
            citations=citations,
            document_id=document_id,
            query=query,
            latency_ms=latency_ms,
            grounding_score=grounding_score,
        )

        avg_relevance_score = (
            round(sum(citation.relevance_score for citation in citations) / len(citations), 3)
            if citations else 0.0
        )
        metrics_service.record_query(document_id, {
            "latency_ms": latency_ms,
            "avg_relevance_score": avg_relevance_score,
            "num_citations": len(citations),
            "answer_found": answer_found,
            "grounding_score": grounding_score,
        })
        await database_service.insert_query_metric(
            document_id=document_id,
            latency_ms=latency_ms,
            avg_relevance_score=avg_relevance_score,
            num_citations=len(citations),
            answer_found=answer_found,
            grounding_score=grounding_score,
        )

        return response

    def _create_citations(
        self,
        candidates: List[tuple[float, dict, float]],
    ) -> List[Citation]:
        """Create citation objects from retrieved chunks."""
        citations = []

        for _, chunk, distance in candidates:
            if len(citations) >= settings.max_citations:
                break
            relevance_score = 1.0 / (1.0 + max(0.0, float(distance)))

            source_file = chunk.get("source_file")
            source_page_number = chunk.get("source_page_number", chunk.get("page_number"))

            text_snippet = chunk["text"][:200]
            if len(chunk["text"]) > 200:
                text_snippet += "..."

            if source_file:
                text_snippet = f"[{source_file} p.{source_page_number}] {text_snippet}"

            citations.append(Citation(
                chunk_id=chunk["chunk_index"],
                page_number=chunk["page_number"],
                text_snippet=text_snippet,
                relevance_score=round(relevance_score, 3)
            ))

        return citations


# Singleton instance
rag_service = RAGService()
