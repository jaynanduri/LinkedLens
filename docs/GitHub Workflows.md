## DAG Deployment Automation
- There are three GitHub Action workflows currently set up:
    - `update_code_vm.yml`: Ensure git repo changes are synced to VM
    - `trigger_airflow_generation.yml`: Restarts the airflow container for the data generation pipeline
    - `trigger_airflow_data_pipeline.yml`: Restarts the airflow container for the data pipeline
- The `update_code_vm.yml` workflow is triggered when there are changes to the respective pipeline folders (`data-generation/**` and `data-preprocessing/**`) on the main branch or when using manual dispatch.
- The remaining two workflows are triggered on completion of workflow runs of `update_code_vm.yml`. There are additional checks to ensure that the containers are only restarted when required.