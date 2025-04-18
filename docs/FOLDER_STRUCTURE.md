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
├─── docs/                      # Readme files for the project
├─── images/                    # Images for the readme folder
├─── .env_template/             # .env file template
├─── requirements.txt/          # Dependency requirements for the project
├─── README.md/                 # Project documentation
```