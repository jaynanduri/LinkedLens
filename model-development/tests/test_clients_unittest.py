import os
import sys
from mock_classes import *
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from clients.embedding_client import EmbeddingClient
from clients.pinecone_client import PineconeClient
from unittest.mock import patch, MagicMock
import unittest     




class TestPineconeClient(unittest.TestCase):

    @patch.object(PineconeClient, "__init__", lambda self: None)
    def setUp(self):
        """Initialize PineconeClient with mock Pinecone"""
        self.client = PineconeClient()
        self.client._pinecone = MagicMock()
        

    def test_get_index(self):
        """Test retrieving index"""
        mock_index = MagicMock()
    
        mock_index_object = MagicMock()
        mock_index_object.name = "dummy-index"
        
        self.client._pinecone.list_indexes.return_value = [mock_index_object]  
        self.client._pinecone.Index.return_value = mock_index
        index = self.client.get_index("dummy-index")
        self.assertEqual(index, mock_index)

    @patch.object(PineconeClient, "get_index")
    def test_get_stats(self, mock_get_index):
        """Test fetching index stats"""
        mock_index = MagicMock()
        mock_index.describe_index_stats.return_value = DummyStats()
        mock_get_index.return_value = mock_index

        stats = self.client.get_stats()
        self.assertEqual(stats["totalVectorCount"], 10300)
        self.assertDictEqual(stats["namespaces"], {"namespace1": 10000, "namespace2": 300})

    @patch.object(PineconeClient, "get_index")
    def test_query_similar(self, mock_get_index):
        """Test querying similar vectors"""
        mock_index = MagicMock()
        mock_index.query.return_value = MagicMock(matches=[
            {
                "id": "id1_chunk_3",
                "metadata": {"title": "Title"},
                "score": 0.643127739
            }
        ])
        mock_get_index.return_value = mock_index

        results = self.client.query_similar([0.1, 0.2, 0.3], top_k=1)
        self.assertTrue(hasattr(results, "matches"))
        self.assertEqual(results.matches[0]["id"], "id1_chunk_3")

    @patch.object(PineconeClient, "get_index")
    def test_fetch_by_vector_ids(self, mock_get_index):
        """Test fetching vectors by ID"""
        mock_index = MagicMock()
        mock_index.fetch.return_value = DummyFetchResponse("namespace", ["dummy_id"])
        mock_get_index.return_value = mock_index

        results = self.client.fetch_by_vector_ids(["dummy_id"]).to_dict()
        self.assertIn("dummy_id", results["vectors"])

class TestEmbeddingClient(unittest.TestCase):
    
    @patch("clients.embedding_client.SentenceTransformer")
    def test_generate_embedding(self, mock_transformer):
        """Test SentenceTransformer embedding generation"""
        mock_instance = MagicMock()
        mock_instance.encode.return_value = torch.ones(384)  
        mock_transformer.return_value = mock_instance  

        client = EmbeddingClient()
        text = "Test embedding"
        embedding = client.generate_embedding(text)

        self.assertEqual(len(embedding), 384)
        self.assertEqual(embedding, [1.0] * 384)


if __name__ == '__main__':
    unittest.main()
