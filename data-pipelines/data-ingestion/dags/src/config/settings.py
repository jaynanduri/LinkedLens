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
    cloud: str = 'aws'
    region : str = 'us-east-1'
    index_name: str = "linked-lens-index"
    batch_size: int = 200
    dimension: int = 384  # Dimension for 'all-MiniLM-L6-v2' model
    # collections: Dict[str, str] = {
    #     "users": "user",
    #     "jobs": "job",
    #     "posts": "post",
    # }
    namespace_collection: Dict[str, str] = {
        "user": "users",
        "user_post" : "posts",
        "recruiter_post": "posts",
        "job": "jobs"
    }
    namespace_collection: Dict[str, str] = {
        "user": "users",
        "user_post" : "posts",
        "recruiter_post": "posts",
        "job": "jobs"
    }
    metadata_fields: Dict[str, List[str]] = {
        # firestoreId, createdAt, updatedAt included by default for all 
        "job": ["title", "company_name", "location", "ttl"],
        "user_post": ["author", "ttl"],
        "user" : ["company", "account_type"],
        "recruiter_post": ["author", "job_id", "ttl"],
    }


class FirestoreSettings(BaseModel):
    """Firestore configuration settings."""
    
    collections: List[str] = ["users", "jobs", "posts"]
    credentials_path: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    database_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("DB_NAME")
    )
    batch_size: int = 500  # Maximum documents to process in one batch


class EmbeddingSettings(BaseModel):
    """Embedding configuration settings."""
    
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    huggingface_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("HUGGINGFACE_API_KEY")
    )


class ProcessingSettings(BaseModel):
    """Processing configuration settings."""
    
    max_concurrent: int = 5  # Maximum concurrent embedding requests
    # index_name: str = 'linkedlens-index'
    update_strategy: str = "changed-fields-only"  # 'all', 'changed-fields-only'
    relevant_fields: Dict[str, List[str]] = {
        "job": ["title", "company_name", "author", "listed_time", "expiry"],
        "post": ["timestamp", "author", "job_id","ttl"],
        "user" : ["company", "username", "first_name", "last_name"]
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
    SMTP_SERVER: str = os.getenv("SMTP_SERVER")
    SMTP_STARTTLS: bool = os.getenv("SMTP_STARTTLS")
    SMTP_USER: str = os.getenv("SMTP_USER")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
    SMTP_PORT: int = os.getenv("SMTP_PORT")
    SMTP_EMAIL: str = os.getenv("SMTP_EMAIL")
    SMTP_TIMEOUT: int = os.getenv("SMTP_TIMEOUT")
    SMTP_RETRY_LIMIT: int = os.getenv("SMTP_RETRY_LIMIT")
    SMTP_RECIPIENT_EMAILS: str = os.getenv("SMTP_RECIPIENT_EMAILS")    
    AIRFLOW_WWW_USER_USERNAME:str = os.getenv("AIRFLOW_WWW_USER_USERNAME")
    AIRFLOW_WWW_USER_PASSWORD:str = os.getenv("AIRFLOW_WWW_USER_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")
    # DB_CREDENTIALS_PATH:str = os.getenv("DB_CREDENTIALS_PATH")
    AIRFLOW_UID:int = os.getenv("AIRFLOW_UID")


# Create settings instance
settings = Settings()
_all_ = ["settings"]