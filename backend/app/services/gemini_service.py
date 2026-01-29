"""
Google Gemini Service
Handles LLM-based answer generation using Google Gemini API.
"""

import google.generativeai as genai
from typing import List, Dict
from app.config import get_settings

settings = get_settings()


class GeminiService:
    """Manages Google Gemini API for answer generation"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(GeminiService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Gemini service"""
        self.model_name = settings.gemini_model
        self.api_key = settings.gemini_api_key
    
    def _initialize_model(self):
        """Initialize Gemini model (lazy loading)"""
        if self._model is None:
            # Configure API key
            genai.configure(api_key=self.api_key)
            
            # Initialize model
            self._model = genai.GenerativeModel(self.model_name)
            print(f"✅ Gemini model initialized: {self.model_name}")
    
    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, any]],
        max_context_length: int = 4000
    ) -> str:
        """
        Generate answer using RAG approach.
        
        Args:
            query: User's question
            context_chunks: List of relevant chunks with 'text' and 'page_number'
            max_context_length: Maximum characters for context
            
        Returns:
            Generated answer string
        """
        self._initialize_model()
        
        # Build context from chunks
        context = self._build_context(context_chunks, max_context_length)
        
        # Create RAG prompt
        prompt = self._create_rag_prompt(query, context)
        
        try:
            # Generate response with temperature control
            response = self._model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.gemini_temperature,
                )
            )
            answer = response.text
            return answer
        except Exception as e:
            print(f"❌ Error generating answer: {str(e)}")
            raise Exception(f"Failed to generate answer: {str(e)}")
    
    def _build_context(
        self,
        chunks: List[Dict[str, any]],
        max_length: int
    ) -> str:
        """
        Build context string from chunks with page references.
        
        Args:
            chunks: List of chunk dictionaries
            max_length: Maximum total length
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0
        
        for i, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            page_num = chunk.get("page_number", "?")
            
            # Format: [Page X] text content
            chunk_text = f"[Page {page_num}] {text}"
            chunk_length = len(chunk_text)
            
            # Check if adding this chunk exceeds limit
            if current_length + chunk_length > max_length:
                break
            
            context_parts.append(chunk_text)
            current_length += chunk_length
        
        return "\n\n".join(context_parts)
    
    def _create_rag_prompt(self, query: str, context: str) -> str:
        """
        Create RAG prompt template.
        
        Args:
            query: User's question
            context: Context from retrieved chunks
            
        Returns:
            Formatted prompt
        """
        prompt = f"""You are a helpful AI assistant answering questions about a document. Your task is to provide accurate, clear answers based ONLY on the provided context.

Context from the document:
{context}

Question: {query}

Instructions:
1. Answer the question using ONLY the information from the context above
2. If the answer is not in the context, clearly state "I cannot find this information in the document"
3. Be concise but complete
4. If you reference specific information, mention the page number
5. Do not make up or infer information not present in the context

Answer:"""
        
        return prompt
    
    def is_initialized(self) -> bool:
        """Check if model is initialized"""
        return self._model is not None


# Singleton instance
gemini_service = GeminiService()
