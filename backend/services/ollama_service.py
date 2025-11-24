import ollama
from typing import Dict, Any, Optional, List
from loguru import logger
from config import settings
from collections import OrderedDict
import threading
import time

class OllamaService:
    """
    Service for interacting with the Ollama LLM backend.
    Handles model availability checks and text generation.
    """
    def __init__(self):
        """
        Initialize Ollama client and model settings.
        """
        """Initialize Ollama client."""
        self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        self.model = settings.OLLAMA_MODEL
        logger.info(f"Ollama service initialized with model: {self.model}")
        # Simple LRU cache for generated outputs to speed up repeated prompts
        self._cache = OrderedDict()
        self._cache_max = 512
        # Optional background lock for thread-safety on cache
        self._lock = threading.Lock()
    
    def check_availability(self) -> bool:
        """
        Check if Ollama is available and the model is pulled.
        """
        """Check if Ollama is available and the model is pulled."""
        try:
            models_response = self.client.list()
            
            # Handle both dict response and direct models list
            if isinstance(models_response, dict):
                models_list = models_response.get('models', [])
            else:
                models_list = models_response
            
            # Extract model names safely
            model_names = []
            for model in models_list:
                if isinstance(model, dict):
                    # Try different possible keys
                    name = model.get('name') or model.get('model') or ''
                    model_names.append(name)
                else:
                    # If it's a string or has a name attribute
                    model_names.append(str(model))
            
            # Check if our model is available
            is_available = any(self.model in name for name in model_names if name)
            
            if is_available:
                logger.info(f"Ollama model '{self.model}' is available")
            else:
                logger.warning(f"Ollama model '{self.model}' not found in {model_names}. Please run: ollama pull {self.model}")
            
            return is_available
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {e}")
            return False
    
    def generate(
       
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> str:
        """
        Generate text using the Ollama LLM model.
        """
        """Generate text using Ollama."""
        try:
            # Check cache first
            cache_key = f"gen:{system_prompt}:{prompt}:{temperature}:{max_tokens}"
            with self._lock:
                if cache_key in self._cache:
                    self._cache.move_to_end(cache_key)
                    return self._cache[cache_key]

            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Cap num_predict to a tighter limit to reduce latency
            num_predict = min(int(max_tokens), 128)
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": num_predict,
                }
            )
            
            content = response['message']['content']
            with self._lock:
                self._cache[cache_key] = content
                if len(self._cache) > self._cache_max:
                    self._cache.popitem(last=False)

            return content
        
        except Exception as e:
            logger.error(f"Error generating text with Ollama: {e}")
            raise
    
    def generate_with_context(
        self,
        query: str,
        context: List[str],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """Generate text with retrieved context."""
        # Build context string
        context_str = "\n\n".join([f"[Context {i+1}]: {ctx}" for i, ctx in enumerate(context)])
        
        # Build full prompt
        full_prompt = f"""Based on the following context, answer the question accurately and concisely.

Context:
{context_str}

Question: {query}

Answer:"""
        
        # Use a tighter max token budget for context-based answers to speed up
        return self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=128
        )

# Singleton instance
ollama_service = OllamaService()
