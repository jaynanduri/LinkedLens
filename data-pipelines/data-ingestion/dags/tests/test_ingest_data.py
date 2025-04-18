import pytest
from unittest.mock import patch, MagicMock
from src.main import ingest_data
from src.config.settings import settings


@patch("src.main.logger")
@patch("src.main.ingest_all_namespaces")
@patch("src.main.PineconeClient")
def test_ingest_data_success(mock_pinecone, mock_ingest_all, mock_logger):
    # Simulate Pinecone index exists
    mock_pinecone.return_value.get_index.return_value = "test-index"

    # Simulate successful ingestion
    mock_ingest_all.return_value = [
        {"collection": "posts", "processed": 50},
        {"collection": "users", "processed": 30},
    ]

    # Run
    ingest_data(only_new=True)

    # Assert
    mock_pinecone.return_value.get_index.assert_called_once()
    mock_ingest_all.assert_called_once_with(True)
    mock_logger.info.assert_any_call("All collections sync completed", extra={"results": mock_ingest_all.return_value})


@patch("src.main.logger")
@patch("src.main.PineconeClient")
def test_ingest_data_index_missing(mock_pinecone, mock_logger):
    # Simulate index missing
    mock_pinecone.return_value.get_index.side_effect = ValueError("Index not found")

    with pytest.raises(ValueError):
        ingest_data()

    mock_logger.error.assert_called_once_with(
        f"Pinecone index '{settings.pinecone.index_name}' does not exist."
    )


@patch("src.main.logger")
@patch("src.main.ingest_all_namespaces", side_effect=Exception("Ingestion failure"))
@patch("src.main.PineconeClient")
def test_ingest_data_ingestion_failure(mock_pinecone, mock_ingest_all, mock_logger):
    # Simulate Pinecone index exists
    mock_pinecone.return_value.get_index.return_value = "test-index"

    with pytest.raises(Exception, match="Ingestion failure"):
        ingest_data()

    mock_logger.error.assert_called_with("Failed to sync data to vector store: Ingestion failure")
