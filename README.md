# DocQuery - Intelligent Document Chat Assistant

An AI-powered application that enables users to upload PDF documents and query them using natural language with citation-backed answers powered by RAG (Retrieval-Augmented Generation).

## 🎯 Features

- **PDF Upload**: Upload and process PDF documents
- **Natural Language Queries**: Ask questions in plain English
- **Citation-Backed Answers**: Get accurate answers with page references
- **Semantic Search**: FAISS-powered vector similarity search
- **Modern UI**: Dark mode interface with futuristic design
- **Google Gemini Integration**: Powered by Gemini 1.5 Flash

## 🏗️ Architecture

- **Frontend**: React + Vite
- **Backend**: FastAPI (Python)
- **Vector DB**: FAISS
- **Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2)
- **LLM**: Google Gemini API
- **Database**: SQLite

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API Key

## 🚀 Getting Started

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

5. Run the server:
```bash
python -m app.main
# or
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

## 📁 Project Structure

```
docquery/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── models/          # Pydantic schemas
│   │   ├── utils/           # Utilities
│   │   ├── config.py        # Configuration
│   │   └── main.py          # FastAPI app
│   ├── data/
│   │   ├── uploads/         # Uploaded PDFs
│   │   ├── faiss_index/     # Vector indices
│   │   └── metadata.db      # SQLite database
│   ├── evaluation/          # Evaluation scripts
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── src/
    │   ├── components/      # React components
    │   ├── services/        # API client
    │   └── App.jsx
    └── package.json
```

## 🔑 API Endpoints

- `GET /api/health` - Health check
- `POST /api/upload` - Upload PDF document
- `POST /api/query` - Query document
- `GET /api/documents` - List uploaded documents

## 🎨 Design System

- **Background**: `#0A0A0B` (Deep Black)
- **Surface**: `#161618` (Card Background)
- **Primary Accent**: `#C1FF72` (Neon Lime)
- **Secondary Accent**: `#9D5DFF` (Vibrant Purple)
- **Typography**: Plus Jakarta Sans / Inter

## 📊 Evaluation

Target: ≥80% Precision@5 retrieval relevance

## 📝 License

MIT License - Academic/Dissertation Project

## 👤 Author

Komal - VIT Dissertation Project 2026
