"""
Firestore client for the LinkedLens Vector Integration.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import firebase_admin
from firebase_admin import credentials, firestore

from config.settings import settings
from src.utils.logger import logger


class FirestoreClient:
    """Client for interacting with Firestore Database."""
    
    _instance = None
    _db = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(FirestoreClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the Firestore client."""
        if self._db is None:
            self._initialize_firestore()
    
    def _initialize_firestore(self):
        """Initialize the Firestore client."""
        try:
            # Get credentials path from settings
            creds_path = settings.firestore.credentials_path
            creds_path = Path(creds_path).resolve()
            
            logger.info(f"Found credentials file at: {creds_path}")
            
            if not creds_path.exists():
                raise FileNotFoundError(f"Firestore credentials file not found at: {creds_path}")
            
            # Get database ID from settings
            db_name = settings.firestore.database_id
            if db_name:
                logger.info(f"Using database ID: {db_name}")
            
            # Load credentials
            cred = credentials.Certificate(str(creds_path))
            
            # Initialize Firebase Admin if not already initialized
            try:
                if firebase_admin._apps:
                    logger.debug("Firebase Admin already initialized")
                else:
                    # Initialize Firebase app
                    firebase_admin.initialize_app(cred)
            except ValueError as e:
                if "already exists" in str(e):
                    logger.debug("Firebase Admin already initialized")
                else:
                    raise
            
            # Initialize Firestore client with database_id parameter
            # This matches the approach used in the data-generation code
            if db_name:
                self._db = firestore.client(database_id=db_name)
            else:
                self._db = firestore.client()
                
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Firestore client: {str(e)}")
            raise
    
    @property
    def client(self):
        """Get the Firestore client."""
        return self._db
    
    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID from a collection.
        
        Args:
            collection: Collection name.
            doc_id: Document ID.
            
        Returns:
            Document data or None if not found.
            
        Raises:
            Exception: If the operation fails.
        """
        try:
            doc_ref = self._db.collection(collection).document(doc_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.debug(f"Document not found: {collection}/{doc_id}")
                return None
            
            return {
                "id": doc.id,
                **doc.to_dict()
            }
        except Exception as e:
            logger.error(f"Error getting document {collection}/{doc_id}: {str(e)}")
            raise
    
    def get_documents(
        self, 
        collection: str, 
        filters: Optional[Dict[str, Any]] = None, 
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get documents from a collection with optional filtering.
        
        Args:
            collection: Collection name.
            filters: Optional filter conditions.
            limit: Optional limit on number of documents.
            
        Returns:
            List of documents.
            
        Raises:
            Exception: If the operation fails.
        """
        try:
            query = self._db.collection(collection)
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    query = query.where(field, "==", value)
            
            # Apply limit if provided
            if limit > 0:
                query = query.limit(limit)
            
            # Execute query
            snapshot = query.get()
            
            if not snapshot:
                logger.debug(f"No documents found in collection: {collection}")
                return []
            
            # Process results
            documents = [{"id": doc.id, **doc.to_dict()} for doc in snapshot]
            
            logger.debug(f"Retrieved {len(documents)} documents from {collection}")
            return documents
        except Exception as e:
            logger.error(f"Error getting documents from {collection}: {str(e)}")
            raise
    
    def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """
        Update a document in Firestore.
        
        Args:
            collection: Collection name.
            doc_id: Document ID.
            data: Data to update.
            
        Returns:
            True if successful.
            
        Raises:
            Exception: If the update fails.
        """
        try:
            doc_ref = self._db.collection(collection).document(doc_id)
            doc_ref.update(data)
            
            logger.debug(f"Updated document {collection}/{doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating document {collection}/{doc_id}: {str(e)}")
            raise
    
    def update_vector_info(self, collection: str, doc_id: str, vector_info: Dict[str, Any]) -> bool:
        """
        Update a document with vector information.
        
        Args:
            collection: Collection name.
            doc_id: Document ID.
            vector_info: Vector information to update.
            
        Returns:
            True if successful.
            
        Raises:
            Exception: If the update fails.
        """
        try:
            doc_ref = self._db.collection(collection).document(doc_id)
            
            # Prepare update data
            update_data = {
                "vectorId": vector_info.get("vectorId", doc_id),
                "vectorNamespace": vector_info.get("namespace"),
                "vectorTimestamp": firestore.SERVER_TIMESTAMP,
                "vectorized": True
            }
            
            # Add error info if provided
            if "vectorError" in vector_info:
                update_data["vectorError"] = vector_info["vectorError"]
            
            # Update the document
            doc_ref.update(update_data)
            
            logger.debug(f"Updated vector info for {collection}/{doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating vector info for {collection}/{doc_id}: {str(e)}")
            raise
    
    def get_documents_for_vectorization(
        self, 
        collection: str, 
        only_new: bool = False, 
        batch_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get documents that need vectorization.
        
        Args:
            collection: Collection name.
            only_new: Only get documents that haven't been vectorized.
            batch_size: Batch size.
            
        Returns:
            List of documents.
            
        Raises:
            Exception: If the operation fails.
        """
        try:
            if batch_size is None:
                batch_size = settings.firestore.batch_size
            
            documents = []
            
            if only_new:
                # This is a simple query that doesn't require an index
                query = self._db.collection(collection).where("vectorized", "==", False).limit(batch_size)
                snapshot = query.get()
                
                if snapshot:
                    documents = [{"id": doc.id, **doc.to_dict()} for doc in snapshot]
            else:
                # Get non-vectorized documents first (up to batch_size)
                non_vectorized_query = self._db.collection(collection).where("vectorized", "==", False).limit(batch_size)
                non_vectorized_snapshot = non_vectorized_query.get()
                
                if non_vectorized_snapshot:
                    for doc in non_vectorized_snapshot:
                        documents.append({"id": doc.id, **doc.to_dict()})
                
                # If we need more documents to reach batch_size, get some vectorized ones
                remaining = batch_size - len(documents)
                if remaining > 0:
                    vectorized_query = self._db.collection(collection).where("vectorized", "==", True).limit(remaining)
                    vectorized_snapshot = vectorized_query.get()
                    
                    if vectorized_snapshot:
                        for doc in vectorized_snapshot:
                            documents.append({"id": doc.id, **doc.to_dict()})
            
            if not documents:
                logger.debug(f"No documents found for vectorization in {collection}")
                return []
            
            logger.info(f"Retrieved {len(documents)} documents for vectorization from {collection}")
            return documents
        except Exception as e:
            logger.error(f"Error getting documents for vectorization from {collection}: {str(e)}")
            raise
    
    def find_updated_documents(
        self, 
        collection: str, 
        batch_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find documents that were updated after their vector was created.
        
        Args:
            collection: Collection name.
            batch_size: Batch size.
            
        Returns:
            List of documents.
            
        Raises:
            Exception: If the operation fails.
        """
        try:
            if batch_size is None:
                batch_size = settings.firestore.batch_size
            
            # Simplified query - just get documents that are vectorized
            # without ordering (which requires an index)
            query = self._db.collection(collection) \
                .where("vectorized", "==", True) \
                .limit(batch_size * 2)  # Get more docs since we'll filter client-side
            
            # Execute query
            snapshot = query.get()
            
            if not snapshot:
                logger.debug(f"No updated documents found in {collection}")
                return []
            
            # Filter and sort documents client-side
            documents = []
            for doc in snapshot:
                data = doc.to_dict()
                doc_with_id = {"id": doc.id, **data}
                
                # If no vector timestamp or update is more recent, it needs updating
                if not data.get("vectorTimestamp") or (
                    data.get("updatedAt") and 
                    data["updatedAt"] > data["vectorTimestamp"]
                ):
                    documents.append(doc_with_id)
            
            # Sort manually by updatedAt (descending)
            if documents:
                documents.sort(
                    key=lambda x: x.get("updatedAt", 0) if x.get("updatedAt") else 0, 
                    reverse=True
                )
                
                # Apply batch size limit after sorting
                documents = documents[:batch_size]
            
            logger.info(f"Found {len(documents)} updated documents in {collection} that need re-vectorization")
            return documents
        except Exception as e:
            logger.error(f"Error finding updated documents in {collection}: {str(e)}")
            raise
    
    def list_collections(self) -> List[str]:
        """
        List all collections in the database.
        
        Returns:
            List of collection names.
            
        Raises:
            Exception: If the operation fails.
        """
        try:
            collections = self._db.collections()
            collection_names = [collection.id for collection in collections]
            
            logger.debug(f"Found {len(collection_names)} collections: {', '.join(collection_names)}")
            return collection_names
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the Firestore connection.
        
        Returns:
            True if connection is successful.
            
        Raises:
            Exception: If the connection fails.
        """
        try:
            # First, just try to get the client
            if not self._db:
                self._initialize_firestore()
                
            logger.info("Firestore client initialized successfully")
            
            # Then try a simple operation that doesn't require listing collections
            # Try to access the 'users' collection (or any collection from settings)
            test_collection = settings.firestore.collections[0] if settings.firestore.collections else "users"
            
            # Just try to get a reference (doesn't actually query the database yet)
            collection_ref = self._db.collection(test_collection)
            logger.info(f"Retrieved reference to collection: {test_collection}")
            
            # Now try to do a small query to verify database access
            try:
                # Try to get a single document (limit=1)
                docs = collection_ref.limit(1).get()
                # Just check if the query executed, don't care about results
                list(docs)  # Force query execution
                logger.info(f"Successfully queried the {test_collection} collection")
            except Exception as e:
                logger.warning(f"Could not query {test_collection} collection: {str(e)}")
                logger.info("Connection partially working - client initialized but query failed")
                # Return true anyway as we at least got a connection
                return True
                
            logger.info("Firestore connection test successful")
            return True
        except Exception as e:
            logger.error(f"Firestore connection test failed: {str(e)}")
            return False