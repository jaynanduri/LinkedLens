"""
Main entry point for the LinkedLens Vector Integration.
"""

import argparse
import sys
from typing import Any, Dict, List, Optional

from src.config.settings import settings
from src.clients.firestore_client import FirestoreClient
from src.clients.pinecone_client import PineconeClient
from src.processors.document_processor import DocumentProcessor
from src.utils.logger import logger


def init_pinecone() -> Dict[str, Any]:
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


def search_similar(
    query_text: str,
    collection_type: str,
    top_k: int = 10,
    filter_dict: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Search for similar documents.
    
    Args:
        query_text: Query text.
        collection_type: Collection type to search (user, job, post).
        top_k: Number of results to return.
        filter_dict: Metadata filter.
        
    Returns:
        Query results.
        
    Raises:
        Exception: If the search fails.
    """
    try:
        logger.info(f"Searching for similar documents to: '{query_text}'")
        
        # Initialize clients
        pinecone_client = PineconeClient()
        embedding_client = DocumentProcessor().embedding_client
        
        # Generate embedding for query
        query_embedding = embedding_client.generate_embedding(query_text)
        
        # Query Pinecone
        results = pinecone_client.query_similar(
            query_vector=query_embedding,
            namespace=collection_type,
            top_k=top_k,
            filter=filter_dict
        )
        
        logger.info(f"Found {len(results.matches)} similar documents")
        
        # Format results
        formatted_results = []
        for match in results.matches:
            formatted_results.append({
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata
            })
        
        return {
            "query": query_text,
            "type": collection_type,
            "results": formatted_results
        }
    except Exception as e:
        logger.error(f"Error searching similar documents: {str(e)}")
        raise


def main(action: str):
    """Main function for the script."""
    
    try:
        if action == "init":
            # Initialize Pinecone index
            result = init_pinecone()
            logger.info("Pinecone initialization completed", extra=result)
        
        elif action== "sync":
            # Check if Pinecone is initialized
            pinecone_client = PineconeClient()
            try:
                pinecone_client.get_index()
            except ValueError:
                logger.error(
                    f"Pinecone index '{settings.pinecone.index_name}' does not exist. Run 'init' command first."
                )
                sys.exit(1)
            
            results = process_all_collections()
            logger.info("All collections sync completed", extra={"results": results})
        
        elif action == "search":
            pass
            # TODO
            # # Perform search
            # results = search_similar(args.query, args.type, args.limit)
            
            # # Display results
            # print(f"\nSearch results for '{args.query}' in {args.type}:")
            # print(f"Found {len(results['results'])} matches\n")
            
            # for i, result in enumerate(results['results']):
            #     print(f"{i+1}. Score: {result['score']:.4f}")
            #     print(f"   ID: {result['id']}")
                
            #     # Print important metadata
            #     if 'metadata' in result:
            #         meta = result['metadata']
            #         for key, value in meta.items():
            #             if key in ['name', 'title', 'company', 'skills', 'headline', 'tags']:
            #                 print(f"   {key}: {value}")
            #     print()
        
        elif action == "test":
            # Import the test connections module and run tests
            from src.scripts.test_connections import test_firestore, test_pinecone, test_embedding
            
            firestore_result = test_firestore()
            pinecone_result = test_pinecone()
            embedding_result = test_embedding()
            
            # Summary
            print("\n" + "=" * 50)
            print("CONNECTION TEST SUMMARY")
            print("=" * 50)
            
            firestore_status = "✅ Connected" if firestore_result["connected"] else "❌ Failed"
            pinecone_status = "✅ Connected" if pinecone_result.get("connected", False) else "❌ Failed"
            embedding_status = "✅ Working" if embedding_result["success"] else "❌ Failed"
            
            print(f"Firestore: {firestore_status}")
            print(f"Pinecone:  {pinecone_status}")
            print(f"Embedding: {embedding_status}")
            
            # Exit with appropriate status code
            if (firestore_result["connected"] and 
                pinecone_result.get("connected", False) and 
                embedding_result["success"]):
                print("\nAll connections successful! ✅")
                sys.exit(0)
            else:
                print("\nSome connections failed. See logs for details. ❌")
                sys.exit(1)
        
        else:
            logger.error(f"Invalid action: {action}")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

def load_env():
    print("Success")
