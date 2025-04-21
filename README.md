# LinkedLens

The **LinkedLens** project is an AI-powered conversational assistant designed to enhance the job search experience on platforms like **LinkedIn**, which already offer a wealth of professional opportunities and content. However, with the growing volume of posts, listings, and user activity, it can become difficult for job seekers to find relevant information quickly and effectively. By integrating **Retrieval-Augmented Generation (RAG)** with **natural language processing**, LinkedLens enables users to retrieve and summarize **job listings**, **recruiter posts**, and **user-generated content** through intuitive conversational queries. The system is designed to support job seekers by making scattered, often unstructured professional data easily accessible and actionable.

The internal architecture is built using a structured **LangChain** workflow orchestrated with **LangGraph**, enabling a clean, modular pipeline. The chatbot operates in three stages: **query analysis**, which examines the user input, rewrites it if needed, and determines whether vector retrieval is necessary; **document retrieval and filtering**, which queries the vector store and discards low-relevance entries; and **final response generation**, which uses prompt engineering along with **Gemini Flash 2.0** to deliver accurate and context-aware answers.

LinkedLens uses **Pinecone** as its vector store to index job listings, user posts, and associated metadata. The backend is developed using **FastAPI** and deployed on **Google Kubernetes Engine (GKE)** as **stateless endpoints**, with session management and state handled on the web frontend. **FirestoreDB** is used to store raw data and preprocessed metadata, while **PostgreSQL** powers the website layer through **OpenWebUI**, managing chat history, feedback, and session-level interactions.

**GitHub Actions** is used to automate continuous integration and deployment pipelines. The evaluation framework for LinkedLens is split into three stages: **pre-evaluation**, where **RAGAS** is used to generate synthetic queries on known contexts and evaluate outputs using **LLM-as-Judge** via **RAGAS** and **EvidentlyAI**; **real-time evaluation**, which uses **cosine similarity** (via **sentence-transformers**) to estimate **context relevance**, **response relevance**, and **faithfulness** for quick feedback without introducing LLM latency; and **post-evaluation**, which periodically fetches user traces from **LangSmith** and runs full LLM-based evaluations to monitor long-term system behavior.

**LangSmith** is integrated for end-to-end tracing of all LLM interactions, supporting debugging and qualitative analysis. Logs from the system are captured through **GCP Logging**, visualized with **Grafana** dashboards, and monitored for system alerts. Although the backend is stateless and internally accessible, architectural boundaries and containerized deployment within **GKE** help ensure a secure and controlled runtime environment.

## System Architecture

![Diagram to show System architecture](/images/Architecture_updated.jpeg)

## Project Components

The main components of this project can be broken down to the following:

1. [Data Pipelines](/data-pipelines/DATA_PIPELINES.md)
2. [Model Development Pipeline](/model-development/README.md)
3. [CI/CD Workflows](/docs/CI_CD_Workflows.md)
4. [GCP Infrastructure & Deployment](/infra/README.md)
5. [Web Interface (OpenWebUI) – External Repo](https://github.com/jaynanduri/open-webui)
6. [Logging Monitoring](/monitoring/README.md)


## Project Setup Guidelines

For detailed instructions on setting up the project both **locally** and on **GCP**, refer to the full [Project Setup Guide](/docs/PROJECT_SETUP.md).


## Project Folder Structure

Below is a high-level view of the project’s folder layout:

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

For detailed descriptions of each folder and key files, see the [[Folder Structure Details](/docs/FOLDER_STRUCTURE.md)]

## Project Deployment

The project deployment is available at:

[http://linkedlens.duckdns.org/](http://linkedlens.duckdns.org/)
