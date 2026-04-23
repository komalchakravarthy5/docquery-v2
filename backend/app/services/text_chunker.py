"""
Text Chunking Service
Splits extracted text into overlapping chunks for embedding generation.
"""

from typing import List, Dict
from app.config import get_settings
import re

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
    
    def chunk_pages(self, pages_data: List[Dict[str, any]], dynamic: bool = True) -> List[Dict[str, any]]:
        """
        Chunk text from multiple pages while preserving page numbers.
        
        Args:
            pages_data: List of page dictionaries with 'page_number' and 'text'
            dynamic: If True, dynamically scale chunk parameters based on document length.
            
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
        
        # Calculate dynamic chunk size
        current_size = self.chunk_size
        current_overlap = self.chunk_overlap
        
        if dynamic:
            total_chars = sum(len(page.get("text", "")) for page in pages_data)
            if total_chars < 5000:
                current_size = 1000
                current_overlap = 200
            elif total_chars < 50000:
                current_size = 750
                current_overlap = 100
            else:
                current_size = 500
                current_overlap = 50
        
        for page_data in pages_data:
            page_number = page_data["page_number"]
            text = page_data["text"]
            source_file = page_data.get("source_file")
            source_page_number = page_data.get("source_page_number", page_number)
            
            # Skip empty pages
            if not text or len(text.strip()) == 0:
                continue
            
            # Create chunks for this page
            page_chunks = self._chunk_text(
                text,
                page_number,
                chunk_id,
                current_size,
                current_overlap,
                source_file=source_file,
                source_page_number=source_page_number,
            )
            all_chunks.extend(page_chunks)
            chunk_id += len(page_chunks)
        
        return all_chunks
    
    def _chunk_text(
        self,
        text: str,
        page_number: int,
        start_chunk_id: int,
        size: int,
        overlap: int,
        source_file: str = None,
        source_page_number: int = None,
    ) -> List[Dict[str, any]]:
        """
        Split text into overlapping chunks using sliding window.
        
        Args:
            text: Text to chunk
            page_number: Page number this text came from
            start_chunk_id: Starting ID for chunks
            size: Chunk size in characters
            overlap: Chunk overlap in characters
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        # Structure-aware split (headings/paragraph blocks) before sliding windows.
        section_candidates = self._split_sections(text)
        text = "\n\n".join(section_candidates)
        text_length = len(text)
        
        # If text is shorter than chunk size, return as single chunk
        if text_length <= size:
            chunks.append({
                "chunk_id": start_chunk_id,
                "text": text.strip(),
                "page_number": page_number,
                "source_file": source_file,
                "source_page_number": source_page_number if source_page_number is not None else page_number,
                "start_char": 0,
                "end_char": text_length
            })
            return chunks
        
        # Sliding window chunking
        start = 0
        chunk_id = start_chunk_id
        
        while start < text_length:
            # Calculate end position
            end = min(start + size, text_length)
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            # Only add non-empty chunks
            if chunk_text:
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "page_number": page_number,
                    "source_file": source_file,
                    "source_page_number": source_page_number if source_page_number is not None else page_number,
                    "start_char": start,
                    "end_char": end
                })
                chunk_id += 1
            
            # Move window forward (with overlap)
            start += (size - overlap)
            
            # Prevent infinite loop
            if start >= text_length:
                break
        
        return chunks

    def _split_sections(self, text: str) -> List[str]:
        """Split text into rough sections by heading-like patterns."""
        if not text:
            return []

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            return [text]

        sections = []
        current = []
        heading_pattern = re.compile(r"^(\d+(\.\d+)*)\s+.+|^[A-Z][A-Za-z\s]{2,40}$")

        for line in lines:
            is_heading = bool(heading_pattern.match(line)) and len(line.split()) <= 12
            if is_heading and current:
                sections.append("\n".join(current))
                current = [line]
            else:
                current.append(line)

        if current:
            sections.append("\n".join(current))

        return sections if sections else [text]
    
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
