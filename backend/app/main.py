from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.api.routes import health, upload, query

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle hooks."""
    print(f"🚀 {settings.app_name} is starting...")
    print(f"📍 Server running on {settings.host}:{settings.port}")
    yield
    print(f"👋 {settings.app_name} is shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Intelligent Document Chat Assistant with RAG",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(query.router, prefix="/api", tags=["Query"])
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
