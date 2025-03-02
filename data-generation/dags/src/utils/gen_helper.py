from src.logger import logger
from google.cloud import storage
from io import BytesIO
import pyarrow.parquet as pq
from src.utils.db import FirestoreClient
from src.utils.rate_limit import RateLimiter
from src.config.config import settings
from typing import List
from src.utils.prompts import PROMTPS
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from src.schema.user_list import UserList
from src.schema.user import BasicUser
from src.llm.llm_client import get_open_router_llm
import pandas as pd
from io import StringIO

def read_input_file(filepath: str, column_names: List[str], filter=False):
    """Reads specific column file from GCP bucket(filepath) """
    try:
        client = storage.Client.from_service_account_json(settings.DB_CREDENTIALS_PATH)
        
        bucket_name = filepath.split("/")[0]
        object_name = "/".join(filepath.split("/")[1:])

        bucket = client.bucket(bucket_name)
        # object_name = 'job_postings/tech_postings.praquet'
        blob = bucket.blob(object_name)
        if not blob.exists():
            raise FileNotFoundError(f"File '{object_name}' not found in bucket '{bucket_name}'.")

        file_data = blob.download_as_bytes()

        if object_name.endswith('.parquet'):
            table = pq.read_table(BytesIO(file_data), columns=column_names)
            df = table.to_pandas()
            if filter:
                if column_names:
                    df = df.astype(str).apply(lambda x: x.str.strip())
                # Filter data 
                df_subset = df.iloc[:60] 
                logger.info(f"Input data to generate data for: {len(df_subset)}")

                return df_subset
            return df
        elif object_name.endswith(".csv"):
            df = pd.read_csv(BytesIO(file_data), usecols=column_names)
            return df
        else: 
            raise ValueError("Unsupported file format: Must be CSV or Parquet.")

    except Exception as e:
        raise RuntimeError(f"Error reading input file: {e}")
    


def connect_to_db():
    """Establishes and returns a connection to the Firestore database."""
    try:
        db_client = FirestoreClient()
        return db_client
    except Exception as e:
        raise RuntimeError(f"Error connecting to DB: {e}")
    


def get_request_limiter():
    """Creates and returns a RateLimiter object for managing API request limits.""" 
    try:
        request_limiter = RateLimiter(settings.MAX_OPEN_AI_REQUEST_PER_MIN, settings.MAX_OPEN_AI_REQUEST_PER_DAY)
        return request_limiter
    except Exception as e:
        raise RuntimeError(f"Error creating request limiter: {e}")
    

def get_docs_list_by_field(docs, field_name):
    field_list = set()
    for doc in docs:
        doc_dict = doc.to_dict()
        field_list.add(doc_dict[field_name])
    return field_list


def get_llm_chain(chain_type):
    """Creates and returns an LLM processing chain and response format instructions."""
    try:
        if chain_type == 'user-recruiter-generation':
            messages = [
                ("system", PROMTPS[chain_type])
            ]
            prompt = ChatPromptTemplate.from_messages(messages)

            parser = PydanticOutputParser(pydantic_object=UserList)
            format_instructions = parser.get_format_instructions()
            logger.info(f"\nFormat Instructions:\n {format_instructions}")
            llm = get_open_router_llm(chain_type)
            chain = prompt | llm | parser

            return chain, format_instructions
        elif chain_type == 'recruiter-post':
            llm = get_open_router_llm(chain_type)
            logger.info(f"\nLLM for posts: \n {llm}")
            post_template = PromptTemplate.from_template(PROMTPS[chain_type])
            chain = post_template | llm
            return chain
        elif chain_type == 'user-post-generation':
            llm = get_open_router_llm(chain_type)
            logger.info(f"\nLLM for posts: \n {llm}")
            post_template = PromptTemplate.from_template(PROMTPS[chain_type])
            chain = post_template | llm
            return chain
        elif chain_type == 'basic-user-details':
            llm = get_open_router_llm(chain_type)
            user_template = PromptTemplate.from_template(PROMTPS[chain_type])
            parser = PydanticOutputParser(pydantic_object=BasicUser)
            user_chain = user_template | llm | parser
            format_instructions = parser.get_format_instructions()
            logger.info(f"\nFormat Instructions:\n {format_instructions}")
            return user_chain, format_instructions
        else:
            raise ValueError(f"The given chain name {chain_type} not found.")

    except Exception as e:
        logger.error(f"Error creating chain: {e}")
        raise Exception(f"Error creating chain: {e}")
    


def upload_file_to_gcs(data, bucket_path):
    try:
        # csv_buffer = StringIO()
        # data.to_csv(csv_buffer, index=False)
        # csv_buffer.seek(0)
        client = storage.Client.from_service_account_json(settings.DB_CREDENTIALS_PATH)
        
        bucket_name = bucket_path.split("/")[0]
        object_name = "/".join(bucket_path.split("/")[1:])
        print(f"Output bucket name: {bucket_name}")
        print(f"Object path: {object_name}")
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        print(f"Created blob for {object_name}")


        buffer = BytesIO()
        data.to_parquet(buffer, engine="pyarrow")
        blob.upload_from_string(buffer.getvalue(), content_type="application/octet-stream")

        # blob.upload_from_string(data, content_type="text/csv")
        print(f"File uploaded to gs://{bucket_name}/{object_name}")
    except Exception as e:
        logger.error(f"Failed to upload data to bucket: {e}")