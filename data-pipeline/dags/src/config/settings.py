"""
Configuration settings for the LinkedLens Vector Integration.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class PineconeSettings(BaseModel):
    """Pinecone configuration settings."""
    
    api_key: str = Field(default_factory=lambda: os.getenv("PINECONE_API_KEY", ""))
    environment: str = Field(default_factory=lambda: os.getenv("PINECONE_ENVIRONMENT", ""))
    index_name: str = "linkedlens-index"
    dimension: int = 384  # Dimension for 'all-MiniLM-L6-v2' model
    collections: Dict[str, str] = {
        "users": "user",
        "jobs": "job",
        "posts": "post",
    }
    metadata_fields: Dict[str, List[str]] = {
        "user": ["name", "headline", "skills", "location", "company"],
        "job": ["title", "company", "location", "skills", "remote", "salary"],
        "post": ["title", "tags", "author", "type"],
    }


class FirestoreSettings(BaseModel):
    """Firestore configuration settings."""
    
    collections: List[str] = ["users", "jobs", "posts"]
    credentials_path: str = Field(
        default_factory=lambda: os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS", 
            str(BASE_DIR / "config" / "db-credentials.json")
        )
    )
    database_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("DB_NAME")
    )
    batch_size: int = 500  # Maximum documents to process in one batch


class EmbeddingSettings(BaseModel):
    """Embedding configuration settings."""
    
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_input_length: int = 8000
    use_cache: bool = True
    huggingface_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("HUGGINGFACE_API_KEY")
    )


class ProcessingSettings(BaseModel):
    """Processing configuration settings."""
    
    max_concurrent: int = 5  # Maximum concurrent embedding requests
    update_strategy: str = "changed-fields-only"  # 'all', 'changed-fields-only'
    relevant_fields: Dict[str, List[str]] = {
        "users": ["name", "headline", "bio", "skills", "experience"],
        "jobs": ["title", "description", "requirements", "skills"],
        "posts": ["title", "content", "tags"],
    }


class LoggingSettings(BaseModel):
    """Logging configuration settings."""
    
    level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format: str = "{time} | {level} | {message}"
    file_path: Optional[str] = str(BASE_DIR / "logs" / "vector-integration.log")


class Settings(BaseModel):
    """Main configuration settings."""
    
    pinecone: PineconeSettings = PineconeSettings()
    firestore: FirestoreSettings = FirestoreSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    processing: ProcessingSettings = ProcessingSettings()
    logging: LoggingSettings = LoggingSettings()
    SMTP_SERVER: str = os.getenv("SMTP_SERVER")
    SMTP_STARTTLS: bool = os.getenv("SMTP_STARTTLS")
    SMTP_USER: str = os.getenv("SMTP_USER")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
    SMTP_PORT: int = os.getenv("SMTP_PORT")
    SMTP_EMAIL: str = os.getenv("SMTP_EMAIL")
    SMTP_TIMEOUT: int = os.getenv("SMTP_TIMEOUT")
    SMTP_RETRY_LIMIT: int = os.getenv("SMTP_RETRY_LIMIT")
    SMTP_RECIPIENT_EMAILS: str = os.getenv("SMTP_RECIPIENT_EMAILS")    


# Create settings instance
settings = Settings()
_all_ = ["settings"]