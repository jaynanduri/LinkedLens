import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuration settings loaded from environment variables."""
    OPENAI_API_KEY: str
    DB_NAME: str
    DB_CREDENTIALS_PATH:str
    AIRFLOW_UID:int
    MAX_OPEN_AI_REQUEST_PER_MIN: int
    MAX_OPEN_AI_REQUEST_PER_DAY: int
    OPEN_ROUTER_BASE_URL: str
    SMTP_SERVER:str
    SMTP_STARTTLS:bool
    SMTP_USER:str
    SMTP_PASSWORD:str
    SMTP_PORT:int
    SMTP_EMAIL:str
    SMTP_TIMEOUT:int
    SMTP_RETRY_LIMIT:int
    SMTP_RECIPIENT_EMAILS:str

    class Config():
        env_file = ".env"
        case_sensitive = True
        

settings = Settings()
_all_ = ["settings"]