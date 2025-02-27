import firebase_admin
from firebase_admin import credentials, firestore
from src.config.config import settings
from src.logger import logger

class FirestoreClient:
    def __init__(self):
        """
        Initialize Firestore client with the service account credentials.
        """
        try:
            self.cred = credentials.Certificate(settings.DB_CREDENTIALS_PATH)
            firebase_admin.initialize_app(self.cred)
            self.db = firestore.client(database_id=settings.DB_NAME)
            logger.info("Connected to Firestore")
        except Exception as e:
            logger.error(f"Error initializing Firestore client: {e}")
            raise RuntimeError(f"Error initializing Firestore client: {e}")
        
    
    def insert_entry(self, collection_name, data, data_id):
        """
        Insert a single entry into the specified Firestore collection.
        """
        try:
            doc_ref = self.db.collection(collection_name).document(data_id).set(data)
            logger.info(f"1 document inserted in {collection_name} collection")
        except Exception as e:
            logger.error(f"Error performing insert into {collection_name}: {e}")
            raise RuntimeError(f"Error performing insert into {collection_name}: {e}")
    
    
    def bulk_insert(self, collection_name: str, data_list, id_field: str):
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
            logger.info(f"Inserted {len(data_list)} documents into {collection_name}.")
        except Exception as e:
            logger.error(f"Error performing bulk insert into {collection_name}: {e}")
            raise RuntimeError(f"Error performing bulk insert into {collection_name}: {e}")
    
    
    def get_all_docs(self, collection_name: str):
        """
        Retrieve all user document IDs and first_name, last_name fields from the 'users' collection.
        """
        try:
            users = self.db.collection(collection_name).get()
            return users
        except Exception as e:
            logger.error(f"Error retrieving users: {e}")
            raise RuntimeError(f"Error retrieving users: {e}")
        
    def filter_docs_equal(self, collection_name: str, field_name: str, value: str):
        """
        Retrieve documents from a collection where the specified field equals the given value.
        """
        try:
            docs = self.db.collection(collection_name).where(field_name, "==", value).get()
            logger.info(f"Retrieved {len(docs)} documents where {field_name} == {value}.")
            return docs
        except Exception as e:
            logger.error(f"Error filtering documents in {collection_name} by {field_name} == {value}: {e}")
            raise RuntimeError(f"Error filtering documents in {collection_name} by {field_name} == {value}: {e}")