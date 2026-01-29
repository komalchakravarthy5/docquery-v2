"""
FAISS Index Service
Manages FAISS vector indices for similarity search.
"""

import faiss
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from app.config import get_settings

settings = get_settings()


class FAISSService:
    """Manages FAISS indices for document embeddings"""
    
    def __init__(self):
        """Initialize FAISS service"""
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        self.indices = {}  # Cache for loaded indices {document_id: index}
    
    def create_index(self, document_id: str) -> faiss.IndexFlatL2:
        """
        Create a new FAISS index for a document.
        
        Args:
            document_id: Unique document identifier
            
        Returns:
            FAISS index instance
        """
        # Create L2 (Euclidean distance) index
        index = faiss.IndexFlatL2(self.embedding_dim)
        self.indices[document_id] = index
        return index
    
    def add_embeddings(self, document_id: str, embeddings: np.ndarray):
        """
        Add embeddings to document's FAISS index.
        
        Args:
            document_id: Document identifier
            embeddings: Numpy array of shape (num_chunks, embedding_dim)
        """
        # Get or create index
        if document_id not in self.indices:
            self.create_index(document_id)
        
        index = self.indices[document_id]
        
        # Ensure embeddings are float32 (FAISS requirement)
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        
        # Add to index
        index.add(embeddings)
    
    def save_index(self, document_id: str, index_path: str):
        """
        Save FAISS index to disk.
        
        Args:
            document_id: Document identifier
            index_path: Path to save the index
        """
        if document_id not in self.indices:
            raise ValueError(f"No index found for document: {document_id}")
        
        index = self.indices[document_id]
        
        # Create directory if needed
        Path(index_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save index
        faiss.write_index(index, index_path)
    
    def load_index(self, document_id: str, index_path: str) -> faiss.IndexFlatL2:
        """
        Load FAISS index from disk.
        
        Args:
            document_id: Document identifier
            index_path: Path to the index file
            
        Returns:
            Loaded FAISS index
        """
        if not Path(index_path).exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
        
        # Load index
        index = faiss.read_index(index_path)
        self.indices[document_id] = index
        return index
    
    def search(
        self,
        document_id: str,
        query_embedding: np.ndarray,
        top_k: int = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for similar embeddings in the index.
        
        Args:
            document_id: Document identifier
            query_embedding: Query embedding vector of shape (embedding_dim,)
            top_k: Number of results to return (default from config)
            
        Returns:
            Tuple of (distances, indices)
            - distances: Array of shape (top_k,) with L2 distances
            - indices: Array of shape (top_k,) with chunk indices
        """
        if document_id not in self.indices:
            raise ValueError(f"No index loaded for document: {document_id}")
        
        if top_k is None:
            top_k = settings.top_k_retrieval
        
        index = self.indices[document_id]
        
        # Ensure query is 2D array and float32
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)
        
        # Search
        distances, indices = index.search(query_embedding, top_k)
        
        # Return flattened results (since we only query one vector)
        return distances[0], indices[0]
    
    def get_index_size(self, document_id: str) -> int:
        """
        Get number of vectors in the index.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Number of vectors in index
        """
        if document_id not in self.indices:
            return 0
        return self.indices[document_id].ntotal
    
    def remove_index(self, document_id: str):
        """
        Remove index from memory cache.
        
        Args:
            document_id: Document identifier
        """
        if document_id in self.indices:
            del self.indices[document_id]
    
    def index_exists(self, document_id: str) -> bool:
        """
        Check if index is loaded in memory.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if index is loaded, False otherwise
        """
        return document_id in self.indices


# Singleton instance
faiss_service = FAISSService()
