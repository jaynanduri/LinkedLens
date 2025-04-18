from typing import Dict, Any


class MockPineconeClient:
    def __init__(self):
        self.index_created = False
        self.index_exists = True
        self.embeddings_stored = []

    def get_index(self):
        if self.index_exists:
            return "mock-index"
        raise ValueError("Index does not exist")

    def get_stats(self):
        return {
            "totalVectorCount": 123,
            "namespaces": {"test_ns": {"vectorCount": 123}}
        }

    def create_index(self, **kwargs):
        self.index_created = True
        return "created"

    def store_embeddings(self, embeddings, namespace):
        self.embeddings_stored.append((embeddings, namespace))
        return {"upserted": len(embeddings)}


class MockFirestoreClient:
    def __init__(self):
        self.call_log = []

    def get_documents_for_vectorization(self, collection, only_new=False, additional_filters=None, batch_size=10):
        self.call_log.append("get_documents")
        # Simulate return of mock documents
        return [{"id": f"doc_{i}", "content": "Some text"} for i in range(5)]

    def bulk_update_vector_info(self, collection, doc_ids):
        self.call_log.append("bulk_update")
        return {"updated": len(doc_ids)}


class MockDocumentProcessor:
    def __init__(self):
        self.processed = []

    def process_documents(self, batch, namespace, collection):
        self.processed.append((batch, namespace, collection))
        # Simulate vector output
        return {
            doc["id"]: {
                "id": doc["id"],
                "values": [0.1] * 384,
                "metadata": doc
            } for doc in batch
        }
