from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.models.schemas import DocumentUploadResponse
from app.services.document_processor import document_processor
from app.services.text_chunker import text_chunker
from app.services.storage import storage_service
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service
from app.services.database import database_service
from app.services.indexing_job_service import indexing_job_service
from app.config import get_settings
import uuid
import asyncio

router = APIRouter()
settings = get_settings()

SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.xlsx', '.csv', '.xls']


async def _process_workspace(files: List[UploadFile], job_id: str = None) -> DocumentUploadResponse:
    if job_id:
        indexing_job_service.mark_running(job_id)

    workspace_id = str(uuid.uuid4())
    all_pages_data = []
    combined_filename = " | ".join([f.filename for f in files])

    async def _extract_file_pages(file: UploadFile):
        file_content = await file.read()
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        if len(file_content) > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds {settings.max_file_size_mb}MB limit",
            )

        file_path = storage_service.save_uploaded_file(
            file_content=file_content,
            document_id=workspace_id,
            filename=file.filename
        )

        pages_data = await asyncio.to_thread(document_processor.extract_text, file_path)

        for page in pages_data:
            page["source_file"] = file.filename
            page["source_page_number"] = page["page_number"]
            page["text"] = f"[Source: {file.filename} | Page {page['page_number']}]\n{page['text']}"

        return pages_data

    extraction_jobs = [_extract_file_pages(file) for file in files]
    extracted_batches = await asyncio.gather(*extraction_jobs)
    for batch in extracted_batches:
        all_pages_data.extend(batch)

    if len(all_pages_data) == 0:
        raise HTTPException(status_code=400, detail="No text content found in uploaded documents")

    chunks = text_chunker.chunk_pages(all_pages_data, dynamic=True)
    num_chunks = len(chunks)

    if num_chunks > settings.max_chunks_per_workspace:
        raise HTTPException(
            status_code=400,
            detail=f"Workspace too large ({num_chunks} chunks). Reduce file size or count.",
        )

    if num_chunks == 0:
        raise HTTPException(status_code=400, detail="No readable content found.")

    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.encode_batch(
        texts=chunk_texts,
        batch_size=32,
        show_progress=False
    )

    faiss_service.create_index(workspace_id)
    faiss_service.add_embeddings(workspace_id, embeddings)

    index_path = storage_service.get_faiss_index_path(workspace_id)
    faiss_service.save_index(workspace_id, index_path)

    await database_service.initialize()
    await database_service.create_document(
        document_id=workspace_id,
        filename=combined_filename,
        num_pages=len(all_pages_data),
        num_chunks=num_chunks,
        file_path=f"workspace/{workspace_id}"
    )
    await database_service.insert_chunks(workspace_id, chunks)

    if job_id:
        indexing_job_service.mark_completed(job_id, workspace_id)

    return DocumentUploadResponse(
        document_id=workspace_id,
        filename=combined_filename,
        num_pages=len(all_pages_data),
        num_chunks=num_chunks,
        message="Workspace generated successfully!"
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(files: List[UploadFile] = File(...)):
    """Upload and index multiple documents in a unified workspace."""
    if len(files) > settings.max_upload_files:
        raise HTTPException(status_code=400, detail=f"Maximum {settings.max_upload_files} files can be uploaded at once")

    for file in files:
        if not any(file.filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")

    try:
        return await _process_workspace(files)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document workspace: {str(e)}")


@router.post("/upload/async")
async def upload_document_async(files: List[UploadFile] = File(...)):
    """Submit indexing job and poll status via /upload/jobs/{job_id}."""
    if len(files) > settings.max_upload_files:
        raise HTTPException(status_code=400, detail=f"Maximum {settings.max_upload_files} files can be uploaded at once")

    for file in files:
        if not any(file.filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")

    job_id = str(uuid.uuid4())
    indexing_job_service.create_job(job_id, " | ".join([f.filename for f in files]))

    async def _run_job():
        try:
            await _process_workspace(files, job_id=job_id)
        except Exception as exc:
            indexing_job_service.mark_failed(job_id, str(exc))

    asyncio.create_task(_run_job())
    return {"job_id": job_id, "status": "queued"}


@router.get("/upload/jobs/{job_id}")
async def get_upload_job(job_id: str):
    job = indexing_job_service.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
