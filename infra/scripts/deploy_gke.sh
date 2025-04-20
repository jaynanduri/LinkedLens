#!/bin/bash
# gcloud beta container \
# --project "linkedlens-452503" clusters create "cluster-1" \
# --region "us-east1" \
# --tier "standard" \
# --no-enable-basic-auth \
# --cluster-version "1.31.6-gke.1020000" \
# --release-channel "regular" \
# --machine-type "e2-medium" \
# --image-type "COS_CONTAINERD" \
# --disk-type "pd-balanced" \
# --disk-size "100" \
# --metadata disable-legacy-endpoints=true \
# --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" \
# --num-nodes "1" --logging=SYSTEM,WORKLOAD \
# --monitoring=SYSTEM,STORAGE,POD,DEPLOYMENT,STATEFULSET,DAEMONSET,HPA,CADVISOR,KUBELET \
# --enable-ip-alias \
# --network "projects/linkedlens-452503/global/networks/default" \
# --subnetwork "projects/linkedlens-452503/regions/us-east1/subnetworks/default" \
# --no-enable-intra-node-visibility --default-max-pods-per-node "110" \
# --enable-ip-access \
# --security-posture=standard \
# --workload-vulnerability-scanning=disabled \
# --no-enable-google-cloud-access \
# --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver \
# --enable-autoupgrade \
# --enable-autorepair \
# --max-surge-upgrade 1 \
# --max-unavailable-upgrade 0 \
# --binauthz-evaluation-mode=DISABLED \
# --enable-managed-prometheus \
# --enable-shielded-nodes \
# --shielded-integrity-monitoring \
# --no-shielded-secure-boot

# gcloud beta container \
# --project "linkedlens-452503" clusters create "linkedlens-test" \
# --region "us-east1" \
# --tier "standard" \
# --no-enable-basic-auth \
# --cluster-version "1.31.6-gke.1064001" \
# --release-channel "regular" \
# --machine-type "e2-medium" \
# --image-type "COS_CONTAINERD" \
# --disk-type "pd-balanced" \
# --disk-size "100" \
# --metadata disable-legacy-endpoints=true \
# --max-pods-per-node "110" \
# --num-nodes "1" \
# --logging=SYSTEM,WORKLOAD \
# --monitoring=SYSTEM,STORAGE,POD,DEPLOYMENT,STATEFULSET,DAEMONSET,HPA,CADVISOR,KUBELET \
# --enable-ip-alias \
# --network "projects/linkedlens-452503/global/networks/default" \
# --subnetwork "projects/linkedlens-452503/regions/us-east1/subnetworks/default" \
# --no-enable-intra-node-visibility \
# --default-max-pods-per-node "110" \
# --enable-ip-access \
# --security-posture=standard \
# --workload-vulnerability-scanning=disabled \
# --no-enable-google-cloud-access \
# --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver \
# --enable-autoupgrade \
# --enable-autorepair \
# --max-surge-upgrade 1 \
# --max-unavailable-upgrade 0 \
# --binauthz-evaluation-mode=DISABLED \
# --enable-managed-prometheus \
# --workload-pool "linkedlens-452503.svc.id.goog" \
# --enable-shielded-nodes \
# --shielded-integrity-monitoring \
# --no-shielded-secure-boot \
# --node-locations "us-east1-b","us-east1-c","us-east1-d"

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