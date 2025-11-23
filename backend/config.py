from pydantic_settings import BaseSettings
from pydantic import field_validator
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

    # Accept human-friendly sizes in the .env (e.g. '50MB', '10KB') and parse
    # them into integer bytes. This makes .env.example readable while still
    # validating to an int for runtime use.
    @field_validator("MAX_UPLOAD_SIZE", mode="before")
    @classmethod
    def _parse_max_upload_size(cls, v):
        if isinstance(v, str):
            s = v.strip().upper()
            try:
                if s.endswith("MB"):
                    return int(float(s[:-2]) * 1024 * 1024)
                if s.endswith("KB"):
                    return int(float(s[:-2]) * 1024)
                if s.endswith("GB"):
                    return int(float(s[:-2]) * 1024 * 1024 * 1024)
                # Fallback: attempt to parse as plain integer string
                return int(s)
            except Exception as e:
                raise ValueError(f"Invalid MAX_UPLOAD_SIZE value: {v}") from e
        return v

settings = Settings()
