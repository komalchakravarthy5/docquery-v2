from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.models.schemas import DocumentUploadResponse
from app.services.document_processor import document_processor
from app.services.text_chunker import text_chunker
from app.services.storage import storage_service
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service
from app.services.database import database_service
import uuid

router = APIRouter()

SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.xlsx', '.csv', '.xls']

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(files: List[UploadFile] = File(...)):
    """
    Upload up to 3 documents for processing.
    Combines parsed pages/chunks from all uploaded files into one unified FAISS index workspace.
    """
    if len(files) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 files can be uploaded at once")
        
    for file in files:
        if not any(file.filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")
    
    try:
        # We generate ONE unified document_id to act as the "Workspace" 
        workspace_id = str(uuid.uuid4())
        
        all_pages_data = []
        combined_filename = " | ".join([f.filename for f in files])
        
        for file in files:
            file_content = await file.read()
            # We save it temporarily as workspace_id_filename
            file_path = storage_service.save_uploaded_file(
                file_content=file_content,
                document_id=workspace_id,
                filename=file.filename
            )
            
            # Extract text using our dynamic parser
            pages_data = document_processor.extract_text(file_path)
            
            # Prefix page data with filename to help LLM distinguish files in prompt
            for page in pages_data:
                page["text"] = f"[Source: {file.filename}] {page['text']}"
                
            all_pages_data.extend(pages_data)
            
        if len(all_pages_data) == 0:
            raise HTTPException(status_code=400, detail="No text content found in uploaded documents")
            
        # Step 4: Chunk ALL text seamlessly
        chunks = text_chunker.chunk_pages(all_pages_data, dynamic=True)
        num_chunks = len(chunks)
        
        if num_chunks == 0:
            raise HTTPException(status_code=400, detail="No readable content found.")
            
        # Step 5: Embed
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.encode_batch(
            texts=chunk_texts,
            batch_size=32,
            show_progress=False
        )
        
        # Step 6: FAISS Mapping
        faiss_service.create_index(workspace_id)
        faiss_service.add_embeddings(workspace_id, embeddings)
        
        index_path = storage_service.get_faiss_index_path(workspace_id)
        faiss_service.save_index(workspace_id, index_path)
        
        # Step 7: Database Metadata
        await database_service.initialize()
        await database_service.create_document(
            document_id=workspace_id,
            filename=combined_filename,
            num_pages=len(all_pages_data),
            num_chunks=num_chunks,
            file_path=f"workspace/{workspace_id}"
        )
        await database_service.insert_chunks(workspace_id, chunks)
        
        return DocumentUploadResponse(
            document_id=workspace_id,
            filename=combined_filename,
            num_pages=len(all_pages_data),
            num_chunks=num_chunks,
            message="Workspace generated successfully!"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        try:
            if 'workspace_id' in locals():
                storage_service.delete_faiss_index(workspace_id)
                # Cleanup loose files implicitly handled by storage service or OS later
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document workspace: {str(e)}"
        )
