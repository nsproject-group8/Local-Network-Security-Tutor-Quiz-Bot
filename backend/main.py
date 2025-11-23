"""
Main FastAPI application for Network Security Tutor & Quiz Bot.
Defines API endpoints for Q&A, quiz, document management, and health checks.
Initializes services, configures CORS, and logging.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import os
import shutil
from pathlib import Path
from loguru import logger

from config import settings
from models import (
    QuestionRequest, QuestionResponse,
    QuizGenerationRequest, QuizResponse,
    AnswerSubmission, QuizGrading,
    HealthResponse
)
from agents import qa_tutor_agent, quiz_agent
from services import (
    chroma_service, ollama_service, document_processor
)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Privacy-Preserving Network Security Tutor & Quiz Bot",
    version="1.0.0"
    # FastAPI app initialization with project metadata
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # CORS configuration for frontend communication
)

# Configure logging
logger.add(
    f"{settings.LOGS_PATH}/app.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
    # Logging configuration for application events
)

# Create necessary directories
os.makedirs(settings.DOCUMENTS_PATH, exist_ok=True)
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
os.makedirs(settings.LOGS_PATH, exist_ok=True)
os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
    # Create necessary directories for document management

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    """
    FastAPI startup event handler.
    Initializes services and checks Ollama availability.
    """
    logger.info("Starting Network Security Tutor Bot...")
    
    # Check Ollama availability
    if not ollama_service.check_availability():
        logger.warning("Ollama service not available. Please start Ollama and pull the model.")
    
    logger.info(f"ChromaDB initialized with {chroma_service.count_documents()} documents")
    logger.info("Application started successfully")

@app.get("/")
async def root():
    """Root endpoint."""
    """
    Root endpoint for API. Returns basic info and docs link.
    """
    return {
        "message": "Network Security Tutor & Quiz Bot API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    """
    Health check endpoint.
    Returns the status of the application and service availability.
    """
    ollama_available = ollama_service.check_availability()
    chroma_initialized = chroma_service.count_documents() >= 0
    documents_count = chroma_service.count_documents()
    
    status = "healthy" if (ollama_available and chroma_initialized) else "degraded"
    
    return HealthResponse(
        status=status,
        ollama_available=ollama_available,
        chroma_initialized=chroma_initialized,
        documents_indexed=documents_count
    )

# ============================================================================
# Q&A Tutor Endpoints
# ============================================================================

@app.post("/api/qa/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question to the Q&A Tutor Agent.
    
    - **question**: The question to ask
    """
    """
    Endpoint for asking questions to the Q&A Tutor Agent.
    Processes the request and returns the answer.
    """
    try:
        logger.info(f"Received question: {request.question}")
        response = qa_tutor_agent.answer_question(request)
        return response
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Quiz Agent Endpoints
# ============================================================================

@app.post("/api/quiz/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizGenerationRequest):
    """
    Generate a new quiz.
    
    - **mode**: random or topic_specific
    - **topic**: Topic for topic-specific quizzes
    - **num_questions**: Number of questions to generate
    - **question_types**: Types of questions to include
    """
    """
    Endpoint for generating a new quiz.
    Accepts quiz parameters and returns the generated quiz.
    """
    try:
        logger.info(f"Generating quiz: {request}")
        quiz = quiz_agent.generate_quiz(request)
        return quiz
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quiz/grade", response_model=QuizGrading)
async def grade_quiz(quiz_id: str, submissions: List[AnswerSubmission]):
    """
    Grade a quiz submission.
    
    - **quiz_id**: The ID of the quiz to grade
    - **submissions**: List of answer submissions
    """
    """
    Endpoint for grading a quiz submission.
    Accepts quiz ID and submissions, returns grading results.
    """
    try:
        logger.info(f"Grading quiz: {quiz_id}")
        grading = quiz_agent.grade_quiz(quiz_id, submissions)
        return grading
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error grading quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Document Management Endpoints
# ============================================================================

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload a document to be indexed.
    
    Supported formats: PDF, DOCX, PPTX, TXT, MD
    """
    """
    Endpoint for uploading documents to be indexed.
    Validates file type and processes the document.
    """
    try:
        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = {'.pdf', '.docx', '.pptx', '.txt', '.md'}
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save file
        file_path = os.path.join(settings.UPLOAD_PATH, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded file: {file.filename}")
        
        # Process and index document
        chunks = document_processor.process_file(file_path)
        
        if chunks:
            texts = [chunk['text'] for chunk in chunks]
            metadatas = [chunk['metadata'] for chunk in chunks]
            
            doc_ids = chroma_service.add_documents(texts, metadatas)
            
            logger.info(f"Indexed {len(doc_ids)} chunks from {file.filename}")
            
            return {
                "message": "Document uploaded and indexed successfully",
                "filename": file.filename,
                "chunks_indexed": len(doc_ids)
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract content from document"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/ingest-directory")
async def ingest_directory(directory_path: str = None):
    """
    Ingest all documents from a directory.
    
    - **directory_path**: Path to directory (defaults to DOCUMENTS_PATH)
    """
    """
    Endpoint for ingesting all documents from a specified directory.
    Processes and indexes documents found in the directory.
    """
    try:
        path = directory_path or settings.DOCUMENTS_PATH
        
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
        
        logger.info(f"Ingesting documents from: {path}")
        chunks = document_processor.process_directory(path)
        
        if chunks:
            texts = [chunk['text'] for chunk in chunks]
            metadatas = [chunk['metadata'] for chunk in chunks]
            
            doc_ids = chroma_service.add_documents(texts, metadatas)
            
            logger.info(f"Indexed {len(doc_ids)} chunks from directory")
            
            return {
                "message": "Directory ingested successfully",
                "directory": path,
                "chunks_indexed": len(doc_ids),
                "total_documents": chroma_service.count_documents()
            }
        else:
            return {
                "message": "No documents found or processed",
                "directory": path
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/count")
async def get_document_count():
    """Get the number of indexed documents."""
    """
    Endpoint for retrieving the count of indexed documents.
    Returns the total number of documents in the database.
    """
    try:
        count = chroma_service.count_documents()
        return {"total_documents": count}
    except Exception as e:
        logger.error(f"Error getting document count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/clear")
async def clear_documents():
    """Clear all indexed documents (use with caution)."""
    """
    Endpoint for clearing all indexed documents.
    Use with caution as this will delete all documents.
    """
    try:
        chroma_service.delete_all()
        logger.warning("All documents cleared from database")
        return {"message": "All documents cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
