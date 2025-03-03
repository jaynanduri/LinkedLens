"""
Document processing for the LinkedLens Vector Integration.
"""

import time
from typing import Any, Dict, List, Optional, Union

from config.settings import settings
from src.clients.embedding_client import EmbeddingClient
from src.utils.logger import logger


class DocumentProcessor:
    """Processor for transforming and vectorizing documents."""
    
    def __init__(self):
        """Initialize the document processor."""
        self.embedding_client = EmbeddingClient()
    
    def process_document(
        self,
        document: Dict[str, Any],
        doc_type: str,
        doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document for vectorization.
        
        Args:
            document: Document to process.
            doc_type: Document type (user, job, post).
            doc_id: Document ID (optional).
            
        Returns:
            Processed document with embedding.
            
        Raises:
            Exception: If processing fails.
        """
        try:
            # Extract text for embedding
            text_to_embed = self.extract_text_for_embedding(document, doc_type)
            
            # Generate embedding
            doc_id = doc_id or document.get("id")
            logger.debug(f"Generating embedding for {doc_type}{' (ID: ' + doc_id + ')' if doc_id else ''}")
            embedding = self.embedding_client.generate_embedding(text_to_embed)
            
            # Extract metadata
            metadata_fields = settings.pinecone.metadata_fields.get(doc_type, [])
            metadata = self.extract_metadata(document, doc_type, metadata_fields)
            
            # Return processed document
            return {
                "id": doc_id,
                "type": doc_type,
                "embedding": embedding,
                "metadata": metadata,
                "original": document
            }
        except Exception as e:
            logger.error(
                f"Error processing {doc_type} document: {str(e)}",
                extra={"id": doc_id or document.get("id")}
            )
            raise
    
    def extract_text_for_embedding(self, document: Dict[str, Any], doc_type: str) -> str:
        """
        Extract text for embedding from a document.
        
        Args:
            document: Document to extract text from.
            doc_type: Document type.
            
        Returns:
            Text for embedding.
        """
        if doc_type == "user":
            # Extract user profile text
            name = document.get("name", "")
            headline = document.get("headline", "")
            bio = document.get("bio", "")
            skills = " ".join(document.get("skills", [])) if isinstance(document.get("skills"), list) else ""
            experience = document.get("experience", "")
            
            return f"{name} {headline} {bio} {skills} {experience}"
        
        elif doc_type == "job":
            # Extract job posting text
            title = document.get("title", "")
            company = document.get("company", "")
            description = document.get("description", "")
            requirements = document.get("requirements", "")
            skills = " ".join(document.get("skills", [])) if isinstance(document.get("skills"), list) else ""
            
            return f"{title} {company} {description} {requirements} {skills}"
        
        elif doc_type == "post":
            # Extract post text
            title = document.get("title", "")
            content = document.get("content", "")
            tags = " ".join(document.get("tags", [])) if isinstance(document.get("tags"), list) else ""
            
            return f"{title} {content} {tags}"
        
        else:
            # Default: stringify the document
            logger.warning(f"Unknown document type: {doc_type}, using stringified document")
            return str(document)
    
    def extract_metadata(
        self,
        document: Dict[str, Any],
        doc_type: str,
        fields: List[str]
    ) -> Dict[str, Any]:
        """
        Extract metadata from a document.
        
        Args:
            document: Document to extract metadata from.
            doc_type: Document type.
            fields: Fields to extract.
            
        Returns:
            Metadata dictionary.
        """
        metadata = {
            "type": doc_type,
            "docType": doc_type  # Include type in metadata for filtering
        }
        
        # Add document creation time
        if "createdAt" in document:
            try:
                # Convert to ISO string if possible
                if hasattr(document["createdAt"], "isoformat"):
                    metadata["createdAt"] = document["createdAt"].isoformat()
                else:
                    metadata["createdAt"] = str(document["createdAt"])
            except Exception:
                logger.debug(f"Could not parse createdAt for {doc_type} document")
        
        # Extract specified fields
        for field in fields:
            if field in document and document[field] is not None:
                value = document[field]
                
                # Handle arrays (like skills)
                if isinstance(value, list):
                    # Only include first few items to stay within metadata size limits
                    metadata[field] = value[:10]
                
                # Handle objects by converting to string
                elif isinstance(value, dict):
                    try:
                        str_value = str(value)
                        metadata[field] = str_value[:500]  # Limit string length
                    except Exception:
                        metadata[field] = str(value)[:500]
                
                # Handle primitives
                else:
                    metadata[field] = str(value)[:500] if isinstance(value, str) else value
        
        return metadata
    
    def process_documents(
        self,
        documents: List[Dict[str, Any]],
        doc_type: str
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents in batch.
        
        Args:
            documents: Documents to process.
            doc_type: Document type.
            
        Returns:
            Array of processed documents with embeddings.
            
        Raises:
            Exception: If batch processing fails.
        """
        try:
            logger.info(f"Processing {len(documents)} {doc_type} documents in batch")
            
            # Process documents in smaller batches to manage memory
            batch_size = 10
            results = []
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                
                # First, extract text for each document
                texts = [self.extract_text_for_embedding(doc, doc_type) for doc in batch]
                
                # Generate embeddings in batch
                embeddings = self.embedding_client.generate_embeddings(texts)
                
                # Process each document with its embedding
                for j, (doc, embedding) in enumerate(zip(batch, embeddings)):
                    doc_id = doc.get("id")
                    metadata_fields = settings.pinecone.metadata_fields.get(doc_type, [])
                    metadata = self.extract_metadata(doc, doc_type, metadata_fields)
                    
                    results.append({
                        "id": doc_id,
                        "type": doc_type,
                        "embedding": embedding,
                        "metadata": metadata,
                        "original": doc
                    })
                
                logger.debug(
                    f"Processed batch {(i // batch_size) + 1} of {(len(documents) + batch_size - 1) // batch_size}"
                )
            
            logger.info(f"Successfully processed {len(results)} {doc_type} documents")
            return results
        except Exception as e:
            logger.error(
                f"Error batch processing {doc_type} documents: {str(e)}",
                extra={"count": len(documents)}
            )
            raise
    
    def check_for_relevant_changes(
        self,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        relevant_fields: List[str]
    ) -> bool:
        """
        Check if any relevant fields have changed.
        
        Args:
            old_data: Old document data.
            new_data: New document data.
            relevant_fields: List of fields to check.
            
        Returns:
            True if any relevant fields changed.
        """
        for field in relevant_fields:
            old_value = old_data.get(field)
            new_value = new_data.get(field)
            
            # Handle arrays specially (e.g. skills)
            if isinstance(old_value, list) and isinstance(new_value, list):
                if len(old_value) != len(new_value):
                    return True
                
                # Check if any values are different
                for i, val in enumerate(old_value):
                    if i >= len(new_value) or val != new_value[i]:
                        return True
                        
                continue
            
            # Handle dictionaries
            if isinstance(old_value, dict) and isinstance(new_value, dict):
                if str(old_value) != str(new_value):
                    return True
                continue
            
            # Simple value comparison
            if old_value != new_value:
                return True
                
        return False