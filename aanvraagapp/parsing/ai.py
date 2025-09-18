import asyncio
import logging
import numpy as np
from numpy.linalg import norm
from typing import Literal, Optional
import ollama
from google import genai
from aanvraagapp.config import settings

logger = logging.getLogger(__name__)

AIProvider = Literal["gemini", "ollama"]


class AIWrapper:
    def __init__(self, provider: AIProvider = "gemini"):
        self.provider = provider
        if provider == "gemini":
            self.gemini_client = genai.Client(api_key=settings.gemini_api_key).aio
        elif provider == "ollama":
            self.ollama_base_url = "http://localhost:11434"
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
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
        model: Optional[str] = None
    ) -> str:
        if self.provider == "gemini":
            # model = model or "gemini-2.5-flash"
            model = model or "gemini-2.0-flash"
            response = await self.gemini_client.models.generate_content(
                model=model,
                contents=prompt
            )
            assert response.text is not None
            return response.text
            
        elif self.provider == "ollama":
            model = model or "reader-lm:1.5b"
            response = await ollama.AsyncClient(host=settings.ollama_uri).generate(
                model=model,
                prompt=prompt,
                options={
                    'num_ctx': 4096 * 8,  # Set context to 32K tokens,
                }
            )
            return response['response']
        
        raise RuntimeError(f"Unsupported provider: {self.provider}")
    
    async def embed_content(
        self, 
        texts: list[str], 
        model: Optional[str] = None
    ) -> np.ndarray:
        if self.provider == "gemini":
            model = model or "gemini-embedding-001"
            result = await self.gemini_client.models.embed_content(
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
            
        elif self.provider == "ollama":
            model = model or "embeddinggemma:300m"  # Has output dimensionality of 768.
            
            # EmbeddingGemma requires specific prompt formatting for documents
            if isinstance(texts, str):
                formatted_texts = f"title: none | text: {texts}"
            else:
                formatted_texts = [f"title: none | text: {t}" for t in texts]
            
            response = await ollama.AsyncClient(host=settings.ollama_uri).embed(
                model=model,
                input=formatted_texts,
            )
            embedding_values = response.embeddings
            # TODO: Shape of array that's returned?
            return np.array(embedding_values, dtype=np.float32)
        
        raise RuntimeError(f"Unsupported provider: {self.provider}")

    async def embed_query(
        self, 
        query: str, 
        model: Optional[str] = None
    ) -> np.ndarray:
        """Create embeddings for search queries (as opposed to documents in the corpus)."""
        if self.provider == "gemini":
            model = model or "gemini-embedding-001"
            result = await self.gemini_client.models.embed_content(
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
            
        elif self.provider == "ollama":
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
        
        raise RuntimeError(f"Unsupported provider: {self.provider}")


def create_ai_client(provider: AIProvider = "gemini") -> AIWrapper:
    return AIWrapper(provider)
