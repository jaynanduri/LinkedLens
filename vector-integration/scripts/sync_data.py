#!/usr/bin/env python3
"""
Script to sync data between Firestore and Pinecone.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.clients.firestore_client import FirestoreClient
from src.clients.pinecone_client import PineconeClient
from src.processors.document_processor import DocumentProcessor
from src.utils.logger import logger


def process_collection(
    collection: str,
    doc_type: str,
    only_new: bool = False,
    batch_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process all documents of a specific collection.
    
    Args:
        collection: Collection name.
        doc_type: Document type (user, job, post).
        only_new: Only process new documents.
        batch_size: Batch size.
        
    Returns:
        Processing results.
        
    Raises:
        Exception: If processing fails.
    """
    try:
        logger.info(f"Starting batch processing for collection: {collection}", extra={"onlyNew": only_new})
        
        # Initialize clients
        firestore_client = FirestoreClient()
        pinecone_client = PineconeClient()
        document_processor = DocumentProcessor()
        
        if batch_size is None:
            batch_size = settings.firestore.batch_size
        
        # Get documents to process
        if only_new:
            # Get only documents that haven't been vectorized
            documents = firestore_client.get_documents_for_vectorization(collection, only_new=True, batch_size=batch_size)
        else:
            # Also include documents that need updating (changed since last vectorization)
            new_docs = firestore_client.get_documents_for_vectorization(collection, only_new=True, batch_size=batch_size)
            updated_docs = firestore_client.find_updated_documents(collection, batch_size=batch_size)
            
            documents = new_docs + updated_docs
        
        if not documents:
            logger.info(f"No documents to process in collection: {collection}")
            return {"processed": 0, "collection": collection}
        
        # Process in batches to manage memory and API limits
        processed = 0
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            current_batch = (i // batch_size) + 1
            
            # Process and generate embeddings
            processed_data = document_processor.process_documents(batch, doc_type)
            
            # Store embeddings in Pinecone
            results = pinecone_client.store_embeddings(processed_data)
            
            # Update Firestore documents with vector info
            for doc in batch:
                firestore_client.update_vector_info(collection, doc["id"], {
                    "vectorId": doc["id"],
                    "namespace": doc_type
                })
            
            processed += len(batch)
            
            logger.info(
                f"Processed batch {current_batch} of {total_batches}",
                extra={
                    "collection": collection,
                    "batchSize": len(batch),
                    "processed": processed,
                    "total": len(documents)
                }
            )
            
            # Sleep a bit to avoid rate limits
            if i + batch_size < len(documents):
                time.sleep(1)
        
        logger.info(
            f"Completed batch processing for collection: {collection}",
            extra={"processed": processed, "total": len(documents)}
        )
        
        return {
            "collection": collection,
            "processed": processed,
            "total": len(documents)
        }
    except Exception as e:
        logger.error(
            f"Error processing collection {collection}: {str(e)}",
            extra={"collection": collection}
        )
        raise


def process_all_collections(only_new: bool = False) -> List[Dict[str, Any]]:
    """
    Process all collections configured in the system.
    
    Args:
        only_new: Only process new documents.
        
    Returns:
        Array of results for each collection.
        
    Raises:
        Exception: If processing fails.
    """
    collections = settings.firestore.collections
    results = []
    
    logger.info(
        f"Starting batch processing for all collections ({len(collections)})",
        extra={"onlyNew": only_new}
    )
    
    for collection in collections:
        try:
            doc_type = settings.pinecone.collections.get(collection)
            
            if not doc_type:
                logger.warning(f"No type mapping found for collection: {collection}, skipping")
                continue
            
            result = process_collection(collection, doc_type, only_new)
            results.append(result)
        except Exception as e:
            logger.error(
                f"Error processing collection: {collection}: {str(e)}",
                extra={"collection": collection}
            )
            results.append({
                "collection": collection,
                "error": str(e),
                "processed": 0
            })
    
    # Log summary of results
    total_processed = sum(result.get("processed", 0) for result in results)
    
    logger.info(
        "Batch processing completed for all collections",
        extra={"collections": len(results), "totalProcessed": total_processed}
    )
    
    return results


def main():
    """Main function for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Sync data between Firestore and Pinecone")
    parser.add_argument(
        "--collection", "-c",
        help="Collection to process (if not specified, process all collections)"
    )
    parser.add_argument(
        "--only-new", "-n",
        action="store_true",
        help="Only process new documents (not already vectorized)"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        help="Batch size for processing (default from config)"
    )
    
    args = parser.parse_args()
    
    try:
        # Check if Pinecone is initialized
        pinecone_client = PineconeClient()
        try:
            pinecone_client.get_index()
        except ValueError:
            logger.error(
                f"Pinecone index '{settings.pinecone.index_name}' does not exist. Run init_pinecone.py first."
            )
            sys.exit(1)
        
        # Run the appropriate sync
        if args.collection:
            # Check if collection is valid
            if args.collection not in settings.firestore.collections:
                logger.error(f"Invalid collection: {args.collection}")
                logger.info(f"Valid collections: {', '.join(settings.firestore.collections)}")
                sys.exit(1)
            
            # Get document type
            doc_type = settings.pinecone.collections.get(args.collection)
            if not doc_type:
                logger.error(f"No type mapping found for collection: {args.collection}")
                sys.exit(1)
            
            # Process the collection
            logger.info(f"Processing collection: {args.collection}")
            result = process_collection(
                args.collection, 
                doc_type, 
                args.only_new, 
                args.batch_size
            )
            
            logger.info(
                f"Collection {args.collection} sync completed",
                extra=result
            )
        else:
            # Process all collections
            logger.info("Processing all collections")
            results = process_all_collections(args.only_new)
            
            logger.info("All collections sync completed", extra={"results": results})
        
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in sync script: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()