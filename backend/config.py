from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Network Security Tutor Bot"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    
    # ChromaDB
    CHROMA_DB_PATH: str = "./data/chroma_db"
    COLLECTION_NAME: str = "network_security_docs"
    
    # Embedding
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Paths
    DOCUMENTS_PATH: str = "./data/documents"
    UPLOAD_PATH: str = "./data/uploads"
    LOGS_PATH: str = "./logs"
    
    # Security
    ENCRYPTION_KEY: Optional[str] = None
    ENABLE_AUDIT_LOGGING: bool = True
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # Quiz
    QUIZ_POOL_SIZE: int = 100
    MIN_SIMILARITY_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
