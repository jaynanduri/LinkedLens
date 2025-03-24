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

## LLM and API Used
We utilize the OpenRouter API via the LangChain OpenAI package to generate text-based content. The responses are validated using Pydantic to maintain structure and consistency.

- Model used: LLaMA- **meta-llama/llama-3.3-70b-instruct:free**

OpenRouter Models: https://openrouter.ai/models