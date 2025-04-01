import pandas as pd
import pyarrow.parquet as pq
import os
import re
import kagglehub
from typing import List, Dict, Any, Tuple
import logging
from tqdm.auto import tqdm
import re
import numpy as np
from datetime import datetime, timedelta

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)



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

CSV_FILE_EXTENSION = '.csv'

PARQUET_FILE_EXTENSION = '.parquet'

KAGGLE_DATASET_PATH = "arshkon/linkedin-job-postings"

"""
Download data - download data and save in respective folders local parquet files
Preprocess - read parquet files from local and preprocess and sacve locally parquet files
Filter - read preprocessed data from local and filter and save locally parquet files
"""


def read_input_file(filepath: str, column_names: List[str]=None, filter: bool=False, num_rows:int=20)->pd.DataFrame:
    """Reads specific column file from given filepath """
    try:

        if filepath.endswith('.parquet'):
            df = pd.read_parquet(filepath, columns=column_names)
            if filter:
                if column_names:
                    df = df.astype(str).apply(lambda x: x.str.strip())
            # Filter data 
            if filter and num_rows > 0:
                df_subset = df.iloc[:num_rows] 
                logger.info(f"Input data to generate data for: {len(df_subset)}")

                return df_subset
            return df
        else: 
            raise ValueError("Unsupported file format: Must be of type Parquet.")

    except Exception as e:
        raise RuntimeError(f"Error reading input file: {e}")


def download_raw_data() -> None:
    # Create Raw data foldr
    os.makedirs(RAW_DATA_FOLDER, exist_ok=True)
    
    path = kagglehub.dataset_download(KAGGLE_DATASET_PATH)
    logger.info(f"Path to dataset files: {path}")  

    for folder, files in FILE_PATHS.items():
        for file in files:
            logger.info(f"Loading {file}..")
            if folder == "postings":
                local_file_path = os.path.join(RAW_DATA_FOLDER, file)
                kaggle_file_path = path +"/"+file.replace(PARQUET_FILE_EXTENSION, CSV_FILE_EXTENSION)
            else:
                local_file_path = os.path.join(RAW_DATA_FOLDER, folder, file)
                kaggle_file_path = path +"/"+folder+"/"+file.replace(PARQUET_FILE_EXTENSION, CSV_FILE_EXTENSION)

            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            df = pd.read_csv(kaggle_file_path)
            print(len(df))
            df.to_parquet(local_file_path, engine="pyarrow")
    logger.info(f"Completed Downloading data from Kaggle")

def extract_deadlines(text: str) -> List[Dict[str, Any]]:
    date_patterns = [
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",  # MM/DD/YY or DD/MM/YY
        r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",  # MM-DD-YY or DD-MM-YY
        r"\b\d{4}/\d{1,2}/\d{1,2}\b",  # YYYY/MM/DD
        r"\b\d{4}-\d{1,2}-\d{1,2}\b",  # YYYY-MM-DD
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}\b",  # Month DD, YYYY
        r"\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b",  # DD Month YYYY
    ]
    # Define deadline-related keywords
    deadline_keywords = [
        "deadline",
        "due date",
        "due by",
        "closes on",
        "closing date",
        "apply by",
        "apply before",
        "apply until",
        "submit by",
        "application deadline",
        "last date",
        "applications close",
    ]

    # Combine patterns into a single regex
    combined_date_pattern = "|".join(date_patterns)
    
    if pd.isna(text):
        return None
    results = []
    # Look for deadline keywords near dates
    for keyword in deadline_keywords:
        keyword_matches = re.finditer(re.escape(keyword), text, re.IGNORECASE)
        for match in keyword_matches:
            start_pos = match.start()
            end_pos = len(text)-1
            context = text[start_pos:end_pos]

            date_matches = re.finditer(combined_date_pattern, context, re.IGNORECASE)
            for date_match in date_matches:
                results.append(
                    {
                        "keyword": keyword,
                        "date": date_match.group(),
                        "context": context.strip(),
                    }
                )

    return results


def filter_deadline(df: pd.DataFrame) -> pd.DataFrame:
    deadline_info = []
    deadline_df = None
    for idx, row in tqdm(df.iterrows()):
        deadlines = extract_deadlines(row["description"])
        if deadlines:
            for d in deadlines:
                deadline_info.append(
                    {
                        "job_id": row["job_id"],
                        "title": row["title"],
                        "keyword": d["keyword"],
                        "date_found": d["date"],
                        "context": d["context"],
                    }
                )

    # Create DataFrame of results
    deadline_df = pd.DataFrame(deadline_info)
    if len(deadline_df) > 0:
        logger.info(f"Found {len(deadline_df)} potential application deadlines")
    else:
        logger.info(f"No application deadlines found in job descriptions")
    return deadline_df


