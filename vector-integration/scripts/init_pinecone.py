#!/usr/bin/env python3
"""
Script to initialize Pinecone index for the LinkedLens Vector Integration.
"""

import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.clients.pinecone_client import PineconeClient
from src.utils.logger import logger


def init_pinecone():
    """
    Initialize Pinecone index.
    
    Returns:
        Dict with initialization results.
    
    Raises:
        Exception: If initialization fails.
    """
    try:
        logger.info("Starting Pinecone index initialization")
        
        # Create Pinecone client
        pinecone_client = PineconeClient()
        
        # Check if index exists
        try:
            index = pinecone_client.get_index()
            
            # If we get here, the index exists
            logger.info("Pinecone index already exists, fetching stats...")
            
            # Get index stats
            stats = pinecone_client.get_stats()
            
            logger.info(
                "Pinecone index stats",
                extra={
                    "totalVectorCount": stats["totalVectorCount"],
                    "namespaces": list(stats["namespaces"].keys()),
                }
            )
            
            return {
                "status": "exists",
                "stats": stats,
            }
        except ValueError:
            # Index doesn't exist, create it
            logger.info("Pinecone index does not exist, creating new index...")
            
            # For free tier accounts, we need to use serverless
            is_free_tier = True  # Set to False for paid accounts
            
            if is_free_tier:
                pinecone_client.create_index(
                    index_name=settings.pinecone.index_name,
                    dimension=settings.pinecone.dimension,
                    serverless=True,
                    cloud="aws",
                    region="us-west-2",
                )
            else:
                pinecone_client.create_index(
                    index_name=settings.pinecone.index_name,
                    dimension=settings.pinecone.dimension,
                    serverless=False,
                )
            
            logger.info(f"Pinecone index '{settings.pinecone.index_name}' created successfully")
            
            return {
                "status": "created",
                "dimension": settings.pinecone.dimension,
                "indexName": settings.pinecone.index_name,
            }
    except Exception as e:
        logger.error(f"Error initializing Pinecone index: {str(e)}")
        raise


def main():
    """Main function for the script."""
    try:
        # Check for required environment variables
        if not settings.pinecone.api_key:
            logger.error("PINECONE_API_KEY environment variable is not set")
            sys.exit(1)
        
        if not settings.pinecone.environment:
            logger.error("PINECONE_ENVIRONMENT environment variable is not set")
            sys.exit(1)
        
        # Initialize Pinecone
        result = init_pinecone()
        
        logger.info("Pinecone initialization completed", extra=result)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pinecone initialization failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()