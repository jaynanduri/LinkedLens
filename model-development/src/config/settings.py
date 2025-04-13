import os

from typing import Dict, List, Optional, Tuple, Any
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
    namesapce_threshold: Dict[str, float] = constants.PINECONE_NAMESPACE_THRESHOLD
    max_docs: int = constants.PINECONE_MAX_DOCS



class PromptSettings(BaseModel):
    project_id: str = Field(default_factory=lambda: os.getenv("GOOGLE_PROJECT_ID"))
    prompt_mapping: Dict[str, Tuple[str, str]] = Field(default_factory=lambda: {
        "query_analysis_prompt": (os.getenv("PROMPT_ID_QUERY_ANALYZER"), os.getenv("PROMPT_VERSION_QUERY_ANALYZER")),
        "final_system_prompt": (os.getenv("PROMPT_ID_FINAL_RESPONSE"), os.getenv("PROMPT_VERSION_FINAL_RESPONSE")),
    })


class FireStoreSettings(BaseModel):
    database_name: str = os.getenv("DB_NAME")
    test_data: Dict[str, Any] = constants.FIRESTORE_TEST_DATA

class RagasSettings(BaseModel):
    RAGAS_SIMPLE_QUERIES: float = constants.RAGAS_SIMPLE_QUERIES
    RAGAS_MULTI_HOP_DIRECT: float = constants.RAGAS_MULTI_HOP_DIRECT
    RAGAS_MULTI_HOP_COMPLEX: float = constants.RAGAS_MULTI_HOP_COMPLEX

class EmbeddingSettings(BaseModel):
    """Embedding configuration settings."""
    model_name: str = constants.EMBEDDING_MODEL_NAME
    huggingface_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("HF_TOKEN"))
    dimension: int = constants.EMBEDDING_DIMENSION

class Settings(BaseModel):
    pinecone: PineconeSettings = PineconeSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    prompt_setting: PromptSettings = PromptSettings()
    ragas_settings: RagasSettings = RagasSettings()
    firestore_setting: FireStoreSettings = FireStoreSettings()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    # GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    GEMINI_MODEL_NAME: str = constants.GEMINI_MODEL_NAME
    GEMINI_EMBEDDING_MODEL: str = constants.GEMINI_EMBEDDING_MODEL
    LOG_NAME: str = constants.LOG_NAME
    PRE_EVAL_LOG_NAME: str = constants.PRE_EVAL_LOG_NAME
    POST_EVAL_LOG_NAME: str = constants.POST_EVAL_LOG_NAME
    TEST_LOG_NAME: str = constants.TEST_LOG_NAME
    NAMESPACE_URLS: Dict[str, str] = constants.NAMESPACE_URLS
    LANGSMITH_API_KEY:str = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT")
    PROD_RUN_ENV:str=constants.PROD_RUN_ENV
    TEST_RUN_ENV:str=constants.TEST_RUN_ENV
    TEST_METRIC_THRESHOLD: Dict[str, float] = constants.TEST_METRIC_THRESHOLD
    LOG_LEVEL:str=os.getenv("LOG_LEVEL", "INFO")
    # LANGSMITH_PROJECT_NAME_TEST: str = "linkedlens-test"
    # LANGSMITH_DATASET_NAME_PROD: str = "LinkedLens"
    # LANGSMITH_DATASET_NAME_TEST: str = "LinkedLensTest"
    # LANGSMITH_EXPERIMENT_PREFIX_PROD: str = "prod_eval"
    # LANGSMITH_EXPERIMENT_PREFIX_TEST: str = "test_eval"

settings = Settings()