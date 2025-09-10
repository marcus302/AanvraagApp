import logging
import numpy as np
from google import genai
from aanvraagapp.config import settings

logger = logging.getLogger(__name__)

def chunk_text(text: str, chunk_size: int = 1024, overlap: int = 128) -> list[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        
        # Avoid infinite loop if overlap is too large
        if start >= len(text):
            break
    
    return chunks

async def generate_embedding(text: str) -> np.ndarray:
    """Generate embedding using Google Gemini API."""
    client = genai.Client(api_key=settings.gemini_api_key).aio
    # TODO: async?
    result = await client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=genai.types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    # Convert to numpy array and ensure it's float32
    assert result.embeddings is not None
    embedding_values = result.embeddings[0].values
    return np.array(embedding_values, dtype=np.float32)
