# CI/CD Workflows

This document explains the CI/CD workflows configured in the project using **GitHub Actions**. Each component of the system (Data Pipelines, Model Backend, Web Interface, etc.) has its own workflow(s) to ensure reliable deployment and integration.

## Data Pipelines:

### Workflows

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
