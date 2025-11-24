"""
Ingest Sample Documents Script
Run this script to populate the database with sample documents
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services import document_processor, chroma_service
from config import settings
from loguru import logger

def main():
    logger.info("Starting document ingestion...")
    
    # Check if documents directory exists
    if not os.path.exists(settings.DOCUMENTS_PATH):
        logger.error(f"Documents directory not found: {settings.DOCUMENTS_PATH}")
        return
    
    # Process all documents in the directory
    chunks = document_processor.process_directory(settings.DOCUMENTS_PATH)
    
    if not chunks:
        logger.warning("No documents found or processed")
        return
    
    # Add to ChromaDB
    texts = [chunk['text'] for chunk in chunks]
    metadatas = [chunk['metadata'] for chunk in chunks]
    
    doc_ids = chroma_service.add_documents(texts, metadatas)
    
    logger.info(f"Successfully indexed {len(doc_ids)} chunks")
    logger.info(f"Total documents in database: {chroma_service.count_documents()}")
    
    print("\n✅ Document ingestion complete!")
    print(f"   - Processed {len(chunks)} chunks")
    print(f"   - Total documents: {chroma_service.count_documents()}")

if __name__ == "__main__":
    main()
