from typing import Any, Dict, List, Optional
from pinecone import Pinecone, Index
from config.settings import settings
from logger import logger


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

    def query_similar(
        self,
        query_vector: List[float],
        namespace: Optional[str] = None,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        include_values: bool = False
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
                "include_metadata": include_metadata,
                "include_values" : include_values
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


    def fetch_by_vector_ids(
            self,
            vector_id_list: List[str],
            namespace:str = None,
        ) -> Dict[str, Any]:
            """
            Fetch records for vector ids.
            
            Args:
                vector_id_list: List of vector ids.
                namespace: Namespace to query.
                
            Returns:
                FetchResponse: Query results.
                
            Raises:
                Exception: If the query fails.
            """
            try:
                index = self.get_index()
                
                logger.debug(
                    "Querying Pinecone for similar vectors",
                    extra={
                        "namespace": namespace,
                        "vector_id_list": vector_id_list
                    }
                )
                
                # Fetch docs
                results = index.fetch(ids=vector_id_list, namespace=namespace)

                logger.info(f"Query returned {len(results.vectors)} results")
                return results
            except Exception as e:
                logger.error(f"Error querying Pinecone: {str(e)}")
                raise

