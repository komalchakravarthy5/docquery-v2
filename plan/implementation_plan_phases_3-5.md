# Backend RAG Implementation Plan - Phases 3-5

Implementation plan for Document Ingestion, Embeddings & FAISS, and RAG Pipeline for the DocQuery intelligent document chat assistant.

## User Review Required

> [!IMPORTANT]
> **Gemini API Key Required**: You need to add your actual Gemini API key to `.env` file (currently set to placeholder). The backend will not work without a valid API key.

> [!NOTE]
> **Dependencies**: All required packages are already in `requirements.txt`. You'll need to install them with `pip install -r requirements.txt` before running the backend.

---

## Proposed Changes

### Backend Services Layer

We'll create 7 new service files in `backend/app/services/` to handle the core RAG functionality:

#### [NEW] [pdf_processor.py](file:///d:/komal/VIT/projects/dissertation_2/docquery/backend/app/services/pdf_processor.py)

**Purpose**: Extract text and metadata from PDF documents

- Use PyMuPDF (fitz) to read PDF files
- Extract text content page by page
- Return structured data: `{page_number: int, text: str}[]`
- Handle errors (corrupted PDFs, password-protected files)

#### [NEW] [text_chunker.py](file:///d:/komal/VIT/projects/dissertation_2/docquery/backend/app/services/text_chunker.py)

**Purpose**: Split extracted text into overlapping chunks

- Implement sliding window algorithm (500 chars, 50 overlap from config)
- Preserve page number metadata for each chunk
- Return chunks with metadata: `{chunk_id, text, page_number, start_idx, end_idx}`
- Handle edge cases (short pages, special characters)

#### [NEW] [storage.py](file:///d:/komal/VIT/projects/dissertation_2/docquery/backend/app/services/storage.py)

**Purpose**: File system operations for uploaded PDFs

- Save uploaded files to `data/uploads/{document_id}.pdf`
- Create directory structure if not exists
- Provide file retrieval and deletion methods
- Validate file sizes and types

---

#### [NEW] [embedding_service.py](file:///d:/komal/VIT/projects/dissertation_2/docquery/backend/app/services/embedding_service.py)

**Purpose**: Generate vector embeddings using sentence-transformers

- Lazy-load `all-MiniLM-L6-v2` model (384-dimensional embeddings)
- Batch process chunks for efficiency
- Provide methods: `encode_text(text)` and `encode_batch(texts[])`
- Cache model in memory (singleton pattern)

#### [NEW] [faiss_service.py](file:///d:/komal/VIT/projects/dissertation_2/docquery/backend/app/services/faiss_service.py)

**Purpose**: Manage FAISS vector index for similarity search

- Initialize FAISS `IndexFlatL2` (384 dimensions)
- Add embeddings with document-specific indices
- Save/load index from `data/faiss_index/{document_id}.index`
- Search functionality: `search(query_embedding, top_k=5)`
- Return indices and distances

#### [NEW] [database.py](file:///d:/komal/VIT/projects/dissertation_2/docquery/backend/app/services/database.py)

**Purpose**: SQLite database for document and chunk metadata

**Schema**:
```sql
-- Documents table
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    num_pages INTEGER,
    num_chunks INTEGER,
    file_path TEXT
);

-- Chunks table
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

**Operations**:
- `create_document()`, `get_document()`, `list_documents()`
- `insert_chunks()`, `get_chunks_by_ids()`
- Async operations using `aiosqlite`

---

#### [NEW] [gemini_service.py](file:///d:/komal/VIT/projects/dissertation_2/docquery/backend/app/services/gemini_service.py)

**Purpose**: Google Gemini API integration for answer generation

- Initialize Gemini client with API key from config
- RAG prompt template:
  ```
  You are a helpful assistant answering questions about a document.
  
  Context from the document:
  {context}
  
  Question: {question}
  
  Provide a clear, accurate answer based ONLY on the context above.
  If the answer is not in the context, say so.
  ```
- Generate answers using `gemini-1.5-flash`
- Handle API errors and rate limits

#### [NEW] [rag_service.py](file:///d:/komal/VIT/projects/dissertation_2/docquery/backend/app/services/rag_service.py)

**Purpose**: Orchestrate the complete RAG pipeline

**Query Flow**:
1. Generate embedding for user query
2. Search FAISS index for top-k similar chunks
3. Retrieve chunk text from database
4. Format context for LLM
5. Generate answer using Gemini
6. Format citations with page numbers and relevance scores

**Methods**:
- `query(document_id: str, question: str) -> QueryResponse`

---

### API Routes Updates

#### [MODIFY] [upload.py](file:///d:/komal/VIT/projects/dissertation_2/docquery/backend/app/api/routes/upload.py)

**Changes**:
- Replace placeholder implementation with full pipeline
- Save uploaded PDF using `storage` service
- Extract text using `pdf_processor`
- Chunk text using `text_chunker`
- Generate embeddings using `embedding_service`
- Create FAISS index using `faiss_service`
- Store metadata in database
- Return actual `num_pages` and `num_chunks`

#### [MODIFY] [query.py](file:///d:/komal/VIT/projects/dissertation_2/docquery/backend/app/api/routes/query.py)

**Changes**:
- Replace placeholder with `rag_service.query()`
- Validate document exists in database
- Return real answers with citations
- Handle errors (document not found, API failures)

---

## Verification Plan

### Automated Tests

1. **Test PDF Processing**
   ```bash
   # Upload a sample PDF via API
   curl -X POST http://localhost:8000/api/upload \
     -F "file=@sample.pdf"
   ```

2. **Test Query Pipeline**
   ```bash
   # Query the uploaded document
   curl -X POST http://localhost:8000/api/query \
     -H "Content-Type: application/json" \
     -d '{"document_id": "xxx", "query": "What is this document about?"}'
   ```

3. **Verify Database**
   - Check SQLite database has documents and chunks
   - Verify chunk count matches expected

4. **Verify FAISS Index**
   - Check index file exists in `data/faiss_index/`
   - Verify index dimension is 384

### Manual Verification

1. **Start Backend Server**
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python -m app.main
   ```

2. **Test via Frontend**
   - Upload a PDF through the UI
   - Ask questions and verify answers
   - Check citations reference correct pages

3. **Evaluation Metrics**
   - Test retrieval accuracy (Precision@5)
   - Verify answer quality
   - Check citation relevance
