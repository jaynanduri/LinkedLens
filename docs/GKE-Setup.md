## Setting Up Google Kubernetes Engine and Connecting to GitHub Actions

1. Create a cluster on GKE ([glcoud command to create cluster](infra/scripts/deploy_gke.sh)) using the following command:
    ```
        gcloud beta container \
        --project "linkedlens-452503" \
        clusters create "linkedlens-cluster" \
        --zone "us-east1-d" \
        --tier "standard" \
        --no-enable-basic-auth \
        --cluster-version "1.32.2-gke.1182003" \
        --release-channel "regular" \
        --machine-type "e2-standard-8" \
        --image-type "COS_CONTAINERD" \
        --disk-type "pd-balanced" \
        --disk-size "50" \
        --metadata disable-legacy-endpoints=true \
        --max-pods-per-node "110" \
        --num-nodes "2" \
        --logging=SYSTEM,WORKLOAD \
        --monitoring=SYSTEM,STORAGE,POD,DEPLOYMENT,STATEFULSET,DAEMONSET,HPA,CADVISOR,KUBELET \
        --enable-ip-alias \
        --network "projects/linkedlens-452503/global/networks/default" \
        --subnetwork "projects/linkedlens-452503/regions/us-east1/subnetworks/default" \
        --no-enable-intra-node-visibility \
        --default-max-pods-per-node "110" \
        --enable-autoscaling --min-nodes "0" \
        --max-nodes "5" --location-policy "BALANCED" \
        --enable-ip-access --security-posture=standard \
        --workload-vulnerability-scanning=disabled \
        --no-enable-google-cloud-access \
        --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver \
        --enable-autoupgrade \
        --enable-autorepair \
        --max-surge-upgrade 1 \
        --max-unavailable-upgrade 0 \
        --maintenance-window-start "2025-04-19T04:00:00Z" \
        --maintenance-window-end "2025-04-20T04:00:00Z" \
        --maintenance-window-recurrence "FREQ=WEEKLY;BYDAY=TU,WE,TH,FR,SA" \
        --binauthz-evaluation-mode=DISABLED --enable-autoprovisioning \
        --min-cpu 1 --max-cpu 6 \
        --min-memory 1 --max-memory 10 \
        --autoprovisioning-locations=us-east1-b,us-east1-c \
        --autoprovisioning-scopes=https://www.googleapis.com/auth/cloud-platform \
        --enable-autoprovisioning-autorepair \
        --enable-autoprovisioning-autoupgrade \
        --autoprovisioning-max-surge-upgrade 2 \
        --autoprovisioning-max-unavailable-upgrade 0 \
        --enable-managed-prometheus \
        --workload-pool "linkedlens-452503.svc.id.goog" \
        --enable-shielded-nodes \
        --shielded-integrity-monitoring \
        --no-shielded-secure-boot \
        --node-locations "us-east1-d"
    ```
    Modify the command to have your project name, and change other customizable specifications such as number of nodes.
    
    Key Configurations:
    1. No. of nodes: 1
    2. Zonal cluster
    3. Enable Workload Identity pool `--workload-pool "<PROJECT_ID>.svc.id.goog"`
    4. Enable node autoscaling
    5. Instance type: `e2-standard8`

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
3. Run the script [startup_gke.sh](/infra/scripts/startup_gke.sh) to setup namespace and `Kubernetes Service Accounts` for the model-development pipeline. The created KSA is linked to the service account that has `Log Viewer` role enabled.
4. To run the GitHub workflow the following values have to be given as Env variables and Secrets:
   1.  env.GCP_PROJECT_ID (GCP Project ID )
   2.  secrets.GCP_WORKLOAD_IDENTITY_PROVIDER (Workload Identity Pool provider, ensure that the workload_identity_provider is given in its entirety) 
   3.  secrets.SERVICE_ACCOUNT (Service account associated with the Workload Identity Provider)
   4.  env.GCP_REGION (GCP Region of the cluster)
   5.  env.GCP_PROJECT_NAME (Project name)
   6.  env.ARTIFACT_REPO (Name of Repository created to push Docker images)
   7.  env.GKE_CLUSTER_NAME (GKE cluster to which the image is to be deployed)
