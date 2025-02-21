import firebase_admin
from firebase_admin import credentials, firestore
from config.config import config
import os

class FirestoreClient:
    def __init__(self):
        """
        Initialize Firestore client with the given service account credentials.
        """
        try:
            print(os.path.join(os.getcwd(), config.DB_CREDENTIALS_PATH))
            self.cred = credentials.Certificate(config.DB_CREDENTIALS_PATH)
            firebase_admin.initialize_app(self.cred)
            self.db = firestore.client(database_id=config.DB_NAME)
        except Exception as e:
            raise RuntimeError(f"Error initializing Firestore client: {e}")
        
    
    def insert_entry(self, collection_name, data, data_id):
        """
        Insert a single entry into the specified Firestore collection.
        """
        doc_ref = self.db.collection(collection_name).document(data_id).add(data)
        print(f"Document inserted with ID: {doc_ref[1].id}")
        
    
    def bulk_insert(self, collection_name, data_list, id_field):
        """
        Insert multiple entries into the specified Firestore collection.
        """
        try:
            batch = self.db.batch()
            for data in data_list:
                data_id = data[id_field]
                doc_ref = self.db.collection(collection_name).document(data_id)
                batch.set(doc_ref, data)
            batch.commit()
            print(f"Inserted {len(data_list)} documents into {collection_name}.")
        except Exception as e:
            raise RuntimeError(f"Error performing bulk insert into {collection_name}: {e}")
    
    
    def get_all_docs(self, collection_name):
        """
        Retrieve all user document IDs and first_name, last_name fields from the 'users' collection.
        """
        try:
            users = self.db.collection(collection_name).get()
            return users
        except Exception as e:
            raise RuntimeError(f"Error retrieving users: {e}")