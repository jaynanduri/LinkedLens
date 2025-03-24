# Continuous Deployment

This project utilizes GitHub Actions to automate the CD pipeline to deploy to GCE and GKE respectively. The workflows are split based on functionality as shown below. 

## DAG Deployment Automation

- There are three GitHub Action workflows currently set up:
    - `update_code_vm.yml`: Ensure git repo changes are synced to VM
    - `trigger_airflow_generation.yml`: Restarts the airflow container for the data generation pipeline
    - `trigger_airflow_data_pipeline.yml`: Restarts the airflow container for the data pipeline
- The `update_code_vm.yml` workflow is triggered when there are changes to the respective pipeline folders (`data-generation/**` and `data-preprocessing/**`) on the main branch or when using manual dispatch.
- The remaining two workflows are triggered on completion of workflow runs of `update_code_vm.yml`. There are additional checks to ensure that the containers are only restarted when required.

## Model Deployment Automation

- The GitHub Action workflow `deploy-to-gke.yml` is used to deploy the model pipeline to the cluster hosted on Google Kubernetes Engine.
- The workflow makes use of Workflow Identity Providers to authenticate with and connect to GCloud.
- Once the connection has been made the docker image is built and pushed to the Artifact Repository created for this project.
- The docker image is then deployed to GKE using the `deployment.yaml` and `service.yaml` files.
- Any failures in this workflow will result in an alert being sent bua email.