import pytest
from unittest.mock import patch, MagicMock
from src.main import search_similar


@patch("src.main.logger")
@patch("src.main.DocumentProcessor")
@patch("src.main.PineconeClient")
def test_search_similar_success(mock_pinecone, mock_processor, mock_logger):
    # --- Setup Embedding ---
    mock_embed = MagicMock()
    mock_embed.generate_embedding.return_value = [0.1, 0.2, 0.3]
    mock_processor.return_value.embedding_client = mock_embed

    # --- Setup Pinecone result ---
    mock_match = MagicMock()
    mock_match.id = "doc1"
    mock_match.score = 0.95
    mock_match.metadata = {"category": "post"}

    mock_pinecone.return_value.query_similar.return_value.matches = [mock_match]

    # --- Run function ---
    result = search_similar("find me something", "posts", top_k=1)

    # --- Assert result ---
    assert result["query"] == "find me something"
    assert result["type"] == "posts"
    assert isinstance(result["results"], list)
    assert result["results"][0]["id"] == "doc1"
    assert result["results"][0]["score"] == 0.95
    assert result["results"][0]["metadata"] == {"category": "post"}

    # --- Assert internal calls ---
    mock_embed.generate_embedding.assert_called_once_with("find me something")
    mock_pinecone.return_value.query_similar.assert_called_once()


@patch("src.main.logger")
@patch("src.main.DocumentProcessor")
@patch("src.main.PineconeClient")
def test_search_similar_failure(mock_pinecone, mock_processor, mock_logger):
    # Simulate embedding generation failure
    mock_processor.return_value.embedding_client.generate_embedding.side_effect = Exception("Embedding failed")

    with pytest.raises(Exception, match="Embedding failed"):
        search_similar("fail this", "posts")
    
    mock_logger.error.assert_called_once()
