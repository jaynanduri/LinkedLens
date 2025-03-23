"""
Main entry point for the LinkedLens Vector Integration.
"""

from typing import Any, Dict, List, Optional

from src.config.settings import settings
from google.cloud.firestore_v1 import FieldFilter
from src.clients.firestore_client import FirestoreClient
from src.clients.pinecone_client import PineconeClient
from src.processors.document_processor import DocumentProcessor
from src.utils.logger import logger
from src.scripts.test_connections import test_firestore, test_pinecone, test_embedding


def init_pinecone() -> Dict[str, Any]:
    """
    Initialize Pinecone index.
    
    Returns:
        Dict with initialization results(stats).
        
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
            
            result =  {
                        "status": "exists",
                        "stats": stats,
                    }
            logger.info("Pinecone initialization completed", extra=result)
            return result
        
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
                    cloud=settings.pinecone.cloud,
                    region=settings.pinecone.region,
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

def test_connections() -> None:
    """
    Tests connections to Firestore, Pinecone, and the embedding model.

    This function checks connectivity and functionality for the three services:
    - Firestore: Verifies if Firestore is accessible.
    - Pinecone: Confirms if the vector database is available.
    - Embedding Model: Ensures the embedding model is functioning correctly.

    Logs the connection test results and provides a summary.

    Raises:
        Exception: If any of the connection tests fail.
    """
    try:
        firestore_result = test_firestore()
        pinecone_result = test_pinecone()
        embedding_result = test_embedding()
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("CONNECTION TEST SUMMARY")
        logger.info("=" * 50)
        
        firestore_status = "✅ Connected" if firestore_result["connected"] else "❌ Failed"
        pinecone_status = "✅ Connected" if pinecone_result.get("connected", False) else "❌ Failed"
        embedding_status = "✅ Working" if embedding_result["success"] else "❌ Failed"
        
        logger.info(f"Firestore: {firestore_status}")
        logger.info(f"Pinecone:  {pinecone_status}")
        logger.info(f"Embedding: {embedding_status}")
        
        # Exit with appropriate status code
        if (firestore_result["connected"] and 
            pinecone_result.get("connected", False) and 
            embedding_result["success"]):
            logger.info("\nAll connections successful! ✅")

    except Exception as e:
        logger.error(f"\nSome connections failed. See logs for details. ❌")

def get_doc_ids_from_vectors(vector_list: List[Dict])->List[str]:
    """
    Extracts unique document IDs from a list of vector records.
    
    Args:
        vector_list (list): List of vector records.
    
    Returns:
        List[str]: Unique Firestore document IDs.
    """
    doc_ids = {vector["metadata"].get("firestoreId") for vector in vector_list if "firestoreId" in vector["metadata"]}
    return list(doc_ids)

def ingest_namespace(namespace: str, collection: str, only_new: bool = False) -> Dict[str, Any]:
    """
    Ingests data from Firestore into the specified namespace in the Pinecone vector store.

    This function handles the ingestion process for a specific namespace by fetching 
    records from Firestore and adding them to Pinecone. It continues ingesting until all 
    relevant records (either only new or both new and updated) are processed, based on 
    the `only_new` parameter.

    Args:
        namespace (str): The namespace in Pinecone where data should be ingested.
        collection (str): The Firestore collection to fetch data from.
        only_new (bool, optional): If True, only new records are ingested; if False, both 
                                   new and updated records are ingested. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary containing ingestion results, such as the number of 
                        records processed and any errors encountered.

    Raises:
        Exception: If there is an error during the ingestion process.
    """
    try:
        logger.info(f"Starting batch processing for namespace: {namespace} collection: {collection}", extra={"onlyNew": only_new})
        # Initialize clients
        firestore_client = FirestoreClient()
        pinecone_client = PineconeClient()
        document_processor = DocumentProcessor()

        batch_size = settings.firestore.batch_size

        # check if namespace requires additional filters 
        additional_filters = []
        if collection == 'posts':
            if namespace == "user_post":
                additional_filters.append(FieldFilter("job_id", "==", ""))
            elif namespace == "recruiter_post":
                additional_filters.append(FieldFilter("job_id", "!=", ""))
            else:
                raise ValueError(f"Failed to apply additional filters for namespace {namespace} and collection {collection}")
        
        processed = 0
        total_docs_fetched = 0
        
        while True:
            logger.info(f"Processing collection {collection} in batch for namespace {namespace}")
            # fetch data to be processed in batches 500
            documents = firestore_client.get_documents_for_vectorization(collection, only_new=only_new, additional_filters=additional_filters, batch_size=batch_size)

            if not documents:
                logger.info(f"Processed all docs in collection {collection} for namespace {namespace}")
                return {
                    "collection": collection,
                    "processed": processed,
                    "total": total_docs_fetched,
                }
            
            total_docs_fetched = total_docs_fetched + len(documents)
            # total_batches = (len(documents) + batch_size - 1) // batch_size
            # if batch size changes later
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                current_batch = (i // batch_size) + 1
                logger.info(f"Processing batch {current_batch}..")
                # get the vectors for the batch 
                batch_vector_doc_grp = document_processor.process_documents(batch, namespace, collection)
                
                # Create batches to store embeddings and update DB:
                upsert_batch_size = settings.pinecone.batch_size
                batches = [] 
                current_upsert_batch = []
                current_count = 0

                # Create batches ensuring document vectors are in one batch
                for doc_id, vectors in batch_vector_doc_grp.items():
                    if current_count + len(vectors) > upsert_batch_size:
                        if current_upsert_batch:
                            batches.append(current_upsert_batch)
                        current_upsert_batch = []
                        current_count = 0

                    current_upsert_batch.extend(vectors)
                    current_count += len(vectors)

                if current_upsert_batch:
                    batches.append(current_upsert_batch)

                logger.info(f"Number of vector batches to upsert data processed in the batch {current_batch} : Vector batch number {len(batches)}")

                for batch_idx, upsert_batch in enumerate(batches):
                    logger.info(f"Loading embiddings for batch {batch_idx}")
                    # store embeddings
                    upsert_result = pinecone_client.store_embeddings(upsert_batch, namespace)
                    logger.info(f"Inserted Data to vector store : {upsert_result}")

                    logger.info(f"Update vector info in DB for batch {batch_idx}")
                    # udpate firestore
                    batch_doc_ids = get_doc_ids_from_vectors(upsert_batch)
                    logger.info(f"Number of docs to be updated in DB {len(batch_doc_ids)}")
                    db_result = firestore_client.bulk_update_vector_info(collection, batch_doc_ids)
                    logger.info(f"Updated vector info in DB for the batch {batch_idx}")

                logger.info(f"Completed upserting data for the current batch {current_batch}")
                docs_in_batch = len(batch_vector_doc_grp)
                processed += docs_in_batch
                logger.info(f"Total documents processed so far: {processed}/{total_docs_fetched}")

    except Exception as e:
        logger.error(
            f"Error processing for namespace {namespace} from collection {collection}: {str(e)}",
            extra={"collection": collection}
        )
        raise

def ingest_all_namespaces(only_new: bool = False):
    """
    Ingests data for all configured namespaces in the Pinecone vector store in batches.

    This function iterates through all namespaces defined in the settings and 
    ingests data for each.

    Args:
        only_new (bool, optional): If True, only new data is ingested; otherwise, 
                                   new and updated data is processed. Defaults to False.

    Returns:
        list: A list of dictionaries containing the ingestion results for each namespace.

    Raises:
        Exception: If an error occurs during ingestion for any namespace.
    """
    namespaces = list(settings.pinecone.namespace_collection.keys())
    results = []
    logger.info(
        f"Starting batch processing for all namespaces ({len(namespaces)})",
        extra={"onlyNew": only_new}
    )
    
    for namespace, collection in settings.pinecone.namespace_collection.items():
        try:
            logger.info(f"Ingesting data for {namespace} from collection {collection}")
            result = ingest_namespace(namespace, collection, only_new)
            logger.info(f"Batch processing completed for namespace {namespace}, Result : {result}")
            results.append(result)
        except Exception as e:
            logger.error(
                f"Error processing namespace: {collection}: {str(e)}",
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

def ingest_data(only_new: bool = False) -> None:
    """
    Ingests data into the Pinecone vector store.

    Args:
        only_new (bool, optional): If True, ingests only new data; otherwise, 
                                   ingests new and updated data. Defaults to False.

    Raises:
        ValueError: If the Pinecone index is not initialized.
        Exception: If the data ingestion process fails.
    """
    # Check if Pinecone is initialized
    pinecone_client = PineconeClient()
    try:
        pinecone_client.get_index()
    except ValueError:
        logger.error(
            f"Pinecone index '{settings.pinecone.index_name}' does not exist. Run 'init' command first."
        )
        raise
    try:
        logger.info(f"Ingesting data for all namespaces..")
        results = ingest_all_namespaces(only_new)
        logger.info("All collections sync completed", extra={"results": results})
    except Exception as e:
        logger.error(f"Failed to sync data to vector store: {e}")
        raise

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