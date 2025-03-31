import shutil
import os
import pandas as pd
from google.cloud import storage
from io import BytesIO
from dotenv import load_dotenv
import logging

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)


load_dotenv(override=True)
GOOGLE_CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
RAW_DATA_FOLDER_NAME = "raw_data"
PREPROCESSED_DATA_FOLDER_NAME  = "preprocessed_data"
FILTERED_DATA_FOLDER_NAME = "filtered_data"

DATA_FOLDER = os.path.join(os.getcwd(), 'data')
RAW_DATA_FOLDER = os.path.join(DATA_FOLDER, RAW_DATA_FOLDER_NAME)
PREPROCESSED_DATA_FOLDER = os.path.join(DATA_FOLDER, PREPROCESSED_DATA_FOLDER_NAME)
FILTERED_DATA_FOLDER = os.path.join(DATA_FOLDER, FILTERED_DATA_FOLDER_NAME)

FILE_PATHS = {
    "postings": ["postings.parquet"],
    "mappings": ["industries.parquet", "skills.parquet"],
    "jobs": ["benefits.parquet", "job_industries.parquet", "job_skills.parquet", "salaries.parquet"],
    "companies": ["companies.parquet", "company_industries.parquet", "company_specialities.parquet", "employee_counts.parquet"]
}

GCP_BUCKET_PATH = "linkedlens_data/"

def upload_file_to_gcs(data: pd.DataFrame, bucket_path: str)-> None:
    """Uploads data to the specified bucket path in GCS """
    try:
        client = storage.Client.from_service_account_json(GOOGLE_CREDENTIALS_PATH)
        print(client)
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
        buffer.seek(0)

        logger.info(f"File uploaded to gs://{bucket_name}/{object_name}")
    except Exception as e:
        logger.error(f"Failed to upload data to bucket: {e}")

def upload_folder_to_gcp(data_folder_name:str, data_folder_path:str, loaded_all:bool)-> bool:
    for folder, files in FILE_PATHS.items():
        for file in files:
            if folder == "postings":
                local_file_path = os.path.join(data_folder_path, file)
                gcp_file_path = GCP_BUCKET_PATH+data_folder_name+"/"+file
            else:
                local_file_path = os.path.join(data_folder_path, folder, file)
                gcp_file_path = GCP_BUCKET_PATH+data_folder_name+"/"+folder+"/"+file

            if os.path.exists(local_file_path):
                df = pd.read_parquet(local_file_path, engine="pyarrow")
                logger.info(f"Loaded Parquet file: {local_file_path}")
                upload_file_to_gcs(df, gcp_file_path)
                logger.info(f"Uploaded file to GCP: {gcp_file_path}")
            else:
                logger.warning(f"File not found, skipping load: {local_file_path}")
                loaded_all = False
    return loaded_all


def upload_to_gcp():
    loaded_all = True
    logger.info(f"Load Raw Data to GCP")
    loaded_all = upload_folder_to_gcp(RAW_DATA_FOLDER_NAME, RAW_DATA_FOLDER, loaded_all)
    logger.info(f"Load Preprocessed Data to GCP")   
    loaded_all = upload_folder_to_gcp(PREPROCESSED_DATA_FOLDER_NAME, PREPROCESSED_DATA_FOLDER, loaded_all)
    logger.info(f"Load Filtered Data to GCP")
    loaded_all = upload_folder_to_gcp(FILTERED_DATA_FOLDER_NAME, FILTERED_DATA_FOLDER, loaded_all)
    logger.info(f"Completed loading data to GCP: {loaded_all}")
    # Delete Data folder from local
    if loaded_all:
        if os.path.exists(DATA_FOLDER):
            try:
                shutil.rmtree(DATA_FOLDER)
                logger.info(f"Successfully deleted folder: {DATA_FOLDER}")
            except Exception as e:
                logger.error(f"Failed to delete {DATA_FOLDER}: {e}")


if __name__ == "__main__":
    upload_to_gcp()
