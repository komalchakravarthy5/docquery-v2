# Create a New GitHub Repo (Keep Old Repo Untouched) + Verify DocQuery Works

This guide helps you publish this project as a **new GitHub repository** so your old version stays unchanged.

---

## 1) Create a NEW empty repository on GitHub

1. Open GitHub → **New repository**
2. Choose a new name (example: `docquery-v2`)
3. Keep it **empty** (do not add README/.gitignore/license)
4. Create repo

GitHub will show a URL like:

- HTTPS: `https://github.com/<your-username>/docquery-v2.git`
- SSH: `git@github.com:<your-username>/docquery-v2.git`

---

## 2) Point this local project to the NEW repo and push

From project root:

```bash
git remote -v
```

If `origin` exists and points to old repo, replace it with the new one:

```bash
git remote set-url origin https://github.com/<your-username>/docquery-v2.git
# OR
git remote set-url origin git@github.com:<your-username>/docquery-v2.git
```

If no `origin` exists, add it:

```bash
git remote add origin https://github.com/<your-username>/docquery-v2.git
```

Push current branch:

```bash
git push -u origin work
```

If your default branch should be `main`:

```bash
git branch -M main
git push -u origin main
```

> Your **old GitHub repo is not modified** unless you push to it.

---

## 3) Configure backend env

Create backend env file:

```bash
cd backend
cp .env.example .env 2>/dev/null || true
```

Set your Gemini key in `backend/.env`:

```env
GEMINI_API_KEY=your_real_key_here
```

---

## 4) Run locally (2 terminals)

### Terminal A (backend)

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
python -m app.main
```

Backend health URL:

- `http://localhost:8000/api/health`

### Terminal B (frontend)

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

- `http://localhost:5173`

---

## 5) How to verify it is working

### A) Basic health check

```bash
curl http://localhost:8000/api/health
```

Expect JSON with `status: "healthy"`.

### B) Upload test PDF

```bash
curl -X POST http://localhost:8000/api/upload -F "file=@/absolute/path/to/test.pdf"
```

Save the returned `document_id`.

### C) Query test

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"document_id":"<document_id>","query":"What is this document about?"}'
```

Expect:

- `answer` text
- non-empty `citations` (if relevant text exists)

### D) List uploaded docs

```bash
curl http://localhost:8000/api/documents
```

---

## 6) Common issues checklist

- `ModuleNotFoundError`: make sure backend venv is active and dependencies installed.
- Gemini errors: ensure `GEMINI_API_KEY` is set in `backend/.env`.
- CORS/UI connection: backend must run on `:8000`, frontend on `:5173`.
- Empty answers: verify PDF contains extractable text (not only scanned images).

---

## 7) Quick production sanity checks before sharing

From project root:

```bash
# backend syntax check
python -m py_compile backend/app/main.py

# frontend production build
cd frontend && npm run build
```

If both pass, repo is usually ready for sharing.
