import pytest
from unittest.mock import patch, MagicMock
from src.main import test_connections


@patch("src.main.test_firestore")
@patch("src.main.test_pinecone")
@patch("src.main.test_embedding")
@patch("src.main.logger")
def test_all_connections_success(mock_logger, mock_embedding, mock_pinecone, mock_firestore):
    # Arrange: Set all services to return 'successful' status
    mock_firestore.return_value = {"connected": True}
    mock_pinecone.return_value = {"connected": True}
    mock_embedding.return_value = {"success": True}

    # Act
    test_connections()

    # Assert
    mock_logger.info.assert_any_call("\nAll connections successful! ✅")


@patch("src.main.test_firestore")
@patch("src.main.test_pinecone")
@patch("src.main.test_embedding")
@patch("src.main.logger")
def test_some_connections_fail(mock_logger, mock_embedding, mock_pinecone, mock_firestore):
    # Arrange: Simulate Firestore failure
    mock_firestore.return_value = {"connected": False}
    mock_pinecone.return_value = {"connected": True}
    mock_embedding.return_value = {"success": True}

    # Act
    test_connections()

    # Assert
    mock_logger.error.assert_called_with("\nSome connections failed. See logs for details. ❌")
