"""
Embedding client for the LinkedLens Vector Integration.
"""

from typing import Dict, List, Optional, Tuple, Union

from sentence_transformers import SentenceTransformer

from config.settings import settings
from src.utils.logger import logger


class EmbeddingClient:
    """Client for generating embeddings using Sentence Transformers."""
    
    _instance = None
    _model = None
    _embedding_cache = {}
    
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
            
            # Clear the cache
            self._embedding_cache = {}
            
            logger.info(f"Embedding model initialized successfully: {settings.embedding.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            raise
    
    @property
    def model(self):
        """Get the Sentence Transformer model."""
        return self._model
    
    def _sanitize_text(self, text: Union[str, List, Dict, None]) -> str:
        """
        Sanitize text for embedding.
        
        Args:
            text: Text to sanitize.
            
        Returns:
            Sanitized text.
        """
        if text is None:
            return ""
        
        # Convert to string if not already
        if not isinstance(text, str):
            if isinstance(text, (list, tuple)):
                return " ".join(str(item) for item in text)
            elif isinstance(text, dict):
                return " ".join(f"{k} {v}" for k, v in text.items())
            return str(text)
        
        # Clean and normalize
        return " ".join(text.split())
    
    def _truncate_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Truncate text to maximum length.
        
        Args:
            text: Text to truncate.
            max_length: Maximum length.
            
        Returns:
            Truncated text.
        """
        if max_length is None:
            max_length = settings.embedding.max_input_length
        
        if len(text) <= max_length:
            return text
        
        logger.debug(f"Truncating text from {len(text)} to {max_length} characters")
        return text[:max_length]
    
    def generate_embedding(
        self, 
        text: Union[str, List, Dict, None], 
        use_cache: Optional[bool] = None
    ) -> List[float]:
        """
        Generate an embedding from text.
        
        Args:
            text: Text to embed.
            use_cache: Whether to use the cache.
            
        Returns:
            The embedding vector.
            
        Raises:
            Exception: If embedding generation fails.
        """
        if use_cache is None:
            use_cache = settings.embedding.use_cache
        
        try:
            # Sanitize and prepare text
            sanitized_text = self._sanitize_text(text)
            truncated_text = self._truncate_text(sanitized_text)
            
            # Check cache if enabled
            cache_key = f"{settings.embedding.model_name}:{truncated_text}"
            if use_cache and cache_key in self._embedding_cache:
                logger.debug("Using cached embedding", extra={"textLength": len(truncated_text)})
                return self._embedding_cache[cache_key]
            
            # Generate embedding
            logger.debug(
                f"Generating embedding with model: {settings.embedding.model_name}",
                extra={"textLength": len(truncated_text)}
            )
            
            embedding = self._model.encode(truncated_text).tolist()
            
            # Cache the result if caching is enabled
            if use_cache:
                self._embedding_cache[cache_key] = embedding
                
                # Limit cache size to prevent memory issues
                if len(self._embedding_cache) > 1000:
                    # Remove oldest item (first key)
                    oldest_key = next(iter(self._embedding_cache))
                    del self._embedding_cache[oldest_key]
            
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
        texts: List[Union[str, List, Dict, None]], 
        use_cache: Optional[bool] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: Array of texts to embed.
            use_cache: Whether to use the cache.
            
        Returns:
            Array of embedding vectors.
            
        Raises:
            Exception: If embedding generation fails.
        """
        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts")
            
            # Process all texts
            sanitized_texts = [self._sanitize_text(text) for text in texts]
            truncated_texts = [self._truncate_text(text) for text in sanitized_texts]
            
            # Check which texts are in cache
            if use_cache is None:
                use_cache = settings.embedding.use_cache
            
            # Initialize embeddings list with the correct size
            embeddings = [None] * len(truncated_texts)
            uncached_texts = []
            uncached_indices = []
            
            if use_cache:
                for i, text in enumerate(truncated_texts):
                    cache_key = f"{settings.embedding.model_name}:{text}"
                    if cache_key in self._embedding_cache:
                        embeddings[i] = self._embedding_cache[cache_key]
                    else:
                        uncached_texts.append(text)
                        uncached_indices.append(i)
            else:
                uncached_texts = truncated_texts
                uncached_indices = list(range(len(truncated_texts)))
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                logger.debug(f"Generating embeddings for {len(uncached_texts)} uncached texts")
                uncached_embeddings = self._model.encode(uncached_texts).tolist()
                
                # Store embeddings in correct positions and cache
                for i, (idx, embedding) in enumerate(zip(uncached_indices, uncached_embeddings)):
                    embeddings[idx] = embedding
                    
                    if use_cache:
                        cache_key = f"{settings.embedding.model_name}:{truncated_texts[idx]}"
                        self._embedding_cache[cache_key] = embedding
                
                # Limit cache size
                if use_cache and len(self._embedding_cache) > 1000:
                    # Remove oldest items
                    excess_count = len(self._embedding_cache) - 1000
                    for _ in range(excess_count):
                        oldest_key = next(iter(self._embedding_cache))
                        del self._embedding_cache[oldest_key]
            
            # Make sure all embeddings were generated
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