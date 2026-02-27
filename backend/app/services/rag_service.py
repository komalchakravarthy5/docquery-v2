"""
RAG Service
Orchestrates the complete Retrieval-Augmented Generation pipeline.
"""

from typing import List
from app.models.schemas import QueryResponse, Citation
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service
from app.services.database import database_service
from app.services.gemini_service import gemini_service
from app.services.storage import storage_service
from app.config import get_settings

settings = get_settings()


class RAGService:
    """Orchestrates the complete RAG pipeline"""

    async def query_document(
        self,
        document_id: str,
        query: str,
        top_k: int = None
    ) -> QueryResponse:
        """Execute complete RAG pipeline for a query."""
        if top_k is None:
            top_k = settings.top_k_retrieval

        # Ensure DB is ready
        await database_service.initialize()

        # Step 1: Validate document exists and adapt retrieval size for small docs
        doc = await database_service.get_document(document_id)
        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        num_chunks = int(doc.get("num_chunks", 0))
        if num_chunks <= 0:
            raise ValueError(f"No indexed chunks found for document: {document_id}")

        adaptive_top_k = min(max(1, top_k), num_chunks)

        # Step 2: Load FAISS index if not already loaded
        if not faiss_service.index_exists(document_id):
            index_path = storage_service.get_faiss_index_path(document_id)
            if not storage_service.faiss_index_exists(document_id):
                raise ValueError(f"FAISS index not found for document: {document_id}")
            faiss_service.load_index(document_id, index_path)

        # Step 3: Generate query embedding
        query_embedding = embedding_service.encode_text(query)

        # Step 4: Search FAISS index
        distances, indices = faiss_service.search(
            document_id=document_id,
            query_embedding=query_embedding,
            top_k=adaptive_top_k
        )

        if len(indices) == 0:
            return QueryResponse(
                answer="I cannot find this information in the document.",
                citations=[],
                document_id=document_id,
                query=query,
            )

        # Step 5: Retrieve chunks from database
        chunk_indices = [int(idx) for idx in indices.tolist() if int(idx) >= 0]
        if not chunk_indices:
            return QueryResponse(
                answer="I cannot find this information in the document.",
                citations=[],
                document_id=document_id,
                query=query,
            )

        chunks = await database_service.get_chunks_by_indices(document_id, chunk_indices)

        # Sort chunks by relevance (same order as FAISS results)
        chunks_dict = {chunk["chunk_index"]: chunk for chunk in chunks}
        sorted_chunks = [chunks_dict[idx] for idx in chunk_indices if idx in chunks_dict]

        # Step 6: Generate answer using Gemini
        answer = gemini_service.generate_answer(
            query=query,
            context_chunks=sorted_chunks
        )

        # Step 7: Create citations
        citations = self._create_citations(sorted_chunks, distances)

        # Step 8: Return response
        return QueryResponse(
            answer=answer,
            citations=citations,
            document_id=document_id,
            query=query
        )

    def _create_citations(
        self,
        chunks: List[dict],
        distances: List[float]
    ) -> List[Citation]:
        """Create citation objects from retrieved chunks."""
        citations = []

        for i, chunk in enumerate(chunks):
            distance = float(distances[i]) if i < len(distances) else 10.0
            relevance_score = max(0.0, 1.0 - (distance / 10.0))

            text_snippet = chunk["text"][:200]
            if len(chunk["text"]) > 200:
                text_snippet += "..."

            citations.append(Citation(
                chunk_id=chunk["chunk_index"],
                page_number=chunk["page_number"],
                text_snippet=text_snippet,
                relevance_score=round(relevance_score, 3)
            ))

        return citations


# Singleton instance
rag_service = RAGService()
