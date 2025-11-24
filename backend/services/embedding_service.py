import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import uuid
from loguru import logger
from config import settings
import threading
from collections import OrderedDict
import time

class EmbeddingService:
    """
    Service for generating text embeddings using Sentence Transformers.
    Provides methods for embedding text and managing ChromaDB.
    """
    def __init__(self):
        """
        Initialize the embedding service with sentence transformers.
        """
        """Initialize the embedding service with sentence transformers."""
        # Defer heavy model loading until first use so the application can start
        # quickly. Loading at import time blocks the FastAPI startup when the
        # model files are downloaded from the hub (which can be large).
        self.model = None
        self.dimension = None
        self.model_name = settings.EMBEDDING_MODEL
        logger.info(f"EmbeddingService initialized (model deferred): {self.model_name}")
        # Simple in-memory LRU cache for single-text embeddings to speed up
        # repeated requests. Keys are strings, values are embedding lists.
        self._cache = OrderedDict()
        self._cache_max = 1024

        # Start background loader so the model is fetched without blocking
        # the startup path. This warms the model in the background.
        def _background_load():
            try:
                # Small delay to let the application finish startup logs.
                time.sleep(1)
                logger.info("Background embedding model loader starting")
                self.ensure_model_loaded()
                logger.info("Background embedding model loader finished")
            except Exception as e:
                logger.warning(f"Background model load failed: {e}")

        t = threading.Thread(target=_background_load, daemon=True)
        t.start()

    def ensure_model_loaded(self):
        """
        Load the SentenceTransformer model if it hasn't been loaded yet.
        """
        """Load the SentenceTransformer model if it hasn't been loaded yet."""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            try:
                self.dimension = self.model.get_sentence_embedding_dimension()
            except Exception:
                # If the model doesn't expose that method, leave dimension None
                self.dimension = None
            logger.info(f"Embedding model loaded. Dimension: {self.dimension}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text.
        """
        """Generate embeddings for a single text."""
        # Check cache first
        if text in self._cache:
            # move to end to mark as recently used
            self._cache.move_to_end(text)
            return self._cache[text]

        self.ensure_model_loaded()
        embedding = self.model.encode(text, convert_to_numpy=True)
        emb_list = embedding.tolist()

        # insert into cache and evict oldest if necessary
        self._cache[text] = emb_list
        if len(self._cache) > self._cache_max:
            self._cache.popitem(last=False)

        return emb_list
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        # For batch requests, reuse cached embeddings when available
        results: List[List[float]] = []
        to_compute: List[str] = []
        compute_indices: List[int] = []

        for i, t in enumerate(texts):
            if t in self._cache:
                self._cache.move_to_end(t)
                results.append(self._cache[t])
            else:
                # placeholder to keep ordering
                results.append(None)
                to_compute.append(t)
                compute_indices.append(i)

        if to_compute:
            self.ensure_model_loaded()
            embeddings = self.model.encode(to_compute, convert_to_numpy=True).tolist()
            for idx, emb in enumerate(embeddings):
                i = compute_indices[idx]
                results[i] = emb
                # cache single items
                key = to_compute[idx]
                self._cache[key] = emb
                if len(self._cache) > self._cache_max:
                    self._cache.popitem(last=False)

        return results

class ChromaDBService:
    def __init__(self, embedding_service: EmbeddingService):
        """Initialize ChromaDB client and collection."""
        self.embedding_service = embedding_service
        
        # Initialize ChromaDB client
        logger.info(f"Initializing ChromaDB at: {settings.CHROMA_DB_PATH}")
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=settings.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Collection '{settings.COLLECTION_NAME}' initialized with {self.collection.count()} documents")
        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
            raise
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add documents to the collection."""
        if not ids:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # Generate embeddings
        embeddings = self.embedding_service.embed_texts(texts)
        
        # Add to collection
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(texts)} documents to collection")
        return ids
    
    def query_similar(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query for similar documents."""
        query_embedding = self.embedding_service.embed_text(query_text)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        return results
    
    def get_all_documents(self) -> Dict[str, Any]:
        """Retrieve all documents from the collection."""
        return self.collection.get(
            include=["documents", "metadatas"]
        )
    
    def count_documents(self) -> int:
        """Get the total number of documents in the collection."""
        return self.collection.count()
    
    def delete_all(self):
        """Delete all documents from the collection."""
        self.client.delete_collection(name=settings.COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("All documents deleted from collection")

# Singleton instances
embedding_service = EmbeddingService()
chroma_service = ChromaDBService(embedding_service)
