from src.logger import logger
from src.utils.gen_helper import get_docs_list_by_field, connect_to_db, read_input_file
from src.schema.job_posting import JobPosting, JobPostingList
from pydantic import ValidationError
import json


def load_jobs(bucket_file_path: str, batch_size: int) -> int:
    """
    Loads job postings from a DataFrame into the database after validating them.
    Uses bulk validation/insertion when possible.
    """
    try:
        df = read_input_file(bucket_file_path, None, True, 5)
        logger.info(f"Total Len of Input DB read: {len(df)}")
        db_client = connect_to_db()
        docs_job = db_client.get_all_docs('jobs')
        job_ids = get_docs_list_by_field(docs_job, 'job_id')

        valid_count = 0 # total validated and inserted records
        records = df.to_dict(orient="records")
        batch_num = 0
        for i in range(0, len(records), batch_size):
            batch_num += 1
            batch = records[i: i + batch_size]
            batch = [row for row in batch if row['job_id'] not in job_ids]
            if not batch:
                logger.info(f"All jobs in batch {batch_num} already loaded to DB.")
                continue

            try:
                logger.info(f"Loading {len(batch)} records from the batch {batch_num}")
                job_postings_batch = JobPostingList(jobs=batch)
                bulk_data = [json.loads(job.model_dump_json()) for job in job_postings_batch.jobs]
                logger.info(f"Validated jobs in  batch {batch_num}")

                db_client.bulk_insert('jobs', bulk_data, 'job_id')
                valid_count += len(bulk_data)
            except ValidationError as batch_err:
                for row in batch:
                    try:
                        job_posting = JobPosting(**row)
                        logger.info(f"Validated single job from batch {batch_num}")
                        job_data = json.loads(job_posting.model_dump_json())
                        db_client.insert_entry('jobs', job_data, job_data['job_id'])
                        valid_count += 1
                    except ValidationError as row_err:
                        logger.error(f"Validation error for job_id {row.get('job_id')}: {row_err}")
        logger.info(f"Total records inserted: {valid_count}")
        return valid_count

    except RuntimeError as e:
        logger.error(f"Loading Jobs process failed with RunTimeError: {e}")
        raise
