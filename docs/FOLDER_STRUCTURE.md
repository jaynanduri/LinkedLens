# Project Folder Structure
This document provides an overview of the project structure, including key folders and a high-level description of their purpose. It also includes detailed tables listing the important files in each major folder.

## Folder Structure
```
root/
├─── .dvc/
|    ├── config                 # DVC core settings and remote storage
├─── .github/
|    ├── workflows/             # CI/CD workflows
├─── data-pipelines/            # Data preprocessing and pipeline scripts
|    ├── data-generation/       # Data Genaration DAG
|    ├── data-ingestion/        # Data Ingestion DAG
|    ├── preprocessing.py       # Raw Kaggle data preprocessing script
|    ├── upload_data_gcp.py     # Upload preprocessed data to GCP bucket
|    ├── data.dvc               # DVC tracking file for data
├─── kubernetes/
|    ├── config.yaml            # Kubernetes config YAML
├─── model-development/         # RAG model backend and API endpoint code
|    ├── eval/                  # pre- and post-deployment evaluation scripts
|    ├── src/                   # Source code for RAG model and endpoint
|    |   ├── clients/           # Service clients for Pinecone, Firestore, and embedding
|    |   ├── config/            # App settings and constants
|    |   ├── graph/             # State, nodes and langgraph workflow
|    |   ├── kubernetes/        # Kubernetes deployment and service YAMLs
|    |   ├── services/          # LLM setup, prompt utils, and similarity scoring logic
|    |   ├── Dockerfile         # Docker for containerizing RAG model
|    |   ├── endpoints.py       # Defines FastAPI routes
|    |   ├── logger.py          # logger
|    |   ├── main.py            # Entry point for the FastAPI app
|    |   ├── requirements.txt   # Dependency requirements for RAG app
|    ├── tests/                 # Unit tests for model
├─── infra/
|    ├── functions/             # Cloud Run function scripts and container
|    ├── scripts/               # Bash scripts for GKE deployment
├─── monitoring/                # Monitoring Dashboards
├─── docs/                      # Readme files for the project
├─── images/                    # Images for the readme folder
├─── .env_template/             # .env file template
├─── requirements.txt/          # Dependency requirements for the project
├─── README.md/                 # Project documentation
```

## Detailed Folder Descriptions:

### 1. .github/workflows/

| File             | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `deploy-to-gke.yml`            | Workflow to deploy model-enpoint to GKE             |
| `tigger_airflow_data_pipeline.yml`            | Workflow to trigger the data-ingestion pipeline hosted on VM             |
| `trigger_airflow_generation.yml`            | Workflow to trigger the data-generation pipeline hosted on VM             |
| `update_code_vm.yml`            | Workflow to update the  latest code on VM for data pipelines             |


### 2. data-pipelines/data-generation/dags/

| File             | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `data_prepocess_generation.py`            | Airflow DAG that defines the data generation pipeline              |

#### src/

| File             | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `config/config.py`            | Loads env variables and sets other constants             |
| `experiments/test_API_call.ipynb`| Jupyter notebook used for testing LLM API calls and prompt behavior  |
| `llm/`                           | Initializes and returns the appropriate LLM based on model name and parameters in the `llm_config.py`   |
| `schema/`                        | Contains all Pydantic classes for validating Firestore input data and LLM output               |
| `utils/`                         | Utility modules used for the data generation pipelines                                  |


### 3. data-pipelines/data-ingestion/dags/

| File             | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `update_vectordb_dag.py`            | Airflow DAG that defines the data ingestion pipeline              |

#### src/

| File          | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| `clients/`              | Classes for interacting with Firestore, Pinecone, and SentenceTransformer  |
| `config/settings.py`    | Loads all constants and environment variables used by the DAG              |
| `scripts/`              | Scripts to test connections with Firestore, Pinecone, and embeddings       |
| `processors/`           | Handles document processing and vectorization                              |
| `utils/`                | Utility functions used across the pipeline                                 |
| `main.py`               | Main entry point that the DAG calls to run the pipeline                    |


### 4. infra/functions/

#### dag-trigger/ 

| File / Folder             | Description                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| `dag-firebase-trigger.py` | Defines the Cloud Run function that's triggered to start the ingestion DAG |
| `Dockerfile`              | Container for deploying the Cloud Run function                       |

#### scripts/
| File / Folder              | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| `keyless_authentication.sh`| Script to set up keyless authentication between GCP and GitHub Actions     |
| `deploy_gke.sh`            | Script to deploy a GKE (Google Kubernetes Engine) cluster    |



### 5. model-development/src/

| File         | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `graph/state.py`            | Defines the state structure used throughout the LangGraph workflow         |
| `graph/nodes.py`            | Implements functions that act as individual nodes in the workflow graph    |
| `graph/graph_builder.py`    | Constructs and compiles the full LangGraph workflow                        |


### 6. model-development/eval/


| File / Folder           | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| `evaluators.py`         | Defines evaluators using RAGAS and Evidently AI (LLM-as-a-judge)           |
| `langsmith_client.py`   | Class to interact with LangSmith for fetching and managing traces          |
| `query_runner.py`       | Runs test queries through the model workflow for evaluation                |
| `ragas_query_generator.py` | Generates synthetic test queries using the RAGAS library                  |
| `settings.py`           | Loads env variables and constants used for post-eval setup                 |
| `post_eval.py`          | Script to run post-deployment evaluation, deployed as a Cloud Run Job      |
| `pre_eval.py`           | Script used in CI to test model performance before deployment              |
| `setup.sh`              | Script to containerize and deploy the post-eval job to Cloud Run           |