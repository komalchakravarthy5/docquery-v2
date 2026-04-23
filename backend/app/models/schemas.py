"""API request and response schemas."""

from typing import List, Optional
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
    source_filter: Optional[str] = None


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
    latency_ms: Optional[float] = None
    grounding_score: Optional[float] = None


class MetricsTrendPoint(BaseModel):
    latency_ms: float
    avg_relevance_score: float
    num_citations: int
    answer_found: bool
    grounding_score: Optional[float] = None


class DocumentMetricsResponse(BaseModel):
    document_id: str
    total_queries: int
    avg_latency_ms: float
    avg_relevance_score: float
    avg_citations: float
    query_success_rate: float
    avg_grounding_score: float
    trend: List[MetricsTrendPoint]


class DocumentInfo(BaseModel):
    id: str
    filename: str
    upload_timestamp: str
    num_pages: int
    num_chunks: int


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
