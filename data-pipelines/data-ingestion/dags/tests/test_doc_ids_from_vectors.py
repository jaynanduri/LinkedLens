import pytest
from src.main import get_doc_ids_from_vectors

def test_get_doc_ids_from_vectors_returns_unique_ids():
    # Arrange
    vector_list = [
        {"metadata": {"firestoreId": "id1"}},
        {"metadata": {"firestoreId": "id2"}},
        {"metadata": {"firestoreId": "id1"}},  # Duplicate
        {"metadata": {"firestoreId": "id3"}},
    ]

    # Act
    result = get_doc_ids_from_vectors(vector_list)

    # Assert
    assert set(result) == {"id1", "id2", "id3"}


def test_get_doc_ids_from_vectors_handles_missing_keys():
    # Arrange
    vector_list = [
        {"metadata": {"notId": "x"}},
        {"metadata": {}},
        {"metadata": {"firestoreId": "id1"}},
    ]

    # Act
    result = get_doc_ids_from_vectors(vector_list)

    # Assert
    assert result == ["id1"]