def modify_dates(num_rows: int)-> Tuple[List[Any], List[Any]]:
    listed_time_start = datetime(2025, 2, 1)
    listed_time_end = datetime(2025, 3, 21)
    listed_time_random = []
    expiry_random = []
    for _ in tqdm(range(num_rows)):
        # Random number of seconds between start and end dates
        random_seconds = np.random.randint(
            0, int((listed_time_end - listed_time_start).total_seconds())
        )
        random_date = listed_time_start + timedelta(seconds=random_seconds)
        expiry_date = random_date + timedelta(days=90)
        listed_time_random.append(int(random_date.timestamp()))        
        expiry_random.append(int(expiry_date.timestamp()))

    
    return listed_time_random, expiry_random



def preprocess_postings(input_filepath: str) -> pd.DataFrame:
    logger.info(f"Reading file {input_filepath}")
    df = read_input_file(input_filepath)
    print(f"Len of file: {len(df)}")
    logger.info(f"Preprocessing file {input_filepath}")
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
    df = df.drop(columns=date_columns)

    df['zip_code'] = df['zip_code'].apply(lambda x: str(int(x)).strip() if pd.notna(x) else "")

    # remove jobs with deadline in description = 2153 deadlines found
    deadline_df = filter_deadline(df)
    df = df[~df["job_id"].isin(deadline_df["job_id"])]

    # Modify Dates
    listed_time_random, expiry_random = modify_dates(len(df))
    df['createdAt'] = listed_time_random
    df['updatedAt'] = df['createdAt']
    df['ttl'] = expiry_random
    df['createdAt'] = df['createdAt'].astype(int)
    df['updatedAt'] = df['updatedAt'].astype(int)
    df['ttl'] = df['ttl'].astype(int)
    logger.info(f"Len after modifying dates: {len(df)}")
    return df

def preprocess_files(input_filepath: str) -> pd.DataFrame:
    logger.info(f"Reading file from {input_filepath}")
    df = read_input_file(input_filepath)
    print(f"Len of file: {len(df)}")
    logger.info(f"Preprocessing file {input_filepath}")
    subset_cols = None
    if 'companies' in input_filepath:
        subset_cols = ['company_id']
    elif 'jobs' in input_filepath:
        subset_cols = ['job_id']
    elif 'mappings/industries' in input_filepath:
        subset_cols = ['industry_id']
    else:
        subset_cols = None
    
    df = df.dropna(subset=subset_cols)
    return df

def preprocess_raw_data() -> None:
    # Make dir for preprocessed
    os.makedirs(PREPROCESSED_DATA_FOLDER, exist_ok=True)
    for folder , files in FILE_PATHS.items():
        for file in files:
            logger.info(f"Preprocessing file {file}..")
            if folder == "postings":
                df = preprocess_postings(os.path.join(RAW_DATA_FOLDER, file))
                local_file_path = os.path.join(PREPROCESSED_DATA_FOLDER, file)
            else:
                df = preprocess_files(os.path.join(RAW_DATA_FOLDER, folder, file))
                local_file_path = os.path.join(PREPROCESSED_DATA_FOLDER, folder, file)

            
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            df.to_parquet(local_file_path, engine="pyarrow")
    logger.info(f"Completed preprocessing for all files")
        

def filter_postings(input_filepath: str) -> pd.DataFrame:
    logger.info(f"Reading file from {input_filepath}")
    df = read_input_file(input_filepath)
    logger.info(f"Filtering file {input_filepath}..")
    # print(f"test data types : \n {df.dtypes}")
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
    # print(f"Check Datatypes after filtering: \n {result_df.dtypes}")
    return result_df

def filter_preprocessed_data() -> None:
    os.makedirs(FILTERED_DATA_FOLDER, exist_ok=True)
    for folder , files in FILE_PATHS.items():
        for file in files:
            logger.info(f"Filtering file {file}..")
            if folder == "postings":
                df = filter_postings(os.path.join(PREPROCESSED_DATA_FOLDER, file))
                local_file_path = os.path.join(FILTERED_DATA_FOLDER, file)
            else:
                df = read_input_file(os.path.join(PREPROCESSED_DATA_FOLDER, folder, file))
                local_file_path = os.path.join(FILTERED_DATA_FOLDER, folder, file)

            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            df.to_parquet(local_file_path, engine="pyarrow")
    logger.info(f"Completed filtering for all files")


def data_preprocessing() -> None:
    try:
        logger.info("Downloading raw data from Kaggle...")
        download_raw_data()
        logger.info("Preprocessing data...")
        preprocess_raw_data()
        logger.info("Filtering data for Tech jobs...")
        filter_preprocessed_data()
        logger.info(f"Preprocessing Completed!")
    except RuntimeError as e:
        logger.error(f"Data Processing Step failed with RunTimeError: \n {e}")


if __name__ == "__main__":
    logger.info("Creating data folder")
    os.makedirs(DATA_FOLDER, exist_ok=True)
    data_preprocessing()