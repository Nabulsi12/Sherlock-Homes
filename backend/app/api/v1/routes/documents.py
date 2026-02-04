"""
Document Upload Endpoints
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models.schemas import DocumentUploadResponse
from datetime import datetime
import uuid
import os

router = APIRouter()

# In-memory document storage (for hackathon - use cloud storage in production)
_documents = {}

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(..., description="Type: W-2, 1099, Tax Return, Pay Stub, Bank Statement, Other"),
    application_id: str = Form(None, description="Optional: Link to a loan application")
):
    """
    Upload a document for a loan application.

    Supports:
    - W-2 forms
    - 1099 forms
    - Tax returns
    - Pay stubs
    - Bank statements
    - Other documents

    File types: PDF, JPG, PNG, DOC, DOCX
    Max size: 10 MB
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024} MB"
        )

    # Generate document ID
    document_id = f"DOC-{str(uuid.uuid4())[:8]}"

    # Store document metadata (in production, upload to cloud storage)
    _documents[document_id] = {
        "document_id": document_id,
        "document_type": document_type,
        "file_name": file.filename,
        "file_size": file_size,
        "content_type": file.content_type,
        "application_id": application_id,
        "upload_date": datetime.utcnow(),
        "status": "uploaded",
        # In production: store file path or cloud URL
        # "file_path": f"/storage/documents/{document_id}{file_ext}"
    }

    # In production: Save file to disk or cloud storage
    # For hackathon: Just store metadata

    return DocumentUploadResponse(
        document_id=document_id,
        document_type=document_type,
        file_name=file.filename,
        file_size=file_size,
        upload_date=datetime.utcnow(),
        status="uploaded"
    )


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Get document metadata by ID.
    """
    if document_id not in _documents:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    doc = _documents[document_id]
    return {
        "document_id": doc["document_id"],
        "document_type": doc["document_type"],
        "file_name": doc["file_name"],
        "file_size": doc["file_size"],
        "upload_date": doc["upload_date"].isoformat(),
        "status": doc["status"],
        "application_id": doc.get("application_id")
    }


@router.get("/documents")
async def list_documents(application_id: str = None):
    """
    List all documents, optionally filtered by application ID.
    """
    docs = list(_documents.values())

    if application_id:
        docs = [d for d in docs if d.get("application_id") == application_id]

    return {
        "documents": [
            {
                "document_id": d["document_id"],
                "document_type": d["document_type"],
                "file_name": d["file_name"],
                "file_size": d["file_size"],
                "upload_date": d["upload_date"].isoformat(),
                "status": d["status"],
            }
            for d in docs
        ],
        "total": len(docs)
    }
