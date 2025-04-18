# GCP Infrastructure

The GCP services used in this project include the following:

1. Cloud Run
   - Cloud Run is used to setup Cloud Functions that trigger the data ingestion pipeline when updates are made to the FirestoreDB. [[Setup](/infra/functions/dag-trigger/README.md)]
2. Compute Engine
   - The VMs provisioned on Compute Engines are used to host the Airflow instances that run the Data DAGs. We use one Debian-based VM with Airflow deployed as a Docker container to run the DAGs. [[Setup](/docs/GCP_Setup.md)] 
3. Google Kubernetes Engine
    - A cluster is provisioned om Google Kubernetes Engine. Currently, the model pipeline is deployed on the cluster with an exposed API endpoint to send queries and receive responses. The cluster is setup to have images deployed by [GitHub Actions](/docs/CD_Pipeline.md). [[Setup](/docs/GKE-Setup.md)]
4. Artifact Repository
    - The images being built for the model pipeline and Artifacts built by other pipelines are pushed to the Artifact Repository, from where they can be deployed to GKE or Cloud Run.
5. Prompt Management
    - The Prompt Management service is used to store and retrive prompts used by the LLM to respond to user queries. [[Setup](/docs/GCP_Setup.md)] 
6. Cloud Logger
    - Cloud Logger collects the logs from the different componenets of the project except the DAGs (handled by Airflow logger). These logs can then be further parsed to setup dashboards and alerting.
7. FirestoreDB
    - FirestoreDB is used to store generated and processed user posts, job postings, and recruiter posts. This will receive the data from the data generation pipeline.[[Setup](/docs/GCP_Setup.md)] 
8. Google Cloud Storage
    - Used to load the initial job postings from the Kaggle dataset. A bucket is also used to store the logs from Airflow Logger. [[Setup](/docs/GCP_Setup.md)] 
