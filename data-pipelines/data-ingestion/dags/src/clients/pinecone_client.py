"""
Pinecone client for the LinkedLens Vector Integration.
"""

import time
from typing import Any, Dict, List, Optional, Union

from pinecone import Pinecone, Index, ServerlessSpec

from src.config.settings import settings
from src.utils.logger import logger


class PineconeClient:
    """Client for interacting with Pinecone Vector Database."""
    
    _instance = None
    _pinecone = None
    _indexes = {}
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(PineconeClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the Pinecone client."""
        if self._pinecone is None:
            self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """Initialize the Pinecone client."""
        try:
            logger.debug("Initializing Pinecone client")
            
            if not settings.pinecone.api_key:
                raise ValueError("PINECONE_API_KEY environment variable is not set")
            
            if not settings.pinecone.environment:
                raise ValueError("PINECONE_ENVIRONMENT environment variable is not set")
            
            # Initialize Pinecone client
            self._pinecone = Pinecone(
                api_key=settings.pinecone.api_key,
                environment=settings.pinecone.environment,
            )
            
            logger.info("Pinecone client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Pinecone client: {}", str(e))
            raise
    
    @property
    def client(self) -> Pinecone:
        """Get the Pinecone client."""
        return self._pinecone
    
    def get_index(self, index_name: str = None) -> Index:
        """
        Get a Pinecone index.
        
        Args:
            index_name: Name of the index to get. Defaults to settings.pinecone.index_name.
            
        Returns:
            Pinecone index.
        
        Raises:
            ValueError: If the index does not exist.
        """
        if index_name is None:
            index_name = settings.pinecone.index_name
        
        # Return cached index if available
        if index_name in self._indexes:
            return self._indexes[index_name]
        
        try:
            # List all indexes to check if our index exists
            index_list = self._pinecone.list_indexes()
            
            # Check if index exists
            if not any(index.name == index_name for index in index_list):
                logger.warning(f"Index '{index_name}' does not exist in Pinecone")
                raise ValueError(f"Pinecone index '{index_name}' does not exist. Please create it first.")
            
            # Get the index
            index = self._pinecone.Index(index_name)
            
            # Cache for future use
            self._indexes[index_name] = index
            
            logger.debug(f"Successfully connected to Pinecone index: {index_name}")
            return index
        except Exception as e:
            logger.error(f"Error getting Pinecone index '{index_name}': {str(e)}")
            raise
    
    def create_index(
        self, 
        index_name: str = None, 
        dimension: int = None, 
        metric: str = "cosine",
        serverless: bool = True,
        cloud: str = "aws",
        region: str = "us-west-2"
    ) -> bool:
        """
        Create a new Pinecone index if it doesn't exist.
        
        Args:
            index_name: Name of the index to create. Defaults to settings.pinecone.index_name.
            dimension: Vector dimension. Defaults to settings.pinecone.dimension.
            metric: Distance metric to use. Defaults to "cosine".
            serverless: Whether to use serverless. Defaults to True.
            cloud: Cloud provider to use. Defaults to "aws".
            region: Region to use. Defaults to "us-west-2".
            
        Returns:
            True if successful.
            
        Raises:
            Exception: If the index creation fails.
        """
        if index_name is None:
            index_name = settings.pinecone.index_name
        
        if dimension is None:
            dimension = settings.pinecone.dimension
        
        try:
            # List all indexes to check if our index already exists
            index_list = self._pinecone.list_indexes()
            
            # Check if index already exists
            if any(index.name == index_name for index in index_list):
                logger.info(f"Pinecone index '{index_name}' already exists")
                return True
            
            # Create index spec based on whether serverless is enabled
            spec = None
            if serverless:
                spec = ServerlessSpec(cloud=cloud, region=region)
            
            # Create the index
            self._pinecone.create_index(
                name=index_name,
                dimension=dimension,
                metric=metric,
                spec=spec
            )
            
            logger.info(f"Successfully created Pinecone index: {index_name} with dimension: {dimension}")
            
            # Wait for index to initialize
            logger.info("Waiting for index to initialize...")
            
            index_ready = False
            retries = 0
            max_retries = 15
            
            while not index_ready and retries < max_retries:
                try:
                    time.sleep(10)  # Wait 10 seconds between checks
                    
                    # Check if index exists and is ready
                    for index in self._pinecone.list_indexes():
                        if index.name == index_name and index.status.ready:
                            index_ready = True
                            logger.info(f"Pinecone index '{index_name}' is now ready to use")
                            break
                    
                    if not index_ready:
                        logger.debug(f"Index '{index_name}' is still initializing...")
                except Exception as e:
                    logger.debug(f"Error checking index status, retrying: {str(e)}")
                
                retries += 1
            
            if not index_ready:
                logger.warning(f"Index '{index_name}' may not be fully initialized yet")
            
            return True
        except Exception as e:
            logger.error(f"Error creating Pinecone index '{index_name}': {str(e)}")
            raise
    
    def store_embeddings(self, vector_list: List[Dict], namespace: str) -> Dict[str, Any]:
        """
        Store multiple embeddings in Pinecone.
        
        Args:
            vector_list: List of vectors - processed documents with embeddings.
            namespace : The namesapce where the vector should be inserted.
            
        Returns:
            Results of the upsert operations.
            
        Raises:
            Exception: If the operation fails.
        """
        try:
            index = self.get_index()
            # Store vectors by namespace
            results = {}
            logger.info(f"Number of vectors to be inserted : {len(vector_list)}")
            # Upsert batch
            result = index.upsert(vectors=vector_list, namespace=namespace)
                    
            logger.info(f"Vectors upserted to {namespace}: {len(vector_list)} vectors")
                    
            # Track results
            if namespace not in results:
                results[namespace] = {"upsertedCount": 0}
                    
            results[namespace]["upsertedCount"] += len(vector_list)
            
            return results
        except Exception as e:
            logger.error(
                f"Error batch storing embeddings: {str(e)}",
                extra={"count": len(vector_list)}
            )
            raise
    
    def query_similar(
        self,
        query_vector: List[float],
        namespace: Optional[str] = None,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query Pinecone for similar vectors.
        
        Args:
            query_vector: Query vector.
            namespace: Namespace to query.
            top_k: Number of results to return.
            filter: Metadata filter.
            
        Returns:
            Query results.
            
        Raises:
            Exception: If the query fails.
        """
        try:
            index = self.get_index()
            
            logger.debug(
                "Querying Pinecone for similar vectors",
                extra={
                    "namespace": namespace,
                    "topK": top_k,
                    "filter": filter,
                }
            )
            
            # Prepare query
            query_params = {
                "vector": query_vector,
                "top_k": top_k,
                "include_metadata": True,
            }
            
            if namespace:
                query_params["namespace"] = namespace
            
            if filter:
                query_params["filter"] = filter
            
            # Execute query
            results = index.query(**query_params)
            
            logger.info(f"Query returned {len(results.matches)} results")
            return results
        except Exception as e:
            logger.error(f"Error querying Pinecone: {str(e)}")
            raise
    
    def delete_vector(self, document_id: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a vector from Pinecone.
        
        Args:
            document_id: Document ID.
            namespace: Namespace of the vector.
            
        Returns:
            Result of the delete operation.
            
        Raises:
            Exception: If the delete fails.
        """
        try:
            index = self.get_index()
            
            logger.debug(f"Deleting vector: {document_id}", extra={"namespace": namespace})
            
            # Delete vector
            delete_params = {"ids": [document_id]}
            
            if namespace:
                delete_params["namespace"] = namespace
            
            result = index.delete(**delete_params)
            
            logger.info(f"Successfully deleted vector: {document_id}", extra={"namespace": namespace})
            return result
        except Exception as e:
            logger.error(f"Error deleting vector: {document_id}: {str(e)}")
            raise
    
    def find_vectors_by_firestore_ids(
        self, 
        firestore_ids: List[str], 
        namespace: Optional[str] = None
    ) -> List[Dict]:
        """
        Find vectors by Firestore IDs.
        
        Args:
            firestore_ids: Firestore document IDs.
            namespace: Namespace to search in.
            
        Returns:
            Matching vector records.
            
        Raises:
            Exception: If the operation fails.
        """
        try:
            index = self.get_index()
            
            # Fetch vectors
            fetch_params = {"ids": firestore_ids}
            
            if namespace:
                fetch_params["namespace"] = namespace
            
            response = index.fetch(**fetch_params)
            
            # Extract vectors
            if response and hasattr(response, "vectors") and response.vectors:
                return list(response.vectors.values())
            
            logger.debug(f"No vectors found for Firestore IDs: {', '.join(firestore_ids)}")
            return []
        except Exception as e:
            logger.error(
                f"Error finding vectors by Firestore IDs: {str(e)}",
                extra={"ids": firestore_ids}
            )
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics for the Pinecone index.
        
        Returns:
            Index statistics.
            
        Raises:
            Exception: If the operation fails.
        """
        try:
            index = self.get_index()
            
            logger.debug("Getting Pinecone index statistics")
            
            # Get stats
            stats = index.describe_index_stats()
            
            # Calculate total count and extract namespaces
            total_vector_count = 0
            namespaces = {}
            
            if hasattr(stats, "namespaces") and stats.namespaces:
                for name, data in stats.namespaces.items():
                    namespaces[name] = data.vector_count
                    total_vector_count += data.vector_count
            
            logger.info(
                "Retrieved Pinecone index statistics",
                extra={
                    "totalVectorCount": total_vector_count,
                    "namespaces": list(namespaces.keys()),
                }
            )
            
            return {
                "totalVectorCount": total_vector_count,
                "namespaces": namespaces,
            }
        except Exception as e:
            logger.error(f"Error getting Pinecone stats: {str(e)}")
            raise