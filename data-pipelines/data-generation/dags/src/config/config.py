import os
from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings(BaseSettings):
    """Configuration settings loaded from environment variables."""
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    DB_NAME: str = os.getenv("DB_NAME")
    GOOGLE_APPLICATION_CREDENTIALS:str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    AIRFLOW_UID:int = os.getenv("AIRFLOW_UID")
    MAX_OPEN_AI_REQUEST_PER_MIN: int = os.getenv("MAX_OPEN_AI_REQUEST_PER_MIN")
    MAX_OPEN_AI_REQUEST_PER_DAY: int = os.getenv("MAX_OPEN_AI_REQUEST_PER_DAY")
    OPEN_ROUTER_BASE_URL: str = os.getenv("OPEN_ROUTER_BASE_URL")
    SMTP_SERVER:str = os.getenv("SMTP_SERVER")
    SMTP_STARTTLS:bool = os.getenv("SMTP_STARTTLS")
    SMTP_USER:str = os.getenv("SMTP_USER")
    SMTP_PASSWORD:str = os.getenv("SMTP_PASSWORD")
    SMTP_PORT:int = os.getenv("SMTP_PORT")
    SMTP_EMAIL:str = os.getenv("SMTP_EMAIL")
    SMTP_TIMEOUT:int = os.getenv("SMTP_TIMEOUT")
    SMTP_RETRY_LIMIT:int = os.getenv("SMTP_RETRY_LIMIT")
    SMTP_RECIPIENT_EMAILS:str = os.getenv("SMTP_RECIPIENT_EMAILS")
    AIRFLOW_WWW_USER_USERNAME:str = os.getenv("AIRFLOW_WWW_USER_USERNAME")
    AIRFLOW_WWW_USER_PASSWORD:str = os.getenv("AIRFLOW_WWW_USER_PASSWORD")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    # class Config():
    #     env_file = ".env"
    #     case_sensitive = True
        

settings = Settings()
_all_ = ["settings"]