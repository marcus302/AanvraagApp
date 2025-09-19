import asyncio
import logging
import numpy as np
from numpy.linalg import norm
from typing import Literal, Optional, Type
from abc import ABC, abstractmethod
import ollama
from google import genai
from aanvraagapp.config import settings
from pydantic import BaseModel
from aanvraagapp.types import AIProvider

logger = logging.getLogger(__name__)


class AIClient(ABC):
    """Abstract base class for AI clients."""
    
    @abstractmethod
    async def generate_content(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        output_schema: Type[BaseModel] | None = None
    ) -> str:
        """Generate text content from a prompt."""
        pass
    
    @abstractmethod
    async def embed_content(
        self, 
        texts: list[str], 
        model: Optional[str] = None
    ) -> np.ndarray:
        """Create embeddings for documents/content."""
        pass
    
    @abstractmethod
    async def embed_query(
        self, 
        query: str, 
        model: Optional[str] = None
    ) -> np.ndarray:
        """Create embeddings for search queries."""
        pass


class GeminiAIClient(AIClient):
    """Gemini AI client implementation."""
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key).aio
    
    def _normalize_embedding_if_needed(self, embedding: np.ndarray) -> np.ndarray:
        """Normalize embedding using L2 normalization if output size is not 3072."""
        if embedding.shape[-1] != 3072:
            # Apply L2 normalization
            normed_embedding = embedding / norm(embedding)
            return normed_embedding
        return embedding
    
    async def generate_content(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        output_schema: Type[BaseModel] | None = None
    ) -> str:
        model = model or "gemini-2.0-flash"
        if output_schema:
            config = genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=output_schema
            )
        else:
            config = None
        response = await self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        assert response.text is not None
        return response.text
    
    async def embed_content(
        self, 
        texts: list[str], 
        model: Optional[str] = None
    ) -> np.ndarray:
        model = model or "gemini-embedding-001"
        result = await self.client.models.embed_content(
            model=model,
            contents=texts,
            config=genai.types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=768),
        )
        assert result.embeddings is not None
        # TODO: Shape of array that's returned?
        # (len(texts), output_dimensionality)
        embeddings = np.array([i.values for i in result.embeddings], dtype=np.float32)
        # Apply normalization if needed
        return self._normalize_embedding_if_needed(embeddings)
    
    async def embed_query(
        self, 
        query: str, 
        model: Optional[str] = None
    ) -> np.ndarray:
        """Create embeddings for search queries (as opposed to documents in the corpus)."""
        model = model or "gemini-embedding-001"
        result = await self.client.models.embed_content(
            model=model,
            contents=query,
            config=genai.types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=768),
        )
        assert result.embeddings is not None
        embedding_values = result.embeddings[0].values
        # TODO: Shape of array that's returned?
        embedding = np.array(embedding_values, dtype=np.float32)
        # Apply normalization if needed
        return self._normalize_embedding_if_needed(embedding)


class OllamaAIClient(AIClient):
    """Ollama AI client implementation."""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
    
    async def generate_content(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        output_schema: Type[BaseModel] | None = None
    ) -> str:
        model = model or "reader-lm:1.5b"
        if output_schema is not None:
            raise RuntimeError("No output schema support for Ollama")
        response = await ollama.AsyncClient(host=settings.ollama_uri).generate(
            model=model,
            prompt=prompt,
            options={
                'num_ctx': 4096 * 8,  # Set context to 32K tokens,
            }
        )
        return response['response']
    
    async def embed_content(
        self, 
        texts: list[str], 
        model: Optional[str] = None
    ) -> np.ndarray:
        model = model or "embeddinggemma:300m"  # Has output dimensionality of 768.
        
        # EmbeddingGemma requires specific prompt formatting for documents
        formatted_texts = [f"title: none | text: {t}" for t in texts]
        
        response = await ollama.AsyncClient(host=settings.ollama_uri).embed(
            model=model,
            input=formatted_texts,
        )
        embedding_values = response.embeddings
        # TODO: Shape of array that's returned?
        return np.array(embedding_values, dtype=np.float32)
    
    async def embed_query(
        self, 
        query: str, 
        model: Optional[str] = None
    ) -> np.ndarray:
        """Create embeddings for search queries (as opposed to documents in the corpus)."""
        model = model or "embeddinggemma:300m"  # Has output dimensionality of 768.
        
        # EmbeddingGemma requires specific prompt formatting for queries
        formatted_query = f"task: search result | query: {query}"
        
        response = await ollama.AsyncClient(host=settings.ollama_uri).embed(
            model=model,
            input=formatted_query,
        )
        embedding_values = response.embeddings
        # TODO: Shape of array that's returned?
        return np.array(embedding_values, dtype=np.float32).squeeze(0)


def get_client(provider: AIProvider = "gemini") -> AIClient:
    """Create an AI client instance based on the provider."""
    if provider == "gemini":
        return GeminiAIClient()
    elif provider == "ollama":
        return OllamaAIClient()
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
