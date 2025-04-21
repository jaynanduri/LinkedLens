#!/bin/bash

gcloud container clusters get-credentials linkedlens-cluster --zone us-east1-d --project linkedlens-452503

kubectl apply -f ./kubernetes/namespace.yaml

kubectl apply -f ./kubernetes/model-svc.yaml

kubectl annotate serviceaccount linkedlens-ksa --namespace app iam.gke.io/gcp-service-account=firestoreserviceaccount@linkedlens.iam.gserviceaccount.com

gcloud iam service-accounts add-iam-policy-binding firestoreserviceaccount@linkedlens.iam.gserviceaccount.com --role roles/iam.workloadIdentityUser --member "serviceAccount:linkedlens-457503.svc.id.goog[app/linkedlens-ksa]" --project=linkedlens