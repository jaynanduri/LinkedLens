# CI/CD Workflows

This document explains the CI/CD workflows configured in the project using **GitHub Actions**. Each component of the system (Data Pipelines, Model Backend, Web Interface, etc.) has its own workflow(s) to ensure reliable deployment and integration.

## Continuous Integration

The [CI pipeline](/.github/workflows/CI.yml) is used to test the model and data pipelines prior to deployment to production clusters. The CI setup runs two jobs in parallel: `Model Unit Tests` and `Data Pipeline Unit Tests`.

The Model Unit Tests job runs the [model unit tests](/model-development/tests/) followed by the model pre-deployment evaluation. Failure to pass either will result in the model not being deployed. If the job finishes successfully, the deployment workflow is triggered.

The Data Pipeline Unit Tests job runs the data generation pipeline unit tests and the data ingestion pipeline unit tests. 

The CI workflow is the first to run and trigger other workflows depending on job success/failure.

![CI/CD](/images/CI.png)


## Data Pipelines:

### DAG Deployment Automation

- There are three GitHub Action workflows currently set up:
    - `update_code_vm.yml`: Ensure git repo changes are synced to VM
    - `trigger_airflow_generation.yml`: Restarts the airflow container for the data generation pipeline
    - `trigger_airflow_data_pipeline.yml`: Restarts the airflow container for the data pipeline
- The `update_code_vm.yml` workflow is triggered when there are changes to the respective pipeline folders (`data-generation/**` and `data-preprocessing/**`) on the main branch or when using manual dispatch.
- The remaining two workflows are triggered on completion of workflow runs of `update_code_vm.yml`. There are additional checks to ensure that the containers are only restarted when required.

1. **Sync Latest Code to VM**
    - **Trigger** : changes in main for path : `LinkedLens/data-pipelines/`
    - **Action**: 
        1. SSH into VM
        2. Pull the latest code from the repository.
        3. Add .env file
        4. Add GCP credentials `.json` file
    - **Workflow** : [update_code_vm.yaml](../.github/workflows/update_code_vm.yml)
    - **name**: Push DAGs changes to VM


2. **Trigger Airflow DAGs**
    - **Trigger** : Completion of Push DAGs changes to VM workflow
    - **Action**: 
        1. SSH into VM
        2. Validates if there were changes to the specific DAG folder
        3. Restart Docker
        4. Ensure the Airflow endpoint is up and running. 
    - **Workflow** : 
        - [data-generation-workflow](../.github/workflows/trigger_airflow_generation.yml)
        - [data-ingestion-workflow](../.github/workflows/trigger_airflow_data_pipeline.yml)

## Model Pipelines

The model pipelines are deployed to a Google Kubernetes Engine cluster ([setup](/docs/GKE-Setup.md)). Before triggering the workflow, enable keyless authentication [[Script to setup workload identity provider keyless_authetication.sh](/infra/scripts/keyless_authentication.sh)]
- Along with the service accounts, this project makes use workload identity pools to authenticate GitHub Actions to GCloud.

### Model Deployment Automation

- The GitHub Action workflow `deploy-to-gke.yml` is used to deploy the model pipeline to the cluster hosted on Google Kubernetes Engine.
- Once the connection has been made the docker image is built and pushed to the Artifact Repository created for this project.
- The `IMAGE_TAG` is set to the first 7 characters of the Git commit hash ( `${{ github.sha }}` ).
- The workflow checks if ConfigMap and Secrets exist, and applies them if they do not exist. 
- The Docker image is then deployed to GKE using the `deployment.template.yaml` and `service.yaml` files. 
- `.template.yaml` files are used for ConfigMap, Secret, and Deployment so that values can be injected using GitHub Repository Variables and Secrets.
- Deployment status is checked by comparing the correct `$COMMIT_SHA` with the deployed image tag obtained from the K8s cluster.

## Logs Workflow

The [logs workflow](/.github/workflows/log-results.yml) is a reusable workflow that is used to log GitHub workflow events to Cloud Logger. It required a message, success, workflow type, and a timestamp as inputs along with the service account key as secret.

## GitHub Repo Variables and Secrets

The following have to be added as Repo variables:

| Variable Names | Description |
| --- | --- |
| PROMPT_VERSION_FINAL_RESPONSE  | Version of the final response prompt |
| PROMPT_VERSION_QUERY_ANALYZER | Version of the query analyzer prompt |
| GKE_CLUSTER_NAME | Google K8s cluster name  |
| GCP_REGION | Google K8s cluster region |
| ARTIFACT_REPO | Repo name on Artifact Registry |
| GCP_PROJECT_ID | PROJECT_ID of project hosting GKE |

The following have to be added as Repo secrets:

| Secret Name | Descripion |
| --- | --- |
| GCP_CREDENTIALS_JSON | Service account key for GCP project |
| GCP_WORKLOAD_IDENTITY_PROVIDER | Workload Identity Provider for GitHub Actions auth |
| SERVICE_ACCOUNT (for GitHub) | Service account needed for Workload Identity |
| PINECONE_ENVIRONMENT | Pinecone Env Region |
| GOOGLE_PROJECT_ID | GCP Project ID  |
| PROMPT_ID_QUERY_ANALYZER  | Prompt ID for query analyzer  |
| PROMPT_ID_FINAL_RESPONSE | Prompt ID for final response |
| PINECONE_API_KEY | Pinecone API key |
| HF_TOKEN | HuggingFace token |
| GEMINI_API_KEY | Gemini API KEY |
| LANGSMITH_API_KEY | Langsmith API key |
| SERVER_IP  | Server IP for Compute VM |
| SERVER_USERNAME | Server username for Compute VM |
| SERVER_KEY | Server key for Compute VM |
| SSH_PORT | SSH port for Compute VM |
| MAX_OPEN_AI_REQUEST_PER_MIN  | Airflow max requests |
| MAX_OPEN_AI_REQUEST_PER_DAY | Airflow min requests |
| OPEN_ROUTER_BASE_URL | OpenRouter base URL |
| SMTP_SERVER | Email SMTP server |
| SMTP_STARTTLS  | Email SMTP config |
| SMTP_USER | Email SMTP user |
| SMTP_PASSWORD | Email SMTP password |
| SMTP_PORT | Email SMTP port |
| SMTP_TIMEOUT  | Email SMTP timeout |
| SMTP_RETRY_LIMIT | Email SMTP retry limit |
| SMTP_RECIPIENT_EMAIL | Email SMTP notifications recepient |
| AIRFLOW_WWW_USER_USERNAME | Airflow username |
| AIRFLOW_WWW_USER_PASSWORD | Airflow password |