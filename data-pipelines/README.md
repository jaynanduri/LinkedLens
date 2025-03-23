# Data Preprocessing and Generation Pipeline

### Overview 
We process a [Kaggle dataset](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) containing job postings, preprocess the data, and store it in a GCP bucket. Using this preprocessed data, we generate synthetic user profiles, recruiter job posts, and interview experience posts using LLM APIs. The generated data is validated using Pydantic before loading it into Firestore DB.

To get an overview of our data exploratory analysis and data bias, refer [link](data-pipeline/)

### 1. Data Preprocessing Pipeline

- Handling Missing Values: Rows are removed if any of the mandatory columns (`description`, `title`, `company_name`, `company_id`, `job_id`) contain NaN values.
- Basic Text Cleaning: Remove leading and trailing whitespaces.
- Removing Duplicates
- Filter for Tech Industry
- Stores the cleaned and filtered dataset in a GCP bucket for downstream processing.

#### DAG Overview
| DAG Name                            | Description                                                                                             |
| ----------------------------------- | --------------------------------------------------------------------------------------------------- |
| **Preprocess_Data**              | Reads raw data from GCS, performs data cleaning (handling missing values, stripping text, removing duplicates, and filtering for the tech industry), and writes the cleaned data back to GCS.  |


#### DAG Execution Flow

![alt text](/images/image_9.png)

![alt text](/images/image_8.png)

### 2. Data Generation and Loading Pipeline

#### DAGS Overview
| DAG Name                     | Description                                                                                     |
| ---------------------------- | ----------------------------------------------------------------------------------------------- |
| **Recruiter_Generator**      | Generates recruiter profiles using LLMs and validates them with Pydantic. `User` and `UserList` |
| **Recruiter_Post_Generator** | Creates recruiter job posts using the preprocessed job dataset as input. `Post`                 |
| **User_Post_Generator**      | Generates interview experience posts based on job postings (company name and title).  `Post`    |
| **Job_Post_Loader**          | Loads validated job data into Firestore DB. `JobPosting`                                        |



#### DAG Execution Flow

- Recruiter_generator

![alt text](/images/image-1.png)

![alt text](/images/image-2.png)

The duration of the `user_recruiter_generation` step varies based on the number of users being created.

- Recruiter_Post_Generator:

![alt text](/images/image-3.png)

![alt text](/images/image-4.png)

The duration of the `create_hiring_posts` step varies based on the number of users being created.

- User_Post_Generator

![alt text](/images/image-5.png)

![alt text](/images/image-6.png)

The duration of the `create_user_posts` step varies based on the number of users being created.

- Job_Post_Loader

![alt text](/images/image.png)

![alt text](/images/image-7.png)

### 3. Data Loading Pipeline

#### DAGs Overview
| DAG Name                     | Description                                                                                     |
| ---------------------------- | ----------------------------------------------------------------------------------------------- |
| **Update_VectorDB**      |Initializes Pinecone (vector store), tests connectivity to Firestore and Vector DB, and ingests/syncs data to vector store   |
 
#### DAG Execution Flow

![alt text](/images/image11.png)

![alt text](/images/image12.png)

#### Logging and Tracking
- Logs are generated at each step and for all functions.
- The logs are currently collected using the in-built Airflow logger
- Errors are captured and logged for easy debugging and resolution.
- Any errors during the pipeline runs result in a failed run, and appropriate notifications are sent to alert about the status.

#### Notification

All DAGs send an email notification updating the status. The email notifications are sent for both failed/successful runs of the data pipelines. An example of the email notification is attached below.

![alt text](/images/image_10.png)


#### LLM and API Used
We utilize the OpenRouter API via the LangChain OpenAI package to generate text-based content. The responses are validated using Pydantic to maintain structure and consistency.

- Model used: LLaMA- **meta-llama/llama-3.3-70b-instruct:free**

OpenRouter Models: https://openrouter.ai/models