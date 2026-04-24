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

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {t for t in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(t) > 2}

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
        adaptive_top_k = min(max(adaptive_top_k, num_sources * 6), num_chunks)
        if any(hint in query.lower() for hint in self.SUMMARY_QUERY_HINTS):
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
        search_k = min(num_chunks, max(adaptive_top_k * 4, 20))
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
        chunk_indices = [int(idx) for idx in indices.tolist() if int(idx) >= 0]
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

        # Sort chunks by relevance (same order as FAISS results)
        chunks_dict = {chunk["chunk_index"]: chunk for chunk in chunks}
        sorted_chunks = [chunks_dict[idx] for idx in chunk_indices if idx in chunks_dict]

        # Hybrid rerank: combine semantic rank with keyword overlap
        ranked = []
        for rank, chunk in enumerate(sorted_chunks):
            semantic_score = 1.0 / (1.0 + math.log2(rank + 2))
            lexical_score = self._keyword_overlap_score(query, chunk.get("text", ""))
            hybrid_score = (0.65 * semantic_score) + (0.35 * lexical_score)
            ranked.append((hybrid_score, chunk))
        ranked.sort(key=lambda x: x[0], reverse=True)
        sorted_chunks = [chunk for _, chunk in ranked[:adaptive_top_k]]

        if source_filter:
            target = source_filter.strip().lower()
            sorted_chunks = [
                chunk for chunk in sorted_chunks
                if (chunk.get("source_file") or "").strip().lower() == target
            ]

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
        answer = gemini_service.generate_answer(
            query=query,
            context_chunks=sorted_chunks
        )

        # Step 7: Create citations
        citations = self._create_citations(sorted_chunks, distances)

        # Step 8: Return response
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        response = QueryResponse(
            answer=answer,
            citations=citations,
            document_id=document_id,
            query=query,
            latency_ms=latency_ms,
            grounding_score=self._grounding_score(answer, sorted_chunks),
        )

        avg_relevance_score = (
            round(sum(citation.relevance_score for citation in citations) / len(citations), 3)
            if citations else 0.0
        )
        metrics_service.record_query(document_id, {
            "latency_ms": latency_ms,
            "avg_relevance_score": avg_relevance_score,
            "num_citations": len(citations),
            "answer_found": "I cannot find this information" not in answer,
            "grounding_score": response.grounding_score or 0.0,
        })
        await database_service.insert_query_metric(
            document_id=document_id,
            latency_ms=latency_ms,
            avg_relevance_score=avg_relevance_score,
            num_citations=len(citations),
            answer_found="I cannot find this information" not in answer,
            grounding_score=response.grounding_score or 0.0,
        )

        return response

    def _create_citations(
        self,
        chunks: List[dict],
        distances: List[float]
    ) -> List[Citation]:
        """Create citation objects from retrieved chunks."""
        citations = []

        for i, chunk in enumerate(chunks):
            if len(citations) >= settings.max_citations:
                break
            distance = float(distances[i]) if i < len(distances) else 10.0
            relevance_score = max(0.0, 1.0 - (distance / 10.0))

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
