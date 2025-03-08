import pandas as pd
from src.utils.gen_helper import read_input_file, upload_file_to_gcs
import os
import re
import kagglehub
from src.logger import logger

"""
Actions: Start on run preprocessing - pass bucket name, folders for raw, processed, filtered
1. Download Kaggle data - 
2. preprocess (postings csv) - upload everything to bucket all other files drop na 
3. preprocess all other files
4. filter posting and upload everything to filtered
"""

FILE_PATHS = [
        '/postings',
        '/mappings/industries',
        '/mappings/skills',
        '/jobs/benefits',
        '/jobs/job_industries',
        '/jobs/job_skills',   
        '/jobs/salaries',
        '/companies/companies',
        '/companies/company_industries',
        '/companies/company_specialities',
        '/companies/employee_counts',
    ]
CSV_FILE_EXTENSION = '.csv'

PARQUET_FILE_EXTENSION = '.parquet'


def download_raw_data(bucket_path: str) -> None:
    path = kagglehub.dataset_download("arshkon/linkedin-job-postings")
    logger.info(f"Path to dataset files: {path}")  
    
    for file_path in FILE_PATHS:
        logger.info(f"Loading {file_path+CSV_FILE_EXTENSION}.. ")
        df = pd.read_csv(path+file_path+CSV_FILE_EXTENSION)
        logger.info(f"Uploading {file_path}.. ")
        bucket_file_path = bucket_path + file_path + PARQUET_FILE_EXTENSION
        upload_file_to_gcs(df, bucket_file_path)
    logger.info(f"Completed Downloading data from Kaggle")


def preprocess_postings(bucket_file_path: str) -> pd.DataFrame:
    logger.info(f"Reading file {bucket_file_path} from GCS")
    df = read_input_file(bucket_file_path, None)
    print(f"Len of file: {len(df)}")
    logger.info(f"Preprocessing file {bucket_file_path}")
    df = df.dropna(subset=['job_id', 'company_name', 'title', 'description'])
    str_columns = ['job_id', 'company_name', 'title', 'description', 'company_id',
               'pay_period', 'location', 'formatted_work_type', 'job_posting_url',
               'application_url', 'application_type', 'formatted_experience_level',
               'skills_desc', 'posting_domain', 'work_type', 'currency', 'compensation_type']
    df['company_id'] = df['company_id'].astype(int)
    df[str_columns] = df[str_columns].astype(str).apply(lambda x: x.str.strip())

    float_columns = ['max_salary', 'med_salary', 'min_salary', 'normalized_salary']
    df[float_columns] = df[float_columns]

    df['applies'] = df['applies'].fillna(0).astype(int)
    df['views'] = df['views'].fillna(0).astype(int)

    df['remote_allowed'] = df['remote_allowed'].fillna(0).astype(bool)
    df['sponsored'] = df['sponsored'].fillna(0).astype(bool)

    date_columns = ['closed_time', 'listed_time', 'expiry', 'original_listed_time']
    df[date_columns] = df[date_columns].apply(lambda x: pd.to_datetime(x, unit='ms', errors='coerce'))
    df[date_columns] = df[date_columns].apply(lambda x: x.dt.strftime("%Y-%m-%d %H:%M:%S"))
    df['zip_code'] = df['zip_code'].apply(lambda x: str(int(x)).strip() if pd.notna(x) else "")
    print(df[date_columns].head())
    return df

def preprocess_files(bucket_file_path: str) -> pd.DataFrame:
    logger.info(f"Reading file {bucket_file_path} from GCS")
    df = read_input_file(bucket_file_path, None)
    print(f"Len of file: {len(df)}")
    logger.info(f"Preprocessing file {bucket_file_path}")
    subset_cols = None
    if 'companies' in bucket_file_path:
        subset_cols = ['company_id']
    elif 'jobs' in bucket_file_path:
        subset_cols = ['job_id']
    elif 'mappings/industries' in bucket_file_path:
        subset_cols = ['industry_id']
    else:
        subset_cols = None
    
    df = df.dropna(subset=subset_cols)
    return df

def preprocess_raw_data(in_bucket_path: str, out_bucket_path: str) -> None:
    for file_path in FILE_PATHS:
        file_path = file_path+PARQUET_FILE_EXTENSION
        logger.info(f"Preprocessing file {file_path}..")

        if '/postings' in file_path:
            df = preprocess_postings(in_bucket_path+file_path)
        else:
            df = preprocess_files(in_bucket_path+file_path)
        
        logger.info(f"Upload preprocessed file {file_path}")
        bucket_file_path = out_bucket_path + file_path
        upload_file_to_gcs(df, bucket_file_path)
    logger.info(f"Completed preprocessing for all files")
        

def filter_postings(bucket_file_path: str) -> pd.DataFrame:
    logger.info(f"Reading file {bucket_file_path} from GCS")
    df = read_input_file(bucket_file_path, None)
    logger.info(f"Filtering file {bucket_file_path}..")
    print(f"test data types : \n {df.dtypes}")
    title_keywords = ["Developer", "Engineer", "Data", "Analyst", "Data Scientist", "Machine Learning",
    "ML", "Artificial Intelligence", "AI", "Full Stack", "IOS", "Android", "Web", "Systems",
    "Network", "Security", "Cloud", "IT", "Database", "Product", "Technical", "QA", "UX", "UI",
    "UX/UI", "UI/UX", "Site Reliability", "Research Scientist", "Blockchain", "Business Intelligence",
    "BI", "AWS", "GCP", "Snowflake", "Cybersecurity", "Systems", "IT Project Manager", "Robotics Engineer",
    "Solutions Architect", "Technical Writer", "Bioinformatics", "Technician", "Tester", "IAM", "Azure",
    "Analytics", "Technical", "Workday Integration", "DevOps", "DevSecOps", "Programmer", "ETL", ".NET",
    ]
    tech_related_titles = [
        (r'\b' + title + r'\b')
        for title in title_keywords
    ]

    result_df = df[df["title"].apply(lambda x: any(re.search(title, x, re.IGNORECASE) for title in tech_related_titles))]
    print(f"Check Datatypes after filtering: \n {result_df.dtypes}")
    return result_df

def filter_preprocessed_data(in_bucket_path: str,  out_bucket_path: str) -> None:
    for file_path in FILE_PATHS:
        file_path = file_path+PARQUET_FILE_EXTENSION
        logger.info(f"Filtering file {file_path}..")
        if '/postings' in file_path:
            df = filter_postings(in_bucket_path+file_path)
        else:
            df = read_input_file(in_bucket_path+file_path, None)
        
        logger.info(f"Upload filtered file {file_path}")
        bucket_file_path = out_bucket_path + file_path
        upload_file_to_gcs(df, bucket_file_path)


def data_preprocessing(bucket_name: str, raw_data_folder: str, processed_data_folder: str, filtered_data_folder: str) -> None:
    try:
        logger.info("Downloading raw data from Kaggle...")
        download_raw_data(bucket_name+"/"+raw_data_folder)
        logger.info("Preprocessing data...")
        preprocess_raw_data(bucket_name+"/"+raw_data_folder, bucket_name+"/"+processed_data_folder)
        logger.info("Filtering data for Tech jobs...")
        filter_preprocessed_data(bucket_name+"/"+processed_data_folder, bucket_name+"/"+filtered_data_folder)
        logger.info(f"Preprocessing Completed!")
    except RuntimeError as e:
        logger.error(f"Data Processing Step failed with RunTimeError: \n {e}")
