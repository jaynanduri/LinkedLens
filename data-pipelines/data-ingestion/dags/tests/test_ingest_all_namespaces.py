import pytest
from unittest.mock import patch, MagicMock
from src.main import ingest_all_namespaces


@patch("src.main.ingest_namespace")
@patch("src.main.settings")
@patch("src.main.logger")
def test_ingest_all_namespaces_success(mock_logger, mock_settings, mock_ingest_namespace):
    # Arrange
    mock_settings.pinecone.namespace_collection = {
        "ns1": "collection1",
        "ns2": "collection2"
    }

    mock_ingest_namespace.side_effect = [
        {"collection": "collection1", "processed": 2, "total": 2},
        {"collection": "collection2", "processed": 3, "total": 3},
    ]

    # Act
    result = ingest_all_namespaces(only_new=True)

    # Assert
    assert len(result) == 2
    assert result[0]["collection"] == "collection1"
    assert result[1]["processed"] == 3
    mock_ingest_namespace.assert_any_call("ns1", "collection1", True)
    mock_ingest_namespace.assert_any_call("ns2", "collection2", True)


@patch("src.main.ingest_namespace")
@patch("src.main.settings")
@patch("src.main.logger")
def test_ingest_all_namespaces_with_errors(mock_logger, mock_settings, mock_ingest_namespace):
    # Arrange
    mock_settings.pinecone.namespace_collection = {
        "ns1": "collection1",
        "ns2": "collection2"
    }

    mock_ingest_namespace.side_effect = [
        {"collection": "collection1", "processed": 2, "total": 2},
        Exception("Failed to process collection2")
    ]

    # Act
    result = ingest_all_namespaces(only_new=False)

    # Assert
    assert len(result) == 2
    assert result[0]["collection"] == "collection1"
    assert result[1]["collection"] == "collection2"
    assert "error" in result[1]
    assert result[1]["processed"] == 0
