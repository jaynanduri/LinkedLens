#!/bin/bash

set -euo pipefail

# Configure variables
REGION="us-central1"
PROJECT_ID="linkedlens"
REPO="post-eval"
IMAGE_NAME="post-eval"
TAG="latest"
JOB_NAME="post-eval-job"
TRIGGER_NAME="post-eval-job-trigger"
SERVICE_ACCOUNT="firestoreserviceaccount@linkedlens.iam.gserviceaccount.com"
FULL_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE_NAME:$TAG"
TIMEZONE="America/New_York"
CRON_SCHEDULE="0 1 * * *"
SECRETS_VARS="GEMINI_API_KEY=GEMINI_API_KEY:latest,LANGSMITH_API_KEY=LANGSMITH_API_KEY:latest,HF_TOKEN=HF_TOKEN:latest"
TRIGGER_URI="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run"
ENV_FILE="$(dirname "$0")/../../.env"

# List of keys to include in ENV_VARS
SELECTED_KEYS=("LANGSMITH_TRACING" "LANGSMITH_ENDPOINT" "LANGSMITH_PROJECT" "GOOGLE_PROJECT_ID")

# Initialize empty ENV_VARS string
ENV_VARS=""

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
  echo " .env file not found at $ENV_FILE"
  exit 1
fi

echo "Loading selected variables from $ENV_FILE..."

# Loop and build ENV_VARS, or stop if any key is missing
for key in "${SELECTED_KEYS[@]}"; do
  value=$(grep -E "^${key}=" "$ENV_FILE" | cut -d '=' -f2- | sed -e 's/^["'"'"']//' -e 's/["'"'"']$//')
  if [ -n "$value" ]; then
    if [ -n "$ENV_VARS" ]; then
      ENV_VARS+=","
    fi
    ENV_VARS+="${key}=${value}"
  else
    echo "Required key '$key' not found in .env.. aborting."
    exit 1
  fi
done

# Show final result
echo "Final ENV_VARS: $ENV_VARS"

# Required secrets
REQUIRED_SECRETS=("GEMINI_API_KEY" "LANGSMITH_API_KEY" "HF_TOKEN")

# Validate if secrets exists in secrets Manager
echo "Validating required secrets in Secret Manager..."
for secret in "${REQUIRED_SECRETS[@]}"; do
  if ! gcloud secrets describe "$secret" &>/dev/null; then
    echo "Required secret '$secret' not found. Please create required secrets before retrying: '${REQUIRED_SECRETS[@]}'."
    exit 1
  else
    echo "Secret '$secret' exists."
  fi
done

# Check if repo exists on artifact. Create if not
if ! gcloud artifacts repositories describe "$REPO" --location="$REGION" &>/dev/null; then
  echo "Artifact Registry repo '$REPO' not found. Creating..."
  gcloud artifacts repositories create "$REPO" --repository-format=docker --location="$REGION" --description="Docker repo for post evaluation job"
else
  echo "Artifact Registry repo '$REPO' already exists. Skipping creation."
fi

echo "Authenticating Docker to GCP Artifact Registry..."
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

echo "Building Docker image: $FULL_IMAGE..."
docker build -t $FULL_IMAGE .

echo "Pushing Docker image..."
docker push $FULL_IMAGE

echo "Creating or updating Cloud Run job: $JOB_NAME"
gcloud run jobs describe "$JOB_NAME" --region="$REGION" &>/dev/null && JOB_EXISTS=true || JOB_EXISTS=false

if [ "$JOB_EXISTS" = true ]; then
  echo "Updating existing job..."
  gcloud run jobs update "$JOB_NAME" --region="$REGION" --image="$FULL_IMAGE" --service-account="$SERVICE_ACCOUNT" --memory=1Gi --cpu=1 --set-env-vars=$ENV_VARS --set-secrets=$SECRETS_VARS
else
  echo "Creating new job..."
  gcloud run jobs create "$JOB_NAME" --region="$REGION" --image="$FULL_IMAGE" --service-account="$SERVICE_ACCOUNT" --memory=1Gi --cpu=1 --set-env-vars=$ENV_VARS --set-secrets=$SECRETS_VARS
fi

if gcloud scheduler jobs describe "$TRIGGER_NAME" --location="$REGION" &>/dev/null; then
  echo "Updating existing schedule.."
  gcloud scheduler jobs update http "$TRIGGER_NAME" --schedule="$CRON_SCHEDULE" --uri="$TRIGGER_URI" --http-method=POST --oauth-service-account-email="$SERVICE_ACCOUNT" --time-zone="$TIMEZONE" --location="$REGION"
else
  echo "Creating new schedule.."
  gcloud scheduler jobs create http "$TRIGGER_NAME" --schedule="$CRON_SCHEDULE" --uri="$TRIGGER_URI" --http-method=POST --oauth-service-account-email="$SERVICE_ACCOUNT" --time-zone="$TIMEZONE" --location="$REGION"
fi

echo "Cloud Run Job Setup Complete! Job '$JOB_NAME' is configured with a daily trigger at 1AM EST.($CRON_SCHEDULE)"