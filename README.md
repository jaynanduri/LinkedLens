# LinkedLens

LinkedLens aims to enhance and streamline existing job search portals and professional social media platforms. The project integrates a conversational chatbot with Retrieval Augmented Generation (RAG) to allow users to retrieve and summarize information using natural language queries. LinkedLens seeks to aid job seekers and recruiters in their job search experience in an already competitive market by making information ranging from company listings, recruiter posts, and other user posts easily searchable and available. 

### Key Features
* Search beyond current user network and connections
* Continuous data integration for an updated database of job openings
* Tracking Time-To-Live for posts to ensure latest insights
* Providing links to original posts along with summaries

## Project Components

The main components of this project can be broken down to the following:

1. [Data Pipelines](/data-pipelines/)
2. [Model Development Pipeline](/model-development/)
3. [Testing & Automation](/docs/CD_Pipeline.md)
4. [Cloud Deployment](/cloud-functions/)

## System Architecture

![Diagram to show System architecture](/images/Architecture_updated.jpeg)

## Logging and Monitoring

The logging for the project is currently being handled separately by Airflow Logger (data pipelines) and Cloud Logger. 

## Folder Structure

```
LinkedLens
   |- .github/              # GitHub workflow automations
   |- data-pipelines/       # Airflow DAGs for data preprocessing and generation
   |- cloud-functions/      # For any setup scripts, cloud functions/trigger
   |- model-development/    # Model Development pipeline using LangGraph
   |- images/               # Images for documentation and visualizations
   |- docs/                 # Additional documentation and guides
   |- README.md
```
## Installation

The repo can be cloned using the following:

```
git clone https://github.com/jaynanduri/LinkedLens.git
```

The DAGs can be run on a local or hosted Docker installation of Airflow. To install Docker using Airflow, use the docker-compose.yml provided in the [pipeline folder](/data-pipelines/data-generation/docker-compose.yaml). 

```
docker-compose up
```

Navigate to the Airflow instance endpoint and run the required DAGs.

The data gets pushed to Firestore DB by the data-generation pipeline and then to the Pinecone Vector DB for ingestion.

The model development pipeline can be run by first installing the required libraries given in the `requirements.txt` in the `model-development/src` using:

```
pip install requirements.txt
```

and then the following command to run the model pipeline:

```
python main.py
```

Alternatively, the pipeline can be run using the Dockerfile providd. Navigate to the `model-development/src` folder and run:

```
docker build -t model-image:latest .

docker run -it -p 80:80 model-image:latest
```