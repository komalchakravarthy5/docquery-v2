"""
PDF Processing Service
Extracts text and metadata from PDF documents using PyMuPDF (fitz).
"""

import fitz  # PyMuPDF
from typing import List, Dict
from pathlib import Path


class PDFProcessor:
    """Handles PDF text extraction and metadata processing"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, any]]:
        """
        Extract text from PDF file page by page.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing page number and text content
            Format: [{"page_number": 1, "text": "..."}, ...]
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF is corrupted or cannot be read
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        pages_data = []
        
        try:
            # Open the PDF
            doc = fitz.open(pdf_path)
            
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")  # Extract plain text
                
                # Clean up the text
                text = text.strip()
                
                pages_data.append({
                    "page_number": page_num + 1,  # 1-indexed for user-facing
                    "text": text
                })
            
            doc.close()
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
        
        return pages_data
    
    @staticmethod
    def get_pdf_metadata(pdf_path: str) -> Dict[str, any]:
        """
        Extract metadata from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing PDF metadata
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = {
                "num_pages": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
            }
            doc.close()
            return metadata
        except Exception as e:
            raise Exception(f"Error reading PDF metadata: {str(e)}")
    
    @staticmethod
    def validate_pdf(pdf_path: str) -> bool:
        """
        Validate if file is a readable PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            doc = fitz.open(pdf_path)
            is_valid = len(doc) > 0
            doc.close()
            return is_valid
        except:
            return False


# Singleton instance
pdf_processor = PDFProcessor()
