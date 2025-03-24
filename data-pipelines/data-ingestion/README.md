## Data Ingestion Pipeline

This pipeline is triggered by a Cloud Run Function whenever there are changes made to the FirestoreDB collection. The purpose of this pipeline is to ingest the data to the vector store, Pinecone from where it would be used by the RAG model.

## DAG Overview
| DAG Step                     | Description                                                                                     |
| ---------------------------- | ----------------------------------------------------------------------------------------------- |
| **Update_VectorDB**      |Initializes Pinecone (vector store), tests connectivity to Firestore and Vector DB, and ingests/syncs data to vector store   |
 
![Data Ingestion Pipeline](/images/data_ingestion.png)