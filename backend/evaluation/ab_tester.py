import asyncio
import os
import glob
import random
import uuid
import json
from pathlib import Path

# Add backend to sys path so we can import app modules directly
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.document_processor import document_processor
from app.services.text_chunker import text_chunker
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service
from app.services.database import database_service
from app.services.rag_service import rag_service
from app.services.gemini_service import gemini_service

PAPERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../doc_query_papers"))

async def generate_ground_truth(text: str, num_questions: int = 3) -> list:
    """Uses Gemini to hallucinate realistic questions based on the text."""
    prompt = f"""
    You are an AI generating evaluation datasets. 
    Read the following text chunk and generate exactly {num_questions} realistic, specific questions that a user might ask, where the answer is found directly in this text.
    Return ONLY a raw JSON list of strings, nothing else. No markdown blocks.

    TEXT:
    {text}
    """
    try:
        gemini_service._initialize_model()
        response = gemini_service._model.generate_content(prompt)
        text_resp = response.text.replace("```json", "").replace("```", "").strip()
        questions = json.loads(text_resp)
        return questions[:num_questions]
    except Exception as e:
        # Fallback if quota is hit
        return ["What is the main topic of this text?", "Summarize the key points."]

async def test_configuration(docs_data: list, config_name: str, dynamic: bool):
    """Run a test configuration and return average retrieval scores natively via FAISS (Bypassing LLM Answer Generation to save quota)."""
    print(f"\n[{config_name.upper()}] Building Vector Index (Dynamic={dynamic})...")
    
    total_relevance = 0.0
    total_citations = 0
    
    await database_service.initialize()
    
    for doc_name, pages, questions in docs_data:
        doc_id = str(uuid.uuid4())
        
        # 1. Chunking
        chunks = text_chunker.chunk_pages(pages, dynamic=dynamic)
        num_chunks = len(chunks)
        
        # 2. Embeddings
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.encode_batch(chunk_texts, batch_size=32, show_progress=False)
        
        # 3. Vector Store
        faiss_service.create_index(doc_id)
        faiss_service.add_embeddings(doc_id, embeddings)
        
        # 4. Evaluation Loop (Pure FAISS Retrieval without LLM answer to save API quota)
        for q in questions:
            q_emb = embedding_service.encode_text(q)
            distances, _ = faiss_service.search(doc_id, q_emb, top_k=5)
            
            if len(distances) > 0:
                # Calculate relevance natively like rag_service does
                relevances = [max(0.0, 1.0 - (float(d) / 10.0)) for d in distances]
                max_score = max(relevances)
                total_relevance += max_score
                total_citations += 1
                
    avg_score = (total_relevance / total_citations) if total_citations > 0 else 0
    print(f"[{config_name.upper()}] Metrics -> Avg Top-1 Relevance Score: {avg_score:.4f}")
    return avg_score

async def run_ab_test():
    print("Welcome to DocQuery A/B Tester")
    print("================================")
    
    pdfs = glob.glob(os.path.join(PAPERS_DIR, "*.pdf"))
    if not pdfs:
        print("No papers found in doc_query_papers!")
        return
        
    test_pdfs = random.sample(pdfs, min(2, len(pdfs))) # Limit to 2 to minimize quota/speed
    print(f"Selected {len(test_pdfs)} papers for evaluation.")
    
    docs_data = []
    total_q = 0
    
    for path in test_pdfs:
        print(f"Processing: {os.path.basename(path)}")
        pages = document_processor.extract_text(path)
        
        mid_idx = len(pages) // 2
        sample_text = pages[mid_idx]["text"][:1500]
        
        questions = await generate_ground_truth(sample_text, num_questions=2)
        total_q += len(questions)
        docs_data.append((os.path.basename(path), pages, questions))
        
    print(f"Generated {total_q} Ground Truth questions.")
    
    # Run Test A (Static - Old Way)
    score_a = await test_configuration(docs_data, "Test A (Static 500/50)", dynamic=False)
    
    # Run Test B (Dynamic)
    score_b = await test_configuration(docs_data, "Test B (Dynamic Scaling)", dynamic=True)
    
    print("\n================================")
    print("A/B TEST RESULTS")
    print("================================")
    print(f"Static Chunking Score:   {score_a:.4f}")
    print(f"Dynamic Chunking Score:  {score_b:.4f}")
    
    delta = score_b - score_a
    if delta > 0:
        print(f"\n✅ DYNAMIC SIZING WINS! (+{delta:.4f} relevance)")
    elif delta < 0:
        print(f"\n❌ STATIC SIZING WINS! ({delta:.4f} relevance)")
    else:
        print("\n➖ TIED! No difference in relevance.")
        
if __name__ == "__main__":
    asyncio.run(run_ab_test())
