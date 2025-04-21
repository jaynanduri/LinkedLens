import os
from dotenv import load_dotenv
from pydantic import BaseModel
from google.cloud import logging as gcloud_logging
from google.oauth2 import service_account
from google.cloud.logging.handlers import CloudLoggingHandler
import logging

load_dotenv(override=True)

class Config(BaseModel):
    POST_EVAL_LOG_NAME: str = "linkedlens_post_eval_test"
    PRE_EVAL_LOG_NAME: str = "linkedlens_pre_eval_test"
    LANGSMITH_API_KEY:str = os.getenv("LANGSMITH_API_KEY")
    HF_TOKEN: str = os.getenv("HF_TOKEN")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT")
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT")
    LANGSMITH_TRACING: str = os.getenv("LANGSMITH_TRACING")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    GEMINI_MODEL_NAME: str = "gemini-2.0-flash-001"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    PROD_RUN_ENV:str="prod"
    TEST_RUN_ENV:str="test"
    PROJECT_ID: str = os.getenv("GOOGLE_PROJECT_ID")
    LOG_LEVEL:str=os.getenv("LOG_LEVEL", "INFO")

config = Config()



def get_logger(name:str ="linkedlens_post_eval"):
    # Initialize Google Cloud Logging client
    gcp_client = gcloud_logging.Client(project=config.PROJECT_ID)
    gcp_handler = CloudLoggingHandler(gcp_client, name=name)

    logger = logging.getLogger(name)
    logger.setLevel(config.LOG_LEVEL)

    # clear handlers to avoid duplicate logs
    logger.handlers.clear()

    logger.addHandler(gcp_handler)
    
    return logger

logger = get_logger(config.POST_EVAL_LOG_NAME)

def set_logger(name:str = "linkedlens_pre_eval"):
    """
    Set up the logger with Google Cloud Logging and stdout logging.
    
    Args:
        name (str): The name of the logger.
    """
    global logger
    logger = get_logger(name=name)

