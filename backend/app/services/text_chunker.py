"""
Text Chunking Service
Splits extracted text into overlapping chunks for embedding generation.
"""

from typing import List, Dict
from app.config import get_settings

settings = get_settings()


class TextChunker:
    """Handles text chunking with sliding window approach"""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize text chunker with configurable parameters.
        
        Args:
            chunk_size: Size of each chunk in characters (default from config)
            chunk_overlap: Overlap between chunks in characters (default from config)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
    
    def chunk_pages(self, pages_data: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Chunk text from multiple pages while preserving page numbers.
        
        Args:
            pages_data: List of page dictionaries with 'page_number' and 'text'
            
        Returns:
            List of chunk dictionaries with metadata
            Format: [{
                "chunk_id": 0,
                "text": "...",
                "page_number": 1,
                "start_char": 0,
                "end_char": 500
            }, ...]
        """
        all_chunks = []
        chunk_id = 0
        
        for page_data in pages_data:
            page_number = page_data["page_number"]
            text = page_data["text"]
            
            # Skip empty pages
            if not text or len(text.strip()) == 0:
                continue
            
            # Create chunks for this page
            page_chunks = self._chunk_text(text, page_number, chunk_id)
            all_chunks.extend(page_chunks)
            chunk_id += len(page_chunks)
        
        return all_chunks
    
    def _chunk_text(self, text: str, page_number: int, start_chunk_id: int) -> List[Dict[str, any]]:
        """
        Split text into overlapping chunks using sliding window.
        
        Args:
            text: Text to chunk
            page_number: Page number this text came from
            start_chunk_id: Starting ID for chunks
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        text_length = len(text)
        
        # If text is shorter than chunk size, return as single chunk
        if text_length <= self.chunk_size:
            chunks.append({
                "chunk_id": start_chunk_id,
                "text": text.strip(),
                "page_number": page_number,
                "start_char": 0,
                "end_char": text_length
            })
            return chunks
        
        # Sliding window chunking
        start = 0
        chunk_id = start_chunk_id
        
        while start < text_length:
            # Calculate end position
            end = min(start + self.chunk_size, text_length)
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            # Only add non-empty chunks
            if chunk_text:
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "page_number": page_number,
                    "start_char": start,
                    "end_char": end
                })
                chunk_id += 1
            
            # Move window forward (with overlap)
            start += (self.chunk_size - self.chunk_overlap)
            
            # Prevent infinite loop
            if start >= text_length:
                break
        
        return chunks
    
    def get_chunk_stats(self, chunks: List[Dict[str, any]]) -> Dict[str, any]:
        """
        Get statistics about chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Dictionary with chunk statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0
            }
        
        chunk_sizes = [len(chunk["text"]) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes)
        }


# Singleton instance
text_chunker = TextChunker()
