from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter
from datetime import datetime, timezone
from config.settings import settings
from logger import logger
import os


class FirestoreClient:
    """Client for interacting with Firestore Database."""
    
    _instance = None
    _db = None
    _config = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(FirestoreClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Firestore client."""
        if self._db is None:
            self._initialize_firestore()
        self.config_path = config_path
        self._load_config()
    
    def _initialize_firestore(self):
        """Initialize the Firestore client."""
        try:
            # Get credentials path from settings
            creds_path = settings.GOOGLE_APPLICATION_CREDENTIALS
            creds_path = Path(creds_path).resolve()
            
            logger.info(f"Found credentials file at: {creds_path}")
            
            if not creds_path.exists():
                raise FileNotFoundError(f"Firestore credentials file not found at: {creds_path}")
            
            # Get database ID from settings
            db_name = settings.firestore_setting.database_name
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

    def _load_config(self):
        """
        Load test data configuration for generating queries.
        
        This method attempts to load configuration in the following order:
        1. From a JSON file if config_path is provided
        2. From settings if no path is provided or loading from file fails
        
        The configuration should contain collection names as keys, with each value
        containing "ids" (list of document IDs) and "field_paths" (list of fields to retrieve).
        
        Example JSON format:
        {
            "jobs": {
                "ids": ["job1", "job2"],
                "field_paths": ["title", "description"]
            },
            "posts": {
                "ids": ["post1", "post2"],
                "field_paths": ["content", "job_id"]
            }
        }
        """
        try:
            if self.config_path:
                resolved_path = Path(self.config_path).resolve()
                if not os.path.exists(resolved_path):
                    logger.warning(f"Config path does not exist: {resolved_path}")

                elif not str(resolved_path).lower().endswith('.json'):
                    logger.warning(f"Config file is not a JSON file: {resolved_path}")
                else:
                    logger.info(f"Loading test IDs from json file_path : {resolved_path}")
                    # load json file
                    try:
                        with open(resolved_path, 'r') as file:
                            # Load the JSON directly without transformation
                            self._config = json.load(file)
                            logger.info(f"Loaded collection configuration from: {resolved_path}")
                            
                    except Exception as file_load_err:
                        logger.error(f"Failed to load from provided json filepath : {resolved_path}")
            if not self._config:
                logger.info(f"No config filepath provided. Loading default ids... ")
                self._config = settings.firestore_setting.test_data
        except Exception as e:
            logger.error(f"Failed to load test IDs details for generating test queries: {str(e)}")

    
    def _get_test_data_by_ids(self, collection_name: str, doc_ids: Optional[List[str]] = None)-> List[Dict[str, Any]]:
        """
        Retrieve multiple documents by their IDs from a specified collection.
        
        This internal method fetches documents from Firestore based on either:
        - Document IDs provided directly via the doc_ids parameter
        - Document IDs from the configuration for the specified collection
        
        Args:
            collection_name: Name of the collection to retrieve documents from
            doc_ids: List of document IDs to retrieve. If None, will use IDs from config.
            
        Returns:
            List of document data dictionaries with added ID and collection information
            
        Raises:
            ValueError: If the collection name is invalid or no document IDs are available
        """

        if not doc_ids and collection_name not in self._config.keys():
            raise ValueError(f"Invalid collection name: {collection_name}. Check your collection configuration.")
        
        test_ids_list = None

        if not doc_ids:
            test_ids_list = self._config.get(collection_name, {}).get("ids",[])
        else:
            test_ids_list = doc_ids

        if not test_ids_list:
            raise ValueError(f"No list of ids was available for the given collection.")
        logger.info(f"Fetching test data from FireStore")
        doc_refs = [self._db.collection(collection_name).document(doc_id) for doc_id in test_ids_list]
        docs = self._db.get_all(doc_refs, field_paths=self._config[collection_name].get("field_paths", None))
        results = []
        for doc in docs:
                if doc.exists:
                    doc_data = doc.to_dict()
                    doc_data['id'] = doc.id
                    doc_data['collection'] = collection_name
                    results.append(doc_data)
        logger.info(f"Fetched {len(results)} docs from collection : {collection_name}",
                    extra={"json_fields": {"collection_name": collection_name, "records": len(results)}})
        return results

    def get_test_docs(self, test_data_config: Dict[str, Dict]=None)-> List[Dict]:
        """
        Retrieve test documents from multiple collections based on configuration.
        
        This is the main public method for retrieving test data. It processes all collections
        defined in the configuration, fetching the specified documents from each collection,
        and returns a combined list of all retrieved documents.
        
        Args:
            test_data_config: Optional dictionary specifying collections, their document IDs, 
                              and field paths. If not provided, uses the configuration loaded
                              during initialization.
                              
        Returns:
            List of document dictionaries from all specified collections,
            with each document containing its ID and collection name
            
        Example:
            # Using default config from initialization
            docs = client.get_test_docs()
            
            # Using custom config
            custom_config = {
                "jobs": {
                    "ids": ["job1", "job2"],
                    "field_paths": ["title", "description"]
                }
            }
            docs = client.get_test_docs(custom_config)
        """
        if not test_data_config:
            test_data_config = self._config
            logger.warning(f"Loading data from configuration used for initialization.. ")
        

        test_docs = []

        for collection_name, details in test_data_config.items():
            res = self._get_test_data_by_ids(collection_name, details["ids"])
            test_docs.extend(res)

        logger.info(f"Extract Documents for Test: {len(test_docs)}")
        return test_docs