#!/bin/bash

gcloud container clusters get-credentials linkedlens-cluster --region us-east1 --project linkedlens-452503

kubectl apply -f /kubernetes/namespace.yaml

kubectl apply -f /kubernetes/model-svc.yaml

kubectl annotate serviceaccount \
  linkedlens-ksa \
  --namespace app \
  iam.gke.io/gcp-service-account=firestoreserviceaccount@linkedlens.iam.gserviceaccount.com