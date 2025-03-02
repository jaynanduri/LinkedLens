#!/usr/bin/env python3

from src.clients.firestore_client import FirestoreClient
from src.utils.logger import logger

def check_vectorized_status(initialize_field=False):
    """
    Check the vectorized field status in documents.
    
    Args:
        initialize_field: If True, initialize the vectorized field to False for documents that don't have it.
    """
    try:
        # Initialize the Firestore client
        client = FirestoreClient()
        
        # Collections to check
        collections = ['users', 'jobs', 'posts']
        
        for coll in collections:
            # Get a sample of documents
            docs = client._db.collection(coll).limit(5).get()
            
            print(f"\nSample documents from {coll}:")
            for doc in docs:
                doc_dict = doc.to_dict()
                vectorized = doc_dict.get("vectorized", "field not present")
                print(f"ID: {doc.id}, vectorized: {vectorized}")
            
            # Count documents with and without vectorized field
            total_docs = 0
            vectorized_true = 0
            vectorized_false = 0
            missing_field = 0
            updated_count = 0
            
            # Get all documents (careful with large collections)
            all_docs = client._db.collection(coll).get()
            
            for doc in all_docs:
                total_docs += 1
                doc_dict = doc.to_dict()
                
                if "vectorized" not in doc_dict:
                    missing_field += 1
                    
                    # Initialize the vectorized field if requested
                    if initialize_field:
                        client._db.collection(coll).document(doc.id).update({"vectorized": False})
                        updated_count += 1
                        
                elif doc_dict["vectorized"] is True:
                    vectorized_true += 1
                else:
                    vectorized_false += 1
            
            print(f"\nStatistics for {coll}:")
            print(f"Total documents: {total_docs}")
            print(f"Documents with vectorized=True: {vectorized_true}")
            print(f"Documents with vectorized=False: {vectorized_false}")
            print(f"Documents missing vectorized field: {missing_field}")
            
            if initialize_field:
                print(f"Documents updated with vectorized=False: {updated_count}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check and initialize vectorized field in Firestore documents")
    parser.add_argument('--initialize', '-i', action='store_true', help='Initialize vectorized field to False for all documents that lack it')
    
    args = parser.parse_args()
    
    check_vectorized_status(initialize_field=args.initialize) 