# Data Preprocessing, Generation, and Ingestion Pipelines

We process a [Kaggle dataset](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) containing job postings, preprocess the data, and store it in a GCP bucket. Using this preprocessed data, we generate synthetic user profiles, recruiter job posts, and interview experience posts using LLM APIs. The generated data is validated using Pydantic before loading it into Firestore DB. The data stored in the FirestoreDB then makes use of the Data loading pipeline to ingest/sync the data into the Vector DB.

There are two main DAGs:
1. [Data Generation and Processing Pipeline](/data-pipelines/data-generation/)
2. [Data Ingestion](/data-pipelines/data-generation/)

## Data Preprocessing

This pipeline fetches job posting and company data from Kaggle, performs preprocessing, and prepares the data for analysis of tech job postings.

### 1. Data Acquisition

- Fetch company and job posting data from Kaggle
- Load multiple related datasets:
  - Company industries
  - Company specialities
  - Employee counts

### 2. Data Preprocessing

- Drop unused columns to reduce dataset size
- Convert columns to appropriate data types
- Clean text fields (descriptions, titles)
- Merge related datasets to create comprehensive view
- Remove entries with null values in critical fields (job_title, job_description)

### 3. Data Analysis

- Perform exploratory data analysis (EDA) on:
  - Company information
  - Industry distribution
  - Job posting characteristics
- Create visualizations of top industries and job titles

### 4. Tech Job Filtering

- Filter job postings to focus on tech-related positions
- Create a specialized dataset for tech industry analysis
- Save processed data to Parquet format for efficient storage and retrieval

## Data Bias Detection Using Data Slicing

Since the dataset from Kaggle is not representative of the entire job market, we need to be aware of potential biases in the data. Below are some interesting slices of the data that can help us understand the biases:

![top-30-job-titles.png](/images/top-30-job-titles.png)
The dataset is skewed towards software engineering roles, with the top job titles being related to software development.

![top-40-companies.png](/images/top-40-companies.png)
The dataset contains job postings from a variety of companies, with the top companies being well-known tech giants, however usual suspects like Apple, Meta/Facebook are missing. The distribution of companies is definitely not representative of the entire job market.

![top-industries.png](/images/top-industries.png)
The industries are definitely dominated by tech companies, with the top industries being related to technology and software development.

## Logging and Failure Tracking
- Logs are generated at each step and for all functions.
- The logs are currently collected using the in-built Airflow logger
- Errors are captured and logged for easy debugging and resolution.
- Any errors during the pipeline runs result in a failed run, and appropriate notifications are sent to alert about the status.

## Alerting

All DAGs send an email notification updating the status. The email notifications are sent for both failed/successful runs of the data pipelines. An example of the email notification is attached below.

![Notification Email Example](/images/image_10.png)

## Folder Structure

- The data preprocessing pipeline and data generation pipeline follow a similar structure as follows:
  ```
    data-generation/
      |- dags/                 #Contains DAG Definitions for data preprocessing and generation
          |- src/
              |- config/       #`config.py` Manages environment variables
              |- experiments/  #`test.ipynb` - Testing LLM prompts
              |- llm/
              |- schema/       #Contains all Pydantic validation schemas
              |- utils/        #Helper functions for data processing 
          |- tests/
          |- __init__.py
          |- logger.py
          |- main.py
      |- airflow.cfg
      |- docker-compose.yml    # For Airflow container
      |- README.md
  ```

## Deployment and Installation

The DAGs are deployed to run on a Cloud VM using Google Compute Engine. The Airflow instance can be run using the `docker-compose.yml` files provided in the respective folders for the DAGs using the following commands:

```
docker-compose up airflow-init
docker-compose up
```
Once the docker container is running, navigate to `https:\\localhost:8080` to access Airflow using the login credentials provided in the docker-compose file.

Follow these [steps](/docs/GCE-Setup.md) before running the DAGs to ensure the required infrastructure is in place.

## LLM and API Used
We utilize the OpenRouter API via the LangChain OpenAI package to generate text-based content. The responses are validated using Pydantic to maintain structure and consistency.

- Model used: LLaMA- **meta-llama/llama-3.3-70b-instruct:free**

OpenRouter Models: https://openrouter.ai/models

## Testing and Validation

### Pydantic Validation

All Pydantic validation classes are stored in the `schema/` directory. These classes ensure data integrity before inserting records into Firestore DB.
Validation ensures:
  - Correct data types.
  - Required fields are present.
  - Structured output for LLM-generated content.


### Data Preprocessing & Validation
1. Type Conversion & Cleaning: Ensuring numeric/string company IDs are standardized, NaN handling, and dtype consistency.
2. Schema Enforcement: Validation of JobPosting Pydantic models with edge cases like epoch timestamp handling.
3. Data Integrity: Testing dataframe operations (merges, drops, enrichment) in enrich_and_clean_postings to ensure valid titles, locations, and company mappings.
4. Company-User Mapping: Verifying correct user allocation ratios with create_company_user_map.
5. ID Generation Workflows: Testing UUID generation, rate limiting, and uniqueness checks for user/post creation.
6. External Service Simulation: Mocking LLM chains (e.g., DummyPostChain, DummyUserChain) to validate structured JSON outputs without real API calls.
7. Rate Limiter Behavior: Simulating allowed/blocked states to test conditional logic in data generation pipelines.
8. Deterministic UUIDs: Using patched UUIDs to verify ID assignment and relational integrity between users and posts.
9. Empty/missing data, invalid types, and schema violations (e.g., testing ValidationError for malformed job postings).
10. Stress-testing functions with mixed data types, zero values, and unexpected NaN propagation.

Test suite combines pandas-based assertions, Pydantic model validation, and unittest.mock to isolate components, ensuring reliability across data pipelines, model hydration, and synthetic data generation workflows.

The results of a test run for all the files in data-generation/dags/src/

![alt text](/images/test-cases.png)
