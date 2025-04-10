"""
Embedding client for the LinkedLens Vector Integration.
"""

from typing import Dict, List, Union
from sentence_transformers import SentenceTransformer, util
from config.settings import settings
from logger import logger


class EmbeddingClient:
    """Client for generating embeddings using Sentence Transformers."""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(EmbeddingClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the Embedding client."""
        if self._model is None:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Sentence Transformer model."""
        try:
            logger.debug(f"Initializing embedding model: {settings.embedding.model_name}")
            
            # Load the model
            self._model = SentenceTransformer(settings.embedding.model_name)
            
            logger.info(f"Embedding model initialized successfully: {settings.embedding.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            raise
    
    @property
    def model(self):
        """Get the Sentence Transformer model."""
        return self._model
      
    def generate_embedding(
        self, 
        text: Union[str, List, Dict, None],
    ) -> List[float]:
        """
        Generate an embedding from text.
        
        Args:
            text: Text to embed.
            
        Returns:
            The embedding vector.
            
        Raises:
            Exception: If embedding generation fails.
        """
        
        try:
            embedding = self._model.encode(text).tolist()
            logger.debug(
                "Successfully generated embedding",
                extra={"dimension": len(embedding), "model": settings.embedding.model_name}
            )
            
            return embedding
        except Exception as e:
            logger.error(
                f"Error generating embedding: {str(e)}",
                extra={
                    "textLength": len(text) if isinstance(text, str) else "N/A",
                    "model": settings.embedding.model_name
                }
            )
            raise

    def cos_sim(self, text1: str, text2: str) -> float:
        try:
            emb1 = self._model.encode(text1, convert_to_tensor=True)
            emb2 = self._model.encode(text2, convert_to_tensor=True)
            similarity = util.cos_sim(emb1, emb2).item()
            return round(similarity, 4)
        except Exception as e:
            logger.error(f"Error computing cosine similarity: {str(e)}")
            raise
    
