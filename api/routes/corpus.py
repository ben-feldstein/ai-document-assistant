"""Corpus management routes for document ingestion and search."""

import time
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc
import io
import tempfile
import os

from api.models.db import get_db
from api.models.entities import User, Doc, Embedding, Membership
from api.models.schemas import DocumentCreate, DocumentResponse, SearchRequest, SearchResponse
from api.routes.auth import get_current_user
from api.services.search import search_service
from api.services.vectorizer import vectorizer_service

router = APIRouter()


@router.post("/doc", response_model=DocumentResponse)
async def create_document(
    document: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new document in the corpus.
    
    This endpoint allows users to add new policy documents
    to the system for AI-powered querying.
    """
    try:
        # CRITICAL: Always get org_id from user's membership for security
        # Users cannot specify org_id to prevent cross-organization access
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a member of any organization"
            )
        
        # Force the org_id to be the user's organization
        document.org_id = membership.org_id
        
        # Verify user has access to this organization
        membership = db.query(Membership).filter(
            Membership.org_id == document.org_id,
            Membership.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        # Create the document
        db_document = Doc(
            org_id=document.org_id,
            source=document.source,
            uri=document.uri,
            title=document.title,
            text=document.text,
            doc_metadata=json.dumps(document.metadata or {})
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Return the created document
        return DocumentResponse(
            id=db_document.id,
            source=db_document.source,
            uri=db_document.uri,
            title=db_document.title,
            text=db_document.text,
            metadata=json.loads(db_document.doc_metadata) if db_document.doc_metadata else {},
            created_at=db_document.created_at,
            updated_at=db_document.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating document: {str(e)}"
        )


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document file and extract its text content.
    
    Supports PDF, Word documents, and text files.
    """
    try:
        # Get user's organization
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a member of any organization"
            )
        
        # Validate file type
        allowed_types = [
            'application/pdf',
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/markdown'
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}. Supported types: PDF, Word, text, markdown"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Extract text based on file type
        if file.content_type == 'text/plain' or file.content_type == 'text/markdown':
            text_content = file_content.decode('utf-8')
        elif file.content_type == 'application/pdf':
            text_content = await _extract_pdf_text(file_content)
        elif file.content_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            text_content = await _extract_word_text(file_content)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Use provided title or extract from filename
        document_title = title or file.filename.rsplit('.', 1)[0]
        
        # Create document metadata
        metadata = {
            "file_type": file.content_type,
            "file_size": len(file_content),
            "original_filename": file.filename,
            "uploaded_at": time.time()
        }
        
        # Create the document
        db_document = Doc(
            org_id=membership.org_id,
            source=file.filename,
            title=document_title,
            text=text_content,
            doc_metadata=json.dumps(metadata)
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Return the created document
        return DocumentResponse(
            id=db_document.id,
            source=db_document.source,
            uri=db_document.uri,
            title=db_document.title,
            text=db_document.text,
            metadata=json.loads(db_document.doc_metadata) if db_document.doc_metadata else {},
            created_at=db_document.created_at,
            updated_at=db_document.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


async def _extract_pdf_text(pdf_content: bytes) -> str:
    """Extract text from PDF content."""
    try:
        # Try to import PyPDF2 or pypdf
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        except ImportError:
            try:
                import pypdf
                pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_content))
            except ImportError:
                raise ImportError("PyPDF2 or pypdf is required for PDF processing")
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )


async def _extract_word_text(doc_content: bytes) -> str:
    """Extract text from Word document content."""
    try:
        # Try to import python-docx
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx is required for Word document processing")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            temp_file.write(doc_content)
            temp_file_path = temp_file.name
        
        try:
            doc = Document(temp_file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text from Word document: {str(e)}"
        )


