import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import DELETE_FIELD
from datetime import datetime, timezone


def update_post_collection(collection, db_client):
    # get all docs of collection
    docs = db_client.collection(collection).get()
    print(f"Number of docs fetched for {collection}: {len(docs)}")
    for doc in docs:
        doc_ref = db.collection(collection).document(doc.id)

        current_ts = int(datetime.now(timezone.utc).timestamp())
        ttl = current_ts + 90 * 24 * 60 * 60
        update_data = {
            "timestamp": DELETE_FIELD,  # This removes the field
            "createdAt": current_ts,
            "updatedAt": current_ts,
            "ttl": ttl,
            "vectorized": False,
            "vectorTimestamp" : DELETE_FIELD
        }
        doc_ref.update(update_data)
        print(f"Updated document {doc.id}")
    print(f"Completed updated for {collection} collection")

def update_job_collection(collection, db_client):
    # get all docs of collection
    docs = db_client.collection(collection).get()
    print(f"Number of docs fetched for {collection}: {len(docs)}")
    for doc in docs:
        doc_ref = db.collection(collection).document(doc.id)

        current_ts = int(datetime.now(timezone.utc).timestamp())
        ttl = current_ts + 90 * 24 * 60 * 60
        update_data = {
            "timestamp": DELETE_FIELD,  # This removes the field
            "createdAt": current_ts,
            "updatedAt": current_ts,
            "ttl": ttl,
            # "vectorized": False,
            # "vectorTimestamp" : DELETE_FIELD
        }
        doc_ref.update(update_data)
        print(f"Updated document {doc.id}")
    print(f"Completed updated for {collection} collection")

def update_user_collection(collection, db_client):
    # get all docs of collection
    docs = db_client.collection(collection).get()
    print(f"Number of docs fetched for {collection}: {len(docs)}")
    for doc in docs:
        doc_ref = db.collection(collection).document(doc.id)

        current_ts = int(datetime.now(timezone.utc).timestamp())
        update_data = {
            "timestamp": DELETE_FIELD,  # This removes the field
            "createdAt": current_ts,
            "updatedAt": current_ts,
            # "vectorized": False,
            # "vectorTimestamp" : DELETE_FIELD
        }
        doc_ref.update(update_data)
        print(f"Updated document {doc.id}")
    print(f"Completed updated for {collection} collection")



if __name__ == '__main__':
    try:
        cred = credentials.Certificate('./credentials/linkedlens-firestore-srvc-acc.json')
        firebase_admin.initialize_app(cred)
        db = firestore.client(database_id='vm-test')
        print("DB:", db)
        # update_user_collection("users", db)
        # update_job_collection("jobs", db)
        update_post_collection("posts", db)
    except Exception as e:
        print(f"Failed: {e}")

"""
Update all records
Users - add createdAt and UpdatedAt in int
Posts - Update timestamp change to createdAt to utc timezone and add UpdatedAt
Jobs - add createdAt and UpdatedAt in int
"""