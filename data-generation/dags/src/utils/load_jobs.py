from src.logger import logger
from src.utils.gen_helper import get_docs_list_by_field, connect_to_db
from src.schema.job_posting import JobPosting
import json

def load_jobs(input_df):
    """Loads job postings from a DataFrame into the database after validation."""
    # get current job ids from DB
    db_client = connect_to_db()
    docs_job = db_client.get_all_docs('jobs')
    job_ids = get_docs_list_by_field(docs_job, 'job_id')

    for row in input_df.to_dict(orient="records"):
        logger.info(f"Loading job_id: {row['job_id']}")
        if row['job_id'] not in job_ids:
            logger.info("Validate row")
            job_posting = JobPosting(**row)
            logger.info("Created job posting object")
            job_data = json.loads(job_posting.model_dump_json())
            job_data['vectorized'] = False
            db_client.insert_entry('jobs', job_data, job_data['job_id'])
            logger.info(f"Inserted job data to DB for job id : {job_data['job_id']}")


