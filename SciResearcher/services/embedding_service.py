"""
Embedding 服务 (Qwen3 Embedding)
"""
import numpy as np
from .model_factory import ModelFactory

class EmbeddingService:
    """Qwen3 Embedding 服务"""

    def __init__(self, model_name: str = "text-embedding-v3", dimension: int = 1536):
        self.model_name = model_name
        self.dimension = dimension
        self.client = ModelFactory.get_client()

    def embed(self, text: str) -> np.ndarray:
        """文本向量化"""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text
        )
        return np.array(response.data[0].embedding, dtype='float32')
