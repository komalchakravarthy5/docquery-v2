from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import QueryRequest, QueryResponse, DocumentInfo, DocumentListResponse, DocumentMetricsResponse
from app.services.rag_service import rag_service
from app.services.database import database_service
from app.services.metrics_service import metrics_service
from app.config import get_settings
import time

settings = get_settings()
_rate_limit_window = {}

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest, http_request: Request):
    """
    Query a document using natural language
    
    This endpoint will:
    1. Generate embedding for the query
    2. Retrieve top-k relevant chunks from FAISS
    3. Use RAG to generate an answer with citations
    """
    try:
        # Basic in-memory rate limiting per client IP
        client_ip = http_request.client.host if http_request.client else "unknown"
        now = time.time()
        window = _rate_limit_window.get(client_ip, [])
        window = [ts for ts in window if now - ts < 60]
        if len(window) >= settings.query_rate_limit_per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please retry in a minute.")
        window.append(now)
        _rate_limit_window[client_ip] = window

        # Execute RAG pipeline
        response = await rag_service.query_document(
            document_id=request.document_id,
            query=request.query,
            source_filter=request.source_filter,
        )
        
        return response
        
    except ValueError as e:
        # Document not found or invalid
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Other errors
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded documents"""
    try:
        # Initialize database if needed
        await database_service.initialize()
        
        # Get all documents
        documents = await database_service.list_documents()
        
        # Convert to response format
        document_list = [
            DocumentInfo(
                id=doc["id"],
                filename=doc["filename"],
                upload_timestamp=doc["upload_timestamp"],
                num_pages=doc["num_pages"],
                num_chunks=doc["num_chunks"]
            )
            for doc in documents
        ]
        
        return {"documents": document_list}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving documents: {str(e)}"
        )


@router.get("/metrics/{document_id}", response_model=DocumentMetricsResponse)
async def get_document_metrics(document_id: str):
    """Get query efficiency metrics for a workspace."""
    try:
        await database_service.initialize()
        doc = await database_service.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        runtime_metrics = metrics_service.get_document_metrics(document_id)
        persisted = await database_service.get_query_metrics(document_id, limit=200)
        if persisted:
            runtime_metrics["avg_latency_ms"] = round(sum(m["latency_ms"] for m in persisted) / len(persisted), 2)
            runtime_metrics["avg_relevance_score"] = round(sum(m["avg_relevance_score"] for m in persisted) / len(persisted), 3)
            runtime_metrics["avg_citations"] = round(sum(m["num_citations"] for m in persisted) / len(persisted), 2)
            runtime_metrics["query_success_rate"] = round(sum(m["answer_found"] for m in persisted) / len(persisted), 3)
            runtime_metrics["avg_grounding_score"] = round(sum(m["grounding_score"] for m in persisted) / len(persisted), 3)
            runtime_metrics["total_queries"] = len(persisted)
            runtime_metrics["trend"] = [
                {
                    "latency_ms": m["latency_ms"],
                    "avg_relevance_score": m["avg_relevance_score"],
                    "num_citations": m["num_citations"],
                    "answer_found": bool(m["answer_found"]),
                    "grounding_score": m["grounding_score"],
                }
                for m in reversed(persisted[:20])
            ]
        return runtime_metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")
