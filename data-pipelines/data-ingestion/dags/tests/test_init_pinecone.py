import pytest
from unittest.mock import patch, MagicMock
from src.main import init_pinecone


@patch("src.main.PineconeClient")
@patch("src.main.logger")
def test_init_pinecone_index_exists(mock_logger, mock_pinecone_client_class):
    # Arrange
    mock_client = MagicMock()
    mock_pinecone_client_class.return_value = mock_client

    mock_client.get_index.return_value = "existing_index"
    mock_client.get_stats.return_value = {
        "totalVectorCount": 123,
        "namespaces": {"test-ns": {}}
    }

    # Act
    result = init_pinecone()

    # Assert
    assert result["status"] == "exists"
    assert "stats" in result
    mock_client.get_index.assert_called_once()
    mock_client.get_stats.assert_called_once()
    mock_logger.info.assert_any_call("Pinecone initialization completed", extra=result)


@patch("src.main.PineconeClient")
@patch("src.main.settings")
@patch("src.main.logger")
def test_init_pinecone_create_index(mock_logger, mock_settings, mock_pinecone_client_class):
    # Arrange
    mock_client = MagicMock()
    mock_pinecone_client_class.return_value = mock_client

    mock_client.get_index.side_effect = ValueError("Index not found")

    mock_settings.pinecone.index_name = "test-index"
    mock_settings.pinecone.dimension = 128
    mock_settings.pinecone.cloud = "aws"
    mock_settings.pinecone.region = "us-east"

    # Act
    result = init_pinecone()

    # Assert
    assert result["status"] == "created"
    assert result["indexName"] == "test-index"
    mock_client.create_index.assert_called_once_with(
        index_name="test-index",
        dimension=128,
        serverless=True,
        cloud="aws",
        region="us-east",
    )
    mock_logger.info.assert_any_call("Pinecone index 'test-index' created successfully")
