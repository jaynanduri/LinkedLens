#!/bin/bash
# This script contains the commands required to setup keyless authetication with GCP and GItHub Actions

# 1. Set the project for which the cluster is to be created
gcloud config set project linkedlens-452503

# 2. Obtain the project number and set the PROJECT_NUMBER variable with it.
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value core/project) --format='value(projectNumber)')

# 3. Create a workload identity pool named github-actions. If project is set, the --project option may be excluded (for this and any command that follows in the same session).
gcloud iam workload-identity-pools create github-actions --location="global" --description="GitHub Actions Auth" --display-name="GitHub Actions" --project="linkedlens-452503"

# 4. Create an oidc provider named github-actions-oidc. This will verify authorization to the GitHub repo. Change value of --attribute-condition="attribute.repository=='jaynanduri/LinkedLens'" to the repo you will be using.
gcloud iam workload-identity-pools providers create-oidc github-actions-oidc --location="global" --workload-identity-pool="github-actions" --display-name="Github Actions OIDC" --project="linkedlens-452503" --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.aud=assertion.aud,attribute.job_workflow_ref=assertion.job_workflow_ref" --issuer-uri="https://token.actions.githubusercontent.com" --attribute-condition="attribute.repository=='jaynanduri/LinkedLens'"

# 5. Setup a service account to use with the workload-identity-pool
SERVICE_ACCOUNT=$(gcloud iam service-accounts create github-actions-workflow --display-name="Github Actions workflow" --format "value(email)")

# 6. Add IAM policies to the created service account. First for the role artifactregistry.writer to enable push to Artifact Repository.
gcloud projects add-iam-policy-binding $(gcloud config get-value core/project) --member serviceAccount:$SERVICE_ACCOUNT --role roles/artifactregistry.writer

# 7. Next, we give the role container.developer to ensure GKE deployments are allowed.
gcloud projects add-iam-policy-binding $(gcloud config get-value core/project) --member serviceAccount:$SERVICE_ACCOUNT --role roles/container.developer

# 8. Set the Subject to the repo and branch which allows access.
SUBJECT=repo:jaynanduri/LinkedLens:ref:refs/heads/main

# 9. Add the role iam.workloadIdentityUser to the service account created.
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT --role=roles/iam.workloadIdentityUser --member="principal://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/subject/$SUBJECT"

# In GitHub Actions, the workload identity provider will be of the form:
# projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/providers/github-actions-oidc

# References:
# https://cloud.google.com/dotnet/docs/getting-started/deploying-to-gke-using-github-actions#before-you-begin
# https://cloud.google.com/blog/products/identity-security/enabling-keyless-authentication-from-github-actions