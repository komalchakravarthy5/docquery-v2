from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.config import get_settings
from app.services.embedding_service import embedding_service
from app.services.gemini_service import gemini_service

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Check if models are loaded
    embedding_loaded = embedding_service.is_model_loaded()
    gemini_loaded = gemini_service.is_initialized()
    models_loaded = embedding_loaded or gemini_loaded
    
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        models_loaded=models_loaded
    )

