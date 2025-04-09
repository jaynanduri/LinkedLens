## Setting Up Google Kubernetes Engine and Connecting to GitHub Actions

1. Create a cluster on GKE ([glcoud command to create cluster](infra/scripts/deploy_gke.sh)) using the following command:
    ```
        gcloud beta container --project "linkedlens-452503" clusters \
        create "cluster-1" --region "us-east1" --tier "standard" \
        --no-enable-basic-auth --cluster-version "1.31.6-gke.1020000" \
        --release-channel "regular" --machine-type "e2-medium" \
        --image-type "COS_CONTAINERD" --disk-type "pd-balanced" 
        --disk-size "100" --metadata disable-legacy-endpoints=true 
        --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" \
        --num-nodes "1" --logging=SYSTEM,WORKLOAD \
        --monitoring=SYSTEM,STORAGE,POD,DEPLOYMENT,STATEFULSET,DAEMONSET,HPA,CADVISOR,KUBELET \
        --enable-ip-alias --network "projects/linkedlens-452503/global/networks/default" 
        --subnetwork "projects/linkedlens-452503/regions/us-east1/subnetworks/default" \
        --no-enable-intra-node-visibility --default-max-pods-per-node "110" --enable-ip-access \
        --security-posture=standard --workload-vulnerability-scanning=disabled \
        --no-enable-google-cloud-access --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver \
        --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 \
        --binauthz-evaluation-mode=DISABLED --enable-managed-prometheus \
        --enable-shielded-nodes --shielded-integrity-monitoring \
        --no-shielded-secure-boot
    ```
    Modify the command to have your project name, and change other customizable specifications such as number of nodes.

2. Create an Artifact Repository to push Docker images using the following commnd:
    ```
    gcloud artifacts repositories create repo-name \
    --repository-format=docker \
    --location=us-central1

    ```
    Allow the Compute Engine default service account to access the repository created:
    ```
    gcloud projects add-iam-policy-binding $(gcloud config get-value core/project) \
    --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com \
    --role=roles/artifactregistry.reader
    ```
3. Enable keyless authentication [[Script to setup workload identity provider keyless_authetication.sh](/infra/scripts/keyless_authentication.sh)]
    - Along with the service accounts, this project makes use workload identity pools to authenticate GitHub Actions to GCloud.
4. To run the GitHub workflow the following values have to be given as Env variables and Secrets:
   1.  env.GCP_PROJECT_ID (GCP Project ID )
   2.  secrets.GCP_WORKLOAD_IDENTITY_PROVIDER (Workload Identity Pool provider, ensure that the workload_identity_provider is given in its entirety) 
   3.  secrets.SERVICE_ACCOUNT (Service account associated with the Workload Identity Provider)
   4.  env.GCP_REGION (GCP Region of the cluster)
   5.  env.GCP_PROJECT_NAME (Project name)
   6.  env.ARTIFACT_REPO (Name of Repository created to push Docker images)
   7.  env.GKE_CLUSTER_NAME (GKE cluster to which the image is to be deployed)
