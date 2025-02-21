import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()  # Load .env variables

        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.DB_NAME = os.getenv("DB_NAME")
        self.DB_CREDENTIALS_PATH = os.getenv("DB_CREDENTIALS_PATH")
        self.MAX_OPEN_AI_REQUEST_PER_MIN = 20
        self.MAX_OPEN_AI_REQUEST_PER_DAY = 200
        
# Create a single config instance
config = Config()