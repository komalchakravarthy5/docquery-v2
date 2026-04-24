from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # API Settings
    app_name: str = "DocQuery"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Google Gemini API
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash-002"
    gemini_temperature: float = 0.2  # Low temperature for factual RAG responses
    
    # CORS
    allowed_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "http://localhost:3000,"
        "http://127.0.0.1:3000"
    )
    
    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    # Storage Paths
    upload_dir: str = "./data/uploads"
    faiss_index_dir: str = "./data/faiss_index"
    database_path: str = "./data/metadata.db"
    
    # Model Settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k_retrieval: int = 5
    max_citations: int = 5
    max_upload_files: int = 3
    max_file_size_mb: int = 25
    max_chunks_per_workspace: int = 5000
    
    # Chunking Settings
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Security / rate-limiting
    query_rate_limit_per_minute: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
