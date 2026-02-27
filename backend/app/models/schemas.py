"""API request and response schemas."""

from typing import List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app_name: str
    models_loaded: bool


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    num_pages: int
    num_chunks: int
    message: str


class QueryRequest(BaseModel):
    document_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=2, max_length=2000)


class Citation(BaseModel):
    chunk_id: int
    page_number: int
    text_snippet: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    document_id: str
    query: str


class DocumentInfo(BaseModel):
    id: str
    filename: str
    upload_timestamp: str
    num_pages: int
    num_chunks: int


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
