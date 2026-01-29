# 🚀 DocQuery - Quick Start Guide

## ⚡ Quick Setup (First Time)

### 1. Add Your Gemini API Key

Edit `backend/.env` and replace the placeholder:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

> Get your API key from: https://makersuite.google.com/app/apikey

### 2. Install Backend Dependencies

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies (if not done)

```bash
cd frontend
npm install
```

---

## 🎯 Running the Application

### Terminal 1: Start Backend

```bash
cd backend
.\venv\Scripts\Activate.ps1
python -m app.main
```

Backend runs on: **http://localhost:8000**

### Terminal 2: Start Frontend

```bash
cd frontend
npm run dev
```

Frontend runs on: **http://localhost:5173**

---

## 📝 Testing the RAG Pipeline

### Option 1: Via Frontend UI

1. Open http://localhost:5173
2. Upload a PDF document
3. Wait for processing (you'll see page/chunk count)
4. Ask questions about the document
5. Get answers with page citations!

### Option 2: Via API (curl)

**Upload a PDF:**
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@path/to/your/document.pdf"
```

Response:
```json
{
  "document_id": "abc-123-xyz",
  "filename": "document.pdf",
  "num_pages": 10,
  "num_chunks": 45,
  "message": "Document uploaded and processed successfully"
}
```

**Query the document:**
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "abc-123-xyz",
    "query": "What is the main topic of this document?"
  }'
```

Response:
```json
{
  "answer": "Based on the document...",
  "citations": [
    {
      "chunk_id": 5,
      "page_number": 2,
      "text_snippet": "The document discusses...",
      "relevance_score": 0.92
    }
  ],
  "document_id": "abc-123-xyz",
  "query": "What is the main topic..."
}
```

---

## 🔍 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Check server status |
| `/api/upload` | POST | Upload PDF document |
| `/api/query` | POST | Ask questions |
| `/api/documents` | GET | List all documents |

---

## 📊 What Happens During Upload?

1. ✅ PDF validation
2. ✅ Text extraction (PyMuPDF)
3. ✅ Text chunking (500 chars, 50 overlap)
4. ✅ Embedding generation (sentence-transformers)
5. ✅ FAISS index creation
6. ✅ Database storage (SQLite)

**Time**: ~2-3 seconds for small PDFs, ~10-15 seconds for medium PDFs

---

## 🤖 What Happens During Query?

1. ✅ Query embedding generation
2. ✅ FAISS similarity search (top-5 chunks)
3. ✅ Chunk retrieval from database
4. ✅ Context building with page numbers
5. ✅ Gemini answer generation
6. ✅ Citation formatting

**Time**: ~1-3 seconds per query

---

## 🛠️ Troubleshooting

### Backend won't start

**Issue**: `GEMINI_API_KEY not set`
- **Fix**: Add your API key to `backend/.env`

**Issue**: `ModuleNotFoundError`
- **Fix**: Activate venv and run `pip install -r requirements.txt`

### Upload fails

**Issue**: "Only PDF files are supported"
- **Fix**: Ensure file has `.pdf` extension

**Issue**: "PDF appears to be empty"
- **Fix**: Check if PDF has extractable text (not scanned images)

### Query returns "Document not found"

- **Fix**: Use the correct `document_id` from upload response

### Slow performance

- **First query is slow**: Models are lazy-loaded (normal)
- **All queries slow**: Check internet connection (Gemini API)

---

## 📁 Project Structure

```
docquery/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── services/        # 7 core services ✅
│   │   ├── models/          # Pydantic schemas
│   │   ├── config.py        # Settings
│   │   └── main.py          # FastAPI app
│   ├── data/
│   │   ├── uploads/         # Uploaded PDFs
│   │   ├── faiss_index/     # Vector indices
│   │   └── metadata.db      # SQLite database
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/      # React components
    │   └── services/        # API client
    └── package.json
```

---

## 🎓 Core Services Implemented

1. **pdf_processor.py** - PDF text extraction
2. **text_chunker.py** - Sliding window chunking
3. **storage.py** - File management
4. **embedding_service.py** - Vector embeddings
5. **faiss_service.py** - Similarity search
6. **database.py** - Metadata storage
7. **gemini_service.py** - LLM integration
8. **rag_service.py** - Pipeline orchestration

---

## 📚 Documentation

- **Implementation Plan**: `plan/implementation_plan_phases_3-5.md`
- **Detailed Walkthrough**: `plan/walkthrough_phases_3-5.md`
- **Task Checklist**: `plan/task_phases_3-5.md`
- **Previous Work**: `plan/walkthrough_phases_1-2.md`

---

## 🎉 You're Ready!

Your intelligent document chat assistant is fully implemented and ready to use!

**Next Steps**:
1. Add your Gemini API key
2. Start both servers
3. Upload a PDF
4. Ask questions and get cited answers!

Good luck with your dissertation! 🚀
