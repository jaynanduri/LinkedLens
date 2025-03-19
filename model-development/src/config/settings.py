import os

from typing import Dict, List, Optional
from config import constants
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv(override=True)


class PineconeSettings(BaseModel):
    """Pinecone configuration settings."""
    
    api_key: str = Field(default_factory=lambda: os.getenv("PINECONE_API_KEY", ""))
    environment: str = constants.PINECONE_REGION
    cloud: str = constants.PINECONE_CLOUD
    region : str = constants.PINECONE_REGION
    index_name: str = constants.PINECONE_INDEX_NAME
    namespace_collection: Dict[str, str] = constants.PINECONE_NAMESPACE_COLLECTION
    metadata_fields: Dict[str, List[str]] = constants.PINECONE_METADATA_FIELDS


class FirestoreSettings(BaseModel):
    """Firestore configuration settings."""
    collections: List[str] = constants.FIRESTORE_COLLECTIONS
    # credentials_path: str = Field(default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    database_id: Optional[str] = Field(default_factory=lambda: os.getenv("DB_NAME"))

class PromptSettings(BaseModel):
    project_id: str = Field(default_factory=lambda: os.getenv("GOOGLE_PROJECT_ID"))
    prompt_mapping: Dict[str, str] = Field(default_factory=lambda: {
        "query_analysis_prompt": os.getenv("PROMPT_ID_QUERY_ANALYZER"),
        "final_system_prompt": os.getenv("PROMPT_ID_FINAL_RESPONSE")
    })


class EmbeddingSettings(BaseModel):
    """Embedding configuration settings."""
    model_name: str = constants.EMBEDDING_MODEL_NAME
    huggingface_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("HF_TOKEN"))

class Settings(BaseModel):
    pinecone: PineconeSettings = PineconeSettings()
    firestore: FirestoreSettings = FirestoreSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    prompt_setting: PromptSettings = PromptSettings()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    GEMINI_MODEL_NAME: str = constants.GEMINI_MODEL_NAME

settings = Settings()