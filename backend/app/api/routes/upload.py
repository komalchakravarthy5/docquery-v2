from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import DocumentUploadResponse
from app.services.pdf_processor import pdf_processor
from app.services.text_chunker import text_chunker
from app.services.storage import storage_service
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service
from app.services.database import database_service
import uuid
import numpy as np

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF document for processing
    
    This endpoint will:
    1. Validate the file is a PDF
    2. Save the file to storage
    3. Extract text and create chunks
    4. Generate embeddings
    5. Store in FAISS index
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Step 1: Read file content
        file_content = await file.read()
        
        # Step 2: Save file to storage
        file_path = storage_service.save_uploaded_file(
            file_content=file_content,
            document_id=document_id,
            filename=file.filename
        )
        
        # Step 3: Extract text from PDF
        pages_data = pdf_processor.extract_text_from_pdf(file_path)
        num_pages = len(pages_data)
        
        if num_pages == 0:
            raise HTTPException(status_code=400, detail="PDF appears to be empty or unreadable")
        
        # Step 4: Chunk the text
        chunks = text_chunker.chunk_pages(pages_data)
        num_chunks = len(chunks)
        
        if num_chunks == 0:
            raise HTTPException(status_code=400, detail="No text content found in PDF")
        
        # Step 5: Generate embeddings for all chunks
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.encode_batch(
            texts=chunk_texts,
            batch_size=32,
            show_progress=False
        )
        
        # Step 6: Create and populate FAISS index
        faiss_service.create_index(document_id)
        faiss_service.add_embeddings(document_id, embeddings)
        
        # Save FAISS index to disk
        index_path = storage_service.get_faiss_index_path(document_id)
        faiss_service.save_index(document_id, index_path)
        
        # Step 7: Initialize database if needed
        await database_service.initialize()
        
        # Step 8: Store document metadata in database
        await database_service.create_document(
            document_id=document_id,
            filename=file.filename,
            num_pages=num_pages,
            num_chunks=num_chunks,
            file_path=file_path
        )
        
        # Step 9: Store chunks in database
        await database_service.insert_chunks(document_id, chunks)
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            num_pages=num_pages,
            num_chunks=num_chunks,
            message="Document uploaded and processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        try:
            if 'document_id' in locals():
                storage_service.delete_document(document_id)
                storage_service.delete_faiss_index(document_id)
        except:
            pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )
