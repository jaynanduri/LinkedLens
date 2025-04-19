## Data Generation and Processing Pipelines

### 1. Data Preprocessing

- Handling Missing Values: Rows are removed if any of the mandatory columns (`description`, `title`, `company_name`, `company_id`, `job_id`) contain NaN values.
- Basic Text Cleaning: Remove leading and trailing whitespaces.
- Removing Duplicates
- Filter for Tech Industry
- Stores the cleaned and filtered dataset in a GCP bucket for downstream processing.

### 2. Data Generation

- The data used by the RAG model is synthetically generated in this pipeline
- The pipeline generates recruiter profiles, and then uses these profiles to generate recruiter posts about job openings.
- Additionally, the pipeline also generates user posts about interview experiences that can also be retrieved and summarized based on the company they interviewed with.
- The generated user posts and processed job posts are both pushed to the FireStoreDB after Pydantic validation.

## DAG Overview
| Step                           | DAG Step | Description                                                                                             |
| ----------------------------------- | -------- |--------------------------------------------------------------------------------------------------- |
| **Preprocess_Data**              | check_file_exists, branch_on_file_existence, run_preprocessing | Reads raw data from GCS, performs data cleaning (handling missing values, stripping text, removing duplicates, and filtering for the tech industry), and writes the cleaned data back to GCS.  |
| **Recruiter_Generator**      | load_jobs, create_recruiter_posts | Generates recruiter profiles using LLMs and validates them with Pydantic. `User` and `UserList` |
| **Recruiter_Post_Generator** | create_recruiter_posts | Creates recruiter job posts using the preprocessed job dataset as input. `Post`                 |
| **User_Post_Generator**      | create_interview_exp_posts | Generates interview experience posts based on job postings (company name and title).  `Post`    |
| **Job_Post_Loader**          | create_interview_exp_posts | Loads validated job data into Firestore DB. `JobPosting`                                        |

![Data Generation and Processing Pipeline](/images/DAG_generation.png)
