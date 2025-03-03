#!/usr/bin/env python3
"""
Script to test Firestore and Pinecone connections.
"""

import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings
from src.clients.firestore_client import FirestoreClient
from src.clients.pinecone_client import PineconeClient
from src.clients.embedding_client import EmbeddingClient
from src.utils.logger import logger


def test_firestore():
    """
    Test Firestore connection and list collections.
    
    Returns:
        Dict with connection status and collections.
    
    Raises:
        Exception: If the connection fails.
    """
    try:
        logger.info("Starting Firestore connection test")
        
        # Check credentials file
        creds_path = Path(settings.firestore.credentials_path).resolve()
        if not creds_path.exists():
            logger.error(f"Credentials file not found at: {creds_path}")
            return {"connected": False, "error": "Credentials file not found"}
        
        logger.info(f"Found credentials file at: {creds_path}")
        
        # Log database info
        db_name = settings.firestore.database_id or "default"
        logger.info(f"Using database: {db_name}")
        
        # Initialize client
        firestore_client = FirestoreClient()
        
        # Test connection
        connected = firestore_client.test_connection()
        
        if not connected:
            logger.error("Firestore connection test failed")
            return {"connected": False, "error": "Connection test failed"}
        
        # List collections
        collection_names = firestore_client.list_collections()
        
        if not collection_names:
            logger.info("No collections found in Firestore database")
            return {"connected": True, "collections": []}
        
        logger.info(f"Found {len(collection_names)} collections: {', '.join(collection_names)}")
        
        # For each collection, get a sample document
        sample_docs = {}
        for collection_name in collection_names:
            docs = firestore_client.get_documents(collection_name, limit=1)
            
            if docs:
                doc = docs[0]
                sample_docs[collection_name] = {
                    "id": doc["id"],
                    "fields": list(doc.keys())
                }
                # Log the actual document content
                logger.info(f"Sample document from {collection_name}:")
                # Convert to string for better logging
                doc_str = str({k: (v if len(str(v)) < 100 else f"{str(v)[:100]}...") for k, v in doc.items()})
                logger.info(doc_str)
            else:
                logger.info(f"Collection {collection_name} is empty")
        
        return {
            "connected": True,
            "collections": collection_names,
            "sample_docs": sample_docs
        }
    except Exception as e:
        logger.error(f"Error testing Firestore connection: {str(e)}")
        return {"connected": False, "error": str(e)}


def test_pinecone():
    """
    Test Pinecone connection and check index.
    
    Returns:
        Dict with connection status and index info.
    
    Raises:
        Exception: If the connection fails.
    """
    try:
        logger.info("Starting Pinecone connection test")
        
        # Check required environment variables
        if not settings.pinecone.api_key:
            logger.error("PINECONE_API_KEY environment variable is not set")
            return {"connected": False, "error": "PINECONE_API_KEY not set"}
        
        if not settings.pinecone.environment:
            logger.error("PINECONE_ENVIRONMENT environment variable is not set")
            return {"connected": False, "error": "PINECONE_ENVIRONMENT not set"}
        
        # Initialize client
        pinecone_client = PineconeClient()
        
        # Check if index exists
        try:
            index = pinecone_client.get_index()
            index_exists = True
            logger.info(f"Connected to Pinecone index: {settings.pinecone.index_name}")
            
            # Get stats
            stats = pinecone_client.get_stats()
            logger.info(
                "Pinecone index stats:",
                extra={
                    "totalVectorCount": stats["totalVectorCount"],
                    "namespaces": list(stats["namespaces"].keys() if stats["namespaces"] else []),
                }
            )
            
            return {
                "connected": True,
                "index_exists": True,
                "index_name": settings.pinecone.index_name,
                "stats": stats
            }
        except ValueError:
            logger.warning(f"Pinecone index '{settings.pinecone.index_name}' does not exist")
            
            # List available indices
            available_indices = [index.name for index in pinecone_client.client.list_indexes()]
            
            return {
                "connected": True,
                "index_exists": False,
                "available_indices": available_indices,
                "message": f"Index '{settings.pinecone.index_name}' does not exist. Run init_pinecone.py to create it."
            }
    except Exception as e:
        logger.error(f"Error testing Pinecone connection: {str(e)}")
        return {"connected": False, "error": str(e)}


def test_embedding():
    """
    Test embedding model.
    
    Returns:
        Dict with model info and test embedding.
    
    Raises:
        Exception: If the model fails to load.
    """
    try:
        logger.info("Testing embedding model")
        
        # Initialize client
        embedding_client = EmbeddingClient()
        
        # Generate a test embedding
        text = "This is a test document for LinkedLens"
        embedding = embedding_client.generate_embedding(text)
        
        logger.info(
            f"Successfully generated test embedding with model: {settings.embedding.model_name}",
            extra={"dimension": len(embedding)}
        )
        
        return {
            "success": True,
            "model": settings.embedding.model_name,
            "dimension": len(embedding),
            "sample_values": embedding[:5]  # First 5 values
        }
    except Exception as e:
        logger.error(f"Error testing embedding model: {str(e)}")
        return {"success": False, "error": str(e)}


def main():
    """Main function for the script."""
    results = {}
    
    # Test Firestore
    logger.info("=" * 50)
    logger.info("TESTING FIRESTORE CONNECTION")
    logger.info("=" * 50)
    results["firestore"] = test_firestore()
    
    # Test Pinecone
    logger.info("\n" + "=" * 50)
    logger.info("TESTING PINECONE CONNECTION")
    logger.info("=" * 50)
    results["pinecone"] = test_pinecone()
    
    # Test Embedding
    logger.info("\n" + "=" * 50)
    logger.info("TESTING EMBEDDING MODEL")
    logger.info("=" * 50)
    results["embedding"] = test_embedding()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("CONNECTION TEST SUMMARY")
    logger.info("=" * 50)
    
    firestore_status = "✅ Connected" if results["firestore"]["connected"] else "❌ Failed"
    pinecone_status = "✅ Connected" if results["pinecone"].get("connected", False) else "❌ Failed"
    embedding_status = "✅ Working" if results["embedding"]["success"] else "❌ Failed"
    
    logger.info(f"Firestore: {firestore_status}")
    logger.info(f"Pinecone:  {pinecone_status}")
    logger.info(f"Embedding: {embedding_status}")
    
    # Exit with appropriate status code
    if (results["firestore"]["connected"] and 
        results["pinecone"].get("connected", False) and 
        results["embedding"]["success"]):
        logger.info("\nAll connections successful! ✅")
        sys.exit(0)
    else:
        logger.error("\nSome connections failed. See logs for details. ❌")
        sys.exit(1)


if __name__ == "__main__":
    main()