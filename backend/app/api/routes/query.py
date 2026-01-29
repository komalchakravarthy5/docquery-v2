from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse, DocumentInfo
from app.services.rag_service import rag_service
from app.services.database import database_service

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    """
    Query a document using natural language
    
    This endpoint will:
    1. Generate embedding for the query
    2. Retrieve top-k relevant chunks from FAISS
    3. Use RAG to generate an answer with citations
    """
    try:
        # Execute RAG pipeline
        response = await rag_service.query_document(
            document_id=request.document_id,
            query=request.query
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


@router.get("/documents")
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
