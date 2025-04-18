import pytest
from unittest.mock import patch, MagicMock
from src.main import ingest_namespace

@patch("src.main.DocumentProcessor")
@patch("src.main.PineconeClient")
@patch("src.main.FirestoreClient")
@patch("src.main.settings")
@patch("src.main.logger")
def test_ingest_namespace_basic_flow(mock_logger, mock_settings, mock_firestore, mock_pinecone, mock_processor):
    # Arrange
    mock_settings.firestore.batch_size = 2
    mock_settings.pinecone.batch_size = 2

    mock_firestore_instance = MagicMock()
    mock_pinecone_instance = MagicMock()
    mock_processor_instance = MagicMock()

    # Return a list of documents
    mock_firestore_instance.get_documents_for_vectorization.side_effect = [
        [
            {"id": "doc1", "content": "sample text"},
            {"id": "doc2", "content": "another text"},
        ],
        []  # stop after one loop
    ]

    # Simulate vectorization output
    mock_processor_instance.process_documents.return_value = {
        "doc1": [
            {"id": "vec1", "values": [0.1] * 384, "metadata": {"firestoreId": "doc1"}}
        ],
        "doc2": [
            {"id": "vec2", "values": [0.2] * 384, "metadata": {"firestoreId": "doc2"}}
        ],
    }

    mock_firestore_instance.bulk_update_vector_info.return_value = {"updated": 2}
    mock_pinecone_instance.store_embeddings.return_value = {"upserted": 2}

    # Patch the clients
    mock_firestore.return_value = mock_firestore_instance
    mock_pinecone.return_value = mock_pinecone_instance
    mock_processor.return_value = mock_processor_instance

    # Act
    result = ingest_namespace("test-ns", "test-collection", only_new=True)

    # Assert
    assert result == {
        "collection": "test-collection",
        "processed": 2,
        "total": 2
    }
    mock_firestore_instance.get_documents_for_vectorization.assert_called()
    mock_processor_instance.process_documents.assert_called()
    mock_pinecone_instance.store_embeddings.assert_called()
    mock_firestore_instance.bulk_update_vector_info.assert_called()