@router.get("/doc/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific document by ID."""
    try:
        # Get user's organizations
        memberships = db.query(Membership).filter(
            Membership.user_id == current_user.id
        ).all()
        
        org_ids = [m.org_id for m in memberships]
        
        # Find the document
        document = db.query(Doc).filter(
            Doc.id == doc_id,
            Doc.org_id.in_(org_ids)
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return DocumentResponse(
            id=document.id,
            source=document.source,
            uri=document.uri,
            title=document.title,
            text=document.text,
            metadata=document.doc_metadata,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document: {str(e)}"
        )


@router.get("/docs", response_model=List[DocumentResponse])
async def list_documents(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    org_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List documents with pagination."""
    try:
        # CRITICAL: Users can only see documents from their own organization
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id
        ).first()
        
        if not membership:
            return []
        
        # Users can only see documents from their own organization
        user_org_id = membership.org_id
        
        # Build query - only user's organization
        query = db.query(Doc).filter(Doc.org_id == user_org_id)
        
        # If org_id is specified, verify it's the user's organization
        if org_id and org_id != user_org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to other organizations"
            )
        
        # Apply pagination and ordering
        documents = query.order_by(desc(Doc.created_at)).offset(offset).limit(limit).all()
        
        # Format response
        return [
            DocumentResponse(
                id=doc.id,
                source=doc.source,
                uri=doc.uri,
                title=doc.title,
                text=doc.text,
                metadata=json.loads(doc.doc_metadata) if doc.doc_metadata else {},
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search documents using semantic similarity.
    
    This endpoint performs vector-based semantic search
    over the document corpus.
    """
    try:
        # CRITICAL: Always get org_id from user's membership for security
        # Users cannot specify org_id to prevent cross-organization access
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a member of any organization"
            )
        
        # Force the org_id to be the user's organization
        request.org_id = membership.org_id
        
        # Perform search
        start_time = time.time()
        try:
            search_results = await search_service.search(
                request.query,
                k=request.k,
                org_id=request.org_id,
                filters=request.filters
            )
            print(f"Search completed successfully, got {len(search_results)} results")
            print(f"First result: {search_results[0] if search_results else 'No results'}")
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            response = SearchResponse(
                results=search_results,
                total=len(search_results),
                query=request.query,
                latency_ms=latency_ms
            )
            print(f"SearchResponse created successfully: {response}")
            return response
            
        except Exception as e:
            print(f"Error in search route: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error searching documents: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching documents: {str(e)}"
        )


@router.delete("/doc/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document from the corpus."""
    try:
        # Get user's organizations
        memberships = db.query(Membership).filter(
            Membership.user_id == current_user.id
        ).all()
        
        org_ids = [m.org_id for m in memberships]
        
        # Find the document
        document = db.query(Doc).filter(
            Doc.id == doc_id,
            Doc.org_id.in_(org_ids)
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if user has admin/owner role
        membership = db.query(Membership).filter(
            Membership.org_id == document.org_id,
            Membership.user_id == current_user.id
        ).first()
        
        if not membership or membership.role not in ["admin", "owner"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete document"
            )
        
        # Delete associated embeddings first
        db.query(Embedding).filter(Embedding.doc_id == doc_id).delete()
        
        # Delete the document
        db.delete(document)
        db.commit()
        
        return {
            "ok": True,
            "data": {"message": "Document deleted successfully"}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )


@router.post("/reindex")
async def reindex_corpus(
    org_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger corpus reindexing for an organization.
    
    This endpoint starts the process of regenerating
    embeddings for all documents in the corpus.
    """
    try:
        # If org_id is not provided, get it from user's primary organization
        if not org_id:
            membership = db.query(Membership).filter(
                Membership.user_id == current_user.id
            ).first()
            
            if membership:
                org_id = membership.org_id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is not a member of any organization"
                )
        
        # Verify user has admin/owner role
        membership = db.query(Membership).filter(
            Membership.org_id == org_id,
            Membership.user_id == current_user.id
        ).first()
        
        if not membership or membership.role not in ["admin", "owner"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to reindex corpus"
            )
        
        # This would typically trigger a background job
        # For now, just return success
        return {
            "ok": True,
            "data": {
                "message": "Corpus reindexing started",
                "org_id": org_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting reindex: {str(e)}"
        )


@router.get("/stats")
async def get_corpus_stats(
    org_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get corpus statistics for an organization."""
    try:
        # If org_id is not provided, get it from user's primary organization
        if not org_id:
            membership = db.query(Membership).filter(
                Membership.user_id == current_user.id
            ).first()
            
            if membership:
                org_id = membership.org_id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is not a member of any organization"
                )
        
        # Verify user has access to this organization
        membership = db.query(Membership).filter(
            Membership.org_id == org_id,
            Membership.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        # Get statistics
        from sqlalchemy import func
        
        doc_count = db.query(func.count(Doc.id)).filter(Doc.org_id == org_id).scalar()
        embedding_count = db.query(func.count(Embedding.id)).join(Doc).filter(Doc.org_id == org_id).scalar()
        
        # Get total text length
        total_length = db.query(func.sum(func.length(Doc.text))).filter(Doc.org_id == org_id).scalar() or 0
        
        return {
            "ok": True,
            "data": {
                "org_id": org_id,
                "document_count": doc_count,
                "embedding_count": embedding_count,
                "total_text_length": total_length,
                "avg_document_length": round(total_length / doc_count, 2) if doc_count > 0 else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting corpus stats: {str(e)}"
        )


@router.get("/doc/{doc_id}/download")
async def download_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a document file."""
    try:
        # Get the document
        document = db.query(Doc).filter(Doc.id == doc_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if user has access to this document
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id,
            Membership.org_id == document.org_id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this document"
            )
        
        # Get file metadata
        metadata = json.loads(document.doc_metadata) if document.doc_metadata else {}
        file_type = metadata.get('file_type', 'text/plain')
        original_filename = metadata.get('original_filename', f'document_{doc_id}.txt')
        
        # For now, return the text content as a downloadable file
        # In a production system, you might want to store the original binary file
        from fastapi.responses import Response
        
        return Response(
            content=document.text,
            media_type=file_type,
            headers={
                "Content-Disposition": f"attachment; filename={original_filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading document: {str(e)}"
        )


@router.get("/doc/{doc_id}/preview")
async def preview_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview a document's content."""
    try:
        # Get the document
        document = db.query(Doc).filter(Doc.id == doc_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if user has access to this document
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id,
            Membership.org_id == document.org_id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this document"
            )
        
        # Get file metadata
        metadata = json.loads(document.doc_metadata) if document.doc_metadata else {}
        file_type = metadata.get('file_type', 'text/plain')
        original_filename = metadata.get('original_filename', f'document_{doc_id}.txt')
        
        # Return document preview data
        return {
            "ok": True,
            "data": {
                "id": document.id,
                "title": document.title,
                "source": document.source,
                "text": document.text,
                "file_type": file_type,
                "original_filename": original_filename,
                "file_size": metadata.get('file_size', 0),
                "uploaded_at": metadata.get('uploaded_at', 0),
                "created_at": document.created_at,
                "updated_at": document.updated_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error previewing document: {str(e)}"
        )
