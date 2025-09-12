import asyncio
import logging
import numpy as np
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
    
    async def generate_content(
        self, 
        prompt: str, 
        model: Optional[str] = None
    ) -> str:
        if self.provider == "gemini":
            model = model or "gemini-2.5-flash"
            response = await self.gemini_client.models.generate_content(
                model=model,
                contents=prompt
            )
            assert response.text is not None
            return response.text
            
        elif self.provider == "ollama":
            model = model or "reader-lm:1.5b"
            response = await ollama.AsyncClient().generate(
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
        text: str | list[str], 
        model: Optional[str] = None
    ) -> np.ndarray:
        if self.provider == "gemini":
            model = model or "gemini-embedding-001"
            result = await self.gemini_client.models.embed_content(
                model=model,
                contents=text,
                config=genai.types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=768),
            )
            assert result.embeddings is not None
            embedding_values = result.embeddings[0].values
            return np.array(embedding_values, dtype=np.float32)
            
        elif self.provider == "ollama":
            model = model or "nomic-embed-text:v1.5"  # Has output dimensionality of 768.
            response = await ollama.AsyncClient().embed(
                model=model,
                input=text,
            )
            embedding_values = response.embeddings
            return np.array(embedding_values, dtype=np.float32)
        
        raise RuntimeError(f"Unsupported provider: {self.provider}")


def create_ai_client(provider: AIProvider = "gemini") -> AIWrapper:
    return AIWrapper(provider)
