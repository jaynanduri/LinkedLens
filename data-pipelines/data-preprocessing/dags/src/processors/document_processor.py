import time
from typing import Any, Dict, List, Optional, Union

from src.config.settings import settings
from src.clients.embedding_client import EmbeddingClient
from src.utils.logger import logger
from datetime import datetime, timezone
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentProcessor:
    """Processor for transforming and vectorizing documents."""
    
    def __init__(self):
        """Initialize the document processor."""
        self.embedding_client = EmbeddingClient()
        self.MAX_CHUNK_LENGTH = 1024
        self.CHUNK_OVERLAP = 200

    def extract_text_for_embedding(self, document: Dict[str, Any], collection_type: str) -> str:
        """
        Extracts relevant text from a document based on its collection type for embedding.

        Args:
            document (Dict[str, Any]): The document from which text is extracted.
            collection_type (str): The type of collection (e.g., 'users', 'posts', 'jobs').

        Returns:
            str: A string representation of the extracted text, or the entire document 
            stringified if no relevant fields are found.
        """
        logger.info(f"Extracting text for collection {collection_type}")
        if collection_type == 'users':
            # convert name and username as strings
            first_name = document.get('first_name', "")
            last_name = document.get('last_name', "")
            username = document.get('username', "")
            text = ""
            if first_name != "":
                text = text + "Name: " + first_name +" " + last_name
            if username != "":
                text = text + "; Username: "+ username
            if text == "":
                return str(document)
            return text
        
        elif collection_type == 'posts':
            content = document.get('content', "")
            if content == "":
                return str(document)
            return content.strip()
        
        elif collection_type == 'jobs':
            description = document.get('description', "")
            if description == "":
                return str(document)
            return description.strip()
        
        else:
            logger.warning(f"Unknown collection type: {collection_type}, using stringified document")
            return str(document)

    def extract_metadata(self, document: Dict[str, Any], doc_type: str, metadata_fields: List[str])->Dict[str, Any]:
        """
        Extracts and constructs metadata for a given document.

        Args:
            document (Dict[str, Any]): The document from which metadata is extracted.
            doc_type (str): The type of document being processed.
            metadata_fields (List[str]): A list of metadata fields to extract.

        Returns:
            Dict[str, Any]: A dictionary containing the extracted metadata.
        """
        # add default fields + doc-type  and last updated time to metadata
        metadata = {
            'docType': doc_type
        }

        # Add createdAt if not in doc generate and use same for updatedAt
        createdAt = document.get('createdAt', 0)
        updatedAt = document.get('updatedAt', 0)
        current_time = datetime.now(timezone.utc)
        current_timestamp = int(current_time.timestamp())
        if createdAt == 0 or updatedAt == 0:
            # generate value
            createdAt = current_timestamp
            updatedAt = current_timestamp
        
        metadata['createdAt'] = createdAt
        metadata['updatedAt'] = updatedAt
        metadata['firestoreId'] = document['id']

        # add as per doc 
        logger.info(f"Adding metadata fields for doc type : {doc_type}")
        for field in metadata_fields:
            if field == 'ttl' or field == 'listed_time':
                default_value = 0
            else:
                default_value = ""
            field_value = document.get(field, default_value)
            metadata[field] = field_value
        logger.info(f"The metadata for the doc_type: {doc_type} is generated successfully. Metadata : {metadata}")
        return metadata

    def sanitize_text(self, text: Union[str, List, Dict, None]) -> str:
        """
        Sanitize text for embedding.
        
        Args:
            text: Text to sanitize.
            
        Returns:
            Sanitized text.
        """
        if text is None:
            return ""
        
        # Convert to string if not already
        if not isinstance(text, str):
            if isinstance(text, (list, tuple)):
                return " ".join(str(item) for item in text)
            elif isinstance(text, dict):
                return " ".join(f"{k} {v}" for k, v in text.items())
            return str(text)
        
        # Clean and normalize
        return " ".join(text.split())

    def chunk_text(self, text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
        """
        Split text into chunks using LangChain's RecursiveCharacterTextSplitter.

        Args:
            text: The full text to split.
            chunk_size: Maximum size of each chunk.
            chunk_overlap: Overlap between adjacent chunks.

        Returns:
            A list of text chunks.
        """
        if not chunk_size:
            chunk_size = self.MAX_CHUNK_LENGTH
        if not chunk_overlap:
            chunk_overlap = self.CHUNK_OVERLAP
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return splitter.split_text(text)


    def process_document(self, document: Dict[str, Any], doc_type: str, collection_type: str, metadata_fields: List[str]) -> List[Dict[str, Any]]:
        """
        Processes a single document by extracting data, chunking it, and embedding it.

        This function takes a document, extracts relevant data, splits it into smaller 
        chunks, generates embeddings for each chunk, and returns a list of vectors.

        Args:
            document (Dict[str, Any]): The document to be processed.
            doc_type (str): The type of document being processed.
            collection_type (str): The collection the document belongs to.
            metadata_fields (List[str]): A list of metadata fields to extract.

        Returns:
            List[Dict[str, Any]]: A list of vectors representing the document's embedded chunks.
        """
        logger.info(f"Processing doc id: {document['id']}; Doc Type : {doc_type}; Collection: {collection_type}")
        id = document['id']
        doc_text = self.extract_text_for_embedding(document, collection_type)
        sanitized_text = self.sanitize_text(doc_text)
        metadata = self.extract_metadata(document, doc_type, metadata_fields)
        chunks = self.chunk_text(sanitized_text)
        logger.info(f"Number of chunks for the document {len(chunks)}")
        if not chunks:
            chunks = [sanitized_text]
        logger.info(f"Generating vectors for each chunk")
        # For each chunk prep vector 
        embedding_client = EmbeddingClient()
        doc_vector_list = []
        for i, chunk in enumerate(chunks):
            vector_id = id if len(chunks) == 1 else f"{id}_chunk_{i+1}"
            embedding = embedding_client.generate_embedding(chunk)
            vector_record = {
                "id": vector_id,
                "values": embedding,
                "metadata": {**metadata, "chunk": i+1, "total_chunks": len(chunks), 
                             "raw_data": chunk, "lastUpdated": int(datetime.now(timezone.utc).timestamp())}
            }
            doc_vector_list.append(vector_record)
        logger.info(f"Generated vectors for doc ID: {id}, doc_type: {doc_type}, Number of vectors: {len(doc_vector_list)}")
        return doc_vector_list

    def extract_batch_data(self, batch: List[Dict[str, Any]], 
                           doc_type: str, 
                           collection_type: str, 
                           metadata_fields: List[str]) -> Dict[str, Any]:
        """
        Processes a batch of documents by extracting data, chunking, and embedding them.

        This function iterates over a batch of documents, processes each document to 
        generate embeddings, and stores the resulting vectors in a dictionary.

        Args:
            batch (List[Dict[str, Any]]): A list of documents to be processed.
            doc_type (str): The type of documents being processed.
            collection_type (str): The collection the documents belong to.
            metadata_fields (List[str]): A list of metadata fields to extract.

        Returns:
            Dict[str, Any]: A dictionary mapping document IDs to their corresponding 
            processed vector lists.

        Raises:
            Exception: If no documents are successfully processed.
        """
        processed_docs = {}
        for doc in batch:
            doc_vector_list = self.process_document(doc, doc_type, collection_type, metadata_fields)
            processed_docs[doc['id']] = doc_vector_list
        if not processed_docs:
            logger.warning(f"No documents processed for the batch")
            if len(batch) > 0:
                raise
        return processed_docs

    def process_documents(
            self,
            documents: List[Dict[str, Any]],
            doc_type: str,
            collection_type: str
        ) -> Dict[str, Any]:
        """
        Process multiple documents in batch.
        
        Args:
            documents: Documents to process.
            doc_type: Document type.
            collection_type: Collection name in Firestore
            
        Returns:
            List of vectors grouped by doc id.
            
        Raises:
            Exception: If batch processing fails.
        """
        try:
            logger.info(f"Processing {len(documents)} {doc_type} documents in batch")
            batch_size = 10
            doc_vectors_grp = {}
            metadata_fields = settings.pinecone.metadata_fields[doc_type]
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                logger.info(f"Processing batch {i+1} : Batch Size: {len(batch)}")
                processed_batch = self.extract_batch_data(batch, doc_type, collection_type, metadata_fields)
                logger.info(f"Processed docs for batch {i+1}. Processed docs vector length {len(processed_batch)}")
                doc_vectors_grp.update(processed_batch)
            return doc_vectors_grp

        except Exception as e:
            logger.error(
                f"Error batch processing {doc_type} documents: {str(e)}",
                extra={"count": len(documents)}
            )
            raise


# Modify as needed    
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