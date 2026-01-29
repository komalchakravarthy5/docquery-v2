"""
Embedding Service
Generates vector embeddings using sentence-transformers.
"""

from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    """Handles text embedding generation using sentence-transformers"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one model instance"""
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize embedding service (lazy loading)"""
        self.model_name = settings.embedding_model
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
    
    def _load_model(self):
        """Lazy load the embedding model"""
        if self._model is None:
            print(f"📦 Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            print(f"✅ Embedding model loaded successfully")
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array of shape (embedding_dim,)
        """
        self._load_model()
        
        # Generate embedding
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding
    
    def encode_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = False) -> np.ndarray:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
            
        Returns:
            Numpy array of shape (num_texts, embedding_dim)
        """
        self._load_model()
        
        # Generate embeddings in batches
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings.
        
        Returns:
            Embedding dimension
        """
        return self.embedding_dim
    
    def is_model_loaded(self) -> bool:
        """
        Check if model is loaded in memory.
        
        Returns:
            True if model is loaded, False otherwise
        """
        return self._model is not None


# Singleton instance
embedding_service = EmbeddingService()
