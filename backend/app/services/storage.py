"""
File Storage Service
Handles file system operations for uploaded PDFs and indices.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from app.config import get_settings

settings = get_settings()


class StorageService:
    """Manages file storage for uploaded documents"""
    
    def __init__(self):
        """Initialize storage service and create directories"""
        self.upload_dir = Path(settings.upload_dir)
        self.faiss_index_dir = Path(settings.faiss_index_dir)
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.faiss_index_dir.mkdir(parents=True, exist_ok=True)
    
    def save_uploaded_file(self, file_content: bytes, document_id: str, filename: str) -> str:
        """
        Save uploaded PDF file to storage.
        
        Args:
            file_content: Binary content of the file
            document_id: Unique document identifier
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        # Create filename with document ID to ensure uniqueness
        file_extension = Path(filename).suffix
        safe_filename = f"{document_id}{file_extension}"
        file_path = self.upload_dir / safe_filename
        
        # Write file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return str(file_path)
    
    def get_document_path(self, document_id: str) -> Optional[str]:
        """
        Get path to stored document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Path to document file or None if not found
        """
        # Try with .pdf extension
        pdf_path = self.upload_dir / f"{document_id}.pdf"
        if pdf_path.exists():
            return str(pdf_path)
        
        return None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete document file from storage.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if deleted, False if not found
        """
        file_path = self.get_document_path(document_id)
        if file_path and Path(file_path).exists():
            os.remove(file_path)
            return True
        return False
    
    def get_faiss_index_path(self, document_id: str) -> str:
        """
        Get path for FAISS index file.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Path where FAISS index should be stored
        """
        return str(self.faiss_index_dir / f"{document_id}.index")
    
    def faiss_index_exists(self, document_id: str) -> bool:
        """
        Check if FAISS index exists for document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if index exists, False otherwise
        """
        index_path = self.get_faiss_index_path(document_id)
        return Path(index_path).exists()
    
    def delete_faiss_index(self, document_id: str) -> bool:
        """
        Delete FAISS index file.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if deleted, False if not found
        """
        index_path = self.get_faiss_index_path(document_id)
        if Path(index_path).exists():
            os.remove(index_path)
            return True
        return False
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage stats
        """
        upload_files = list(self.upload_dir.glob("*.pdf"))
        index_files = list(self.faiss_index_dir.glob("*.index"))
        
        return {
            "total_documents": len(upload_files),
            "total_indices": len(index_files),
            "upload_dir_size_mb": sum(f.stat().st_size for f in upload_files) / (1024 * 1024),
            "index_dir_size_mb": sum(f.stat().st_size for f in index_files) / (1024 * 1024)
        }


# Singleton instance
storage_service = StorageService()
