import pandas as pd
import pyarrow.parquet as pq  
from google.cloud import storage
from io import BytesIO
from src.utils.gen_helper import read_input_file, upload_file_to_gcs
import os
from src.logger import logger

# This can be loaded from env or directly passed in Airflow DAG
DB_CREDENTIALS_PATH = os.getenv("DB_CREDENTIALS_PATH", "/opt/airflow/gcp_credentials.json")

def read_file_from_gcs(filepath: str, column_names=None) -> pd.DataFrame:
    """
    Reads data from GCP bucket into a DataFrame.
    filepath should be of the format: bucket_name/object_name
    """

    client = storage.Client.from_service_account_json(DB_CREDENTIALS_PATH)
    
    bucket_name, object_name = filepath.split("/", 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    if not blob.exists():
        raise FileNotFoundError(f"File '{object_name}' not found in bucket '{bucket_name}'.")

    file_data = blob.download_as_bytes()

    # Detect file format and read appropriately (CSV vs Parquet)
    if object_name.endswith(".parquet"):
        table = pq.read_table(BytesIO(file_data), columns=column_names)
        df = table.to_pandas()
    elif object_name.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_data), usecols=column_names)
    else:
        raise ValueError("Unsupported file format: Must be CSV or Parquet.")

    return df

# ------------------- Step 1: Load Data -------------------

def load_all_data(input_bucket_path, file_type):
    """Loads all required datasets from GCS bucket."""
    postings = read_input_file(input_bucket_path+'/postings'+file_type, None)
    companies = read_input_file(input_bucket_path+'/companies'+file_type, None)
    benefits = read_input_file(input_bucket_path+'/benefits'+file_type, None)
    employee_counts = read_input_file(input_bucket_path+'/employee_counts'+file_type, None)
    return postings, companies, benefits, employee_counts

# ------------------- Step 2: Preprocess company_id -------------------

def clean_company_ids(postings_df, companies_df):
    """Ensure company_id is consistent across postings and companies."""
    postings_df["company_id"] = postings_df["company_id"].apply(lambda x: str(int(float(x))) if pd.notna(x) else x)
    companies_df["company_id"] = companies_df["company_id"].apply(lambda x: str(int(float(x))) if pd.notna(x) else x)

    postings_df["company_id"] = postings_df["company_id"].astype(str)
    companies_df["company_id"] = companies_df["company_id"].astype(str)

    return postings_df, companies_df

# ------------------- Step 3: Clean and enrich postings -------------------

def enrich_and_clean_postings(postings_df, companies_df):
    """Add company names to postings and handle missing values."""
    company_name_mapping = companies_df.set_index("company_id")["name"].to_dict()
    postings_df["company_name"] = postings_df["company_id"].map(company_name_mapping)
    postings_df["company_name"].fillna("", inplace=True)

    postings_df.dropna(subset=["company_name", "title", "location"], inplace=True)

    return postings_df

# ------------------- Master Function (Combine All) -------------------

def load_and_clean_data(input_bucket_path, output_bucket_path):
    """
    Complete process: Load from GCS -> Clean -> Save.
    """

    # Step 1: Load all
    postings_df, companies_df, benefits_df, employee_counts_df = load_all_data(input_bucket_path, '.csv')
    logger.info("Loaded all raw data")
    # Step 2: Clean company_ids
    postings_df, companies_df = clean_company_ids(postings_df, companies_df)
    logger.info("Clean Company ids")
    # Step 3: Clean and enrich postings
    postings_df = enrich_and_clean_postings(postings_df, companies_df)
    logger.info("Enriched posts")

    # Deduplication across all
    postings_df.drop_duplicates(inplace=True)
    companies_df.drop_duplicates(inplace=True)
    benefits_df.drop_duplicates(inplace=True)
    employee_counts_df.drop_duplicates(inplace=True)
    logger.info(f"Dropped duplicates: {len(postings_df)}")
    # Save cleaned files to GCP
    upload_file_to_gcs(postings_df, output_bucket_path+'/postings.parquet')
    upload_file_to_gcs(companies_df, output_bucket_path+'/companies.parquet')
    upload_file_to_gcs(benefits_df, output_bucket_path+'/benefits.parquet')
    upload_file_to_gcs(employee_counts_df, output_bucket_path+'/employee_counts.parquet')


    logger.info(f" All cleaned files saved to {output_bucket_path}")
    
    return


def filter_technology_industry(input_bucket_path, output_bucket_path):

    postings_df, companies_df, benefits_df, employee_counts_df = load_all_data(input_bucket_path, '.parquet')

    postings_df['company_name'] = postings_df['company_name'].str.lower().str.strip()
    companies_df['name'] = companies_df['name'].str.lower().str.strip()

    combined_df = postings_df.merge(companies_df, on="company_id", suffixes=('_postings', '_companies'), how="left")
    logger.info(f"Merges companies and postings")

    tech_keywords = [
        'tech', 'technology', 'software', 'ai', 'cloud', 'data', 'it', 'systems', 'digital',
        'analytics', 'robotics', 'cyber', 'computing', 'network', 'engineering', 'electronics',
        'semiconductor', 'programming', 'developer', 'internet', 'solutions'
    ]

    tech_mask = combined_df['company_name'].str.contains('|'.join(tech_keywords), na=False) | \
                combined_df['name'].str.contains('|'.join(tech_keywords), na=False) | \
                combined_df['title'].str.contains('|'.join(tech_keywords), na=False)
    
    tech_companies_df = combined_df[tech_mask]
    tech_company_ids = tech_companies_df['company_id'].unique()

    tech_postings_df = postings_df[postings_df['company_id'].isin(tech_company_ids)]
    tech_benefits_df = benefits_df[benefits_df['job_id'].isin(tech_postings_df['job_id'])]
    tech_employee_counts_df = employee_counts_df[employee_counts_df['company_id'].isin(tech_company_ids)]

    logger.info(f"Number of records: {len(tech_postings_df)}")

    upload_file_to_gcs(tech_postings_df, output_bucket_path+'/tech_postings.parquet')
    upload_file_to_gcs(tech_companies_df, output_bucket_path+'/companies.parquet')
    upload_file_to_gcs(tech_benefits_df, output_bucket_path+'/benefits.parquet')
    upload_file_to_gcs(tech_employee_counts_df, output_bucket_path+'/employee_counts.parquet')

    logger.info(f"Uploaded to GCS filtered files.")