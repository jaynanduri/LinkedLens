# Logging, Alerting, and Monitoring

Monitoring, Logging, and Alerting is setup using Google Cloud Logger combined with Grafana. Cloud logger collects logs from the different services set up across GCP and GitHub Actions. Grafana uses these logs to set up monitoring dashboards.

## Logging

Logging is done from the following sources:

| Log Name | Description |
|----------|-------------|
| github_action_logs | Logs from the GitHubActions workflow |
| linkedlens_chat | Logs tracking model requests, LangGraphn node exeutions, model pipeline failures, and real-time evaluations |
| linkedlens_pre_eval | Pre-deployment Evaluation of model pipeline. Results, errors, and metrics summary |
| linkedlens_post_eval | Post-deployment Evaluation of model pipeline. Results, errors, and metrics summary |

The logs from Airflow are tracked separately by the Airflow instance itself. Langsmith is used to trace calls to model pipeline and these logs are retrieved and used for scheduled post-deployment evaluations, and for monitoring. The GitHub Actions logs are created and stored by the [log-results.yml](/.github/workflows/log-results.yml) workflow.

## Alerting

Cloud Monitoring is used to set up log-based alerts for severe to moderate errors in the model-pipeline and CI workflow for pre-deployment evaluations failures.
The three main alerts are:
- Middleware unhandled exception (!!)
- Node Process Failure (!!!)
- Pre-deployment Evaluation failures (!!)

All three alerts are configured to send out email notifications to the managed email addresses with varying frequency depending on the severity.

![Example Alert](/images/email-alert.png)

## Monitoring

Monitoring is done using Grafana Cloud. Setting up an instance of Grafana cloud involves signing up for the service and adding Google Cloud Logging as a data source. The instructions for creating a new connection and adding gclou-logging as a data source can be found [here](https://grafana.com/grafana/plugins/googlecloud-logging-datasource/). Additionally, the data from `PostgreSQL` stored by `Open-webui` is also accessesible using the builtin PostgrSQL data connector.

The following dashboards are setup:

| Log Name | Description |
|----------|-------------|
| GitHub Logs | GitHubActions workflow runs, unit test results |
| Model Requests | No. of model requests received, completed successfully, and completed unsucessgully along with run logs |
| Model Feedback | User feedback per chat (+1/-1) from PostgreSQL |
| Pre-Evaluation | Pre-deployment Evaluation of model pipeline. Results, errors, and metrics summary timeseries and tables |
| Post-Evaluation | Post-deployment Evaluation of model pipeline. Results, errors, and metrics summary timeseries and tables |
| Errors | Errors count, and occurences |

### Example Dashboards

All Grafana dashboards can be found in the [/monitoring/dashboards](/monitoring/dashboards/) folder and can be imported into any Grafana instance that has a working `gcloud-logging` plugin.

1. Post Deployment Evaluations
   ![post deploy eval](/images/post-eval.png)

2. Model Requests
   ![model requests](/images/model-requests.png)