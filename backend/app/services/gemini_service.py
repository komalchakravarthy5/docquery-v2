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
        if self._model is not None:
            return

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing. Set it in backend/.env to enable query generation.")

        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(self.model_name)
        print(f"✅ Gemini model initialized: {self.model_name}")

    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, any]],
        max_context_length: int = 4000
    ) -> str:
        """Generate answer using RAG approach."""
        if not context_chunks:
            return "I cannot find this information in the document."

        self._initialize_model()

        context = self._build_context(context_chunks, max_context_length)
        if not context.strip():
            return "I cannot find this information in the document."

        prompt = self._create_rag_prompt(query, context)

        try:
            response = self._model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.gemini_temperature,
                )
            )
            answer = (response.text or "").strip()
            return answer or "I cannot find this information in the document."
        except Exception as e:
            print(f"❌ Error generating answer: {str(e)}")
            raise Exception(f"Failed to generate answer: {str(e)}")

    def _build_context(
        self,
        chunks: List[Dict[str, any]],
        max_length: int
    ) -> str:
        """Build context string from chunks with page references."""
        context_parts = []
        current_length = 0

        for chunk in chunks:
            text = chunk.get("text", "")
            source_file = chunk.get("source_file", "Document")
            source_page_number = chunk.get("source_page_number", chunk.get("page_number", "?"))
            chunk_text = f"[Source: {source_file} | Page {source_page_number}] {text}"
            chunk_length = len(chunk_text)

            if current_length + chunk_length > max_length:
                break

            context_parts.append(chunk_text)
            current_length += chunk_length

        return "\n\n".join(context_parts)

    def _create_rag_prompt(self, query: str, context: str) -> str:
        """Create RAG prompt template."""
        return f"""You are a helpful AI assistant answering questions about one or more uploaded documents. Your task is to provide accurate, clear answers based ONLY on the provided context.

Context from the document:
{context}

Question: {query}

Instructions:
1. Answer the question using ONLY the information from the context above.
2. If asked for a summary, provide a structured summary of key findings/themes from the retrieved context, using bullet points.
3. If findings are incomplete in context, mention what is present first, then state what is missing.
4. Mention source file name(s) and page number(s) when citing facts.
5. If the answer is not in the context at all, clearly state: I cannot find this information in the document.
6. Do not hallucinate, infer, or fabricate.

Answer:"""

    def is_initialized(self) -> bool:
        """Check if model is initialized"""
        return self._model is not None


# Singleton instance
gemini_service = GeminiService()
