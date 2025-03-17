"""
Embedding client for the LinkedLens Vector Integration.
"""

from typing import Dict, List, Optional, Tuple, Union

from sentence_transformers import SentenceTransformer

from src.config.settings import settings
from src.utils.logger import logger


class EmbeddingClient:
    """Client for generating embeddings using Sentence Transformers."""
    
    _instance = None
    _model = None
    # _embedding_cache = {}
    
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
            
            # # Clear the cache
            # self._embedding_cache = {}
            
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
    
    def generate_embeddings(
        self, 
        texts: List[Union[str, List, Dict, None]]
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: Array of texts to embed.
            
        Returns:
            Array of embedding vectors.
            
        Raises:
            Exception: If embedding generation fails.
        """
        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts")
            
            embeddings = [None] * len(texts)
            
            if None in embeddings:
                logger.warning(f"Some embeddings were not generated: {embeddings.count(None)} of {len(embeddings)}")
                # Fill in any missing embeddings with empty vectors (this shouldn't happen, but just in case)
                dimension = len(embeddings[0]) if embeddings[0] is not None else settings.pinecone.dimension
                empty_vector = [0.0] * dimension
                embeddings = [embedding if embedding is not None else empty_vector for embedding in embeddings]
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings in batch: {str(e)}")
            raise