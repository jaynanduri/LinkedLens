# gcloud compute instances create test \
#     --project=linkedlens \
#     --zone=us-central1-c \
#     --machine-type=e2-custom-8-32768 \
#     --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
#     --metadata=enable-osconfig=TRUE \
#     --can-ip-forward \
#     --maintenance-policy=MIGRATE \
#     --provisioning-model=STANDARD \
#     --service-account=1099036781287-compute@developer.gserviceaccount.com \
#     --scopes=https://www.googleapis.com/auth/cloud-platform \
#     --tags=airflow-port,allow-dns,allow-ssh,http-server,https-server,smtp-outbound-vm \
#     --create-disk=auto-delete=yes,boot=yes,device-name=test,disk-resource-policy=projects/linkedlens/regions/us-central1/resourcePolicies/default-schedule-1,image=projects/debian-cloud/global/images/debian-12-bookworm-v20250415,mode=rw,size=100,type=pd-balanced \
#     --no-shielded-secure-boot \
#     --shielded-vtpm \
#     --shielded-integrity-monitoring \
#     --labels=goog-ops-agent-policy=v2-x86-template-1-4-0,goog-ec-src=vm_add-gcloud \
#     --reservation-affinity=any \
# && \
# printf 'agentsRule:\n  packageState: installed\n  version: latest\ninstanceFilter:\n  inclusionLabels:\n  - labels:\n      goog-ops-agent-policy: v2-x86-template-1-4-0\n' > config.yaml \
# && \
# gcloud compute instances ops-agents policies create goog-ops-agent-v2-x86-template-1-4-0-us-central1-c \
#     --project=linkedlens \
#     --zone=us-central1-c \
#     --file=config.yaml

#!/bin/bash

PROJECT_ID="linkedlens"
ZONE="us-central1-c"
VM_NAME="test"
MACHINE_TYPE="e2-custom-8-32768"
DISK_SIZE=100
IMAGE="projects/debian-cloud/global/images/debian-12-bookworm-v20250415"
DISK_POLICY="projects/linkedlens/regions/us-central1/resourcePolicies/default-schedule-1"
SERVICE_ACCOUNT="1099036781287-compute@developer.gserviceaccount.com"
SSH_KEY_PATH="$HOME/.ssh/gcp_vm_key.pub"
OPS_AGENT_POLICY="v2-x86-template-1-4-0"


echo "Creating firewall rules..."


# gcloud compute firewall-rules create allow-ssh-test \
#   --allow tcp:22 \
#   --direction=INGRESS \
#   --source-ranges=0.0.0.0/0 \
#   --target-tags=allow-ssh \
#   --project="$PROJECT_ID" || true

# gcloud compute firewall-rules create airflow-port-test \
#   --allow tcp:8080,tcp:9090 \
#   --direction=INGRESS \
#   --source-ranges=0.0.0.0/0 \
#   --target-tags=airflow-port \
#   --project="$PROJECT_ID" || true

# gcloud compute firewall-rules create allow-dns-test \
#   --allow tcp:53,udp:53 \
#   --direction=EGRESS \
#   --destination-ranges=0.0.0.0/0 \
#   --target-tags=allow-dns \
#   --project="$PROJECT_ID" || true

# gcloud compute firewall-rules create smtp-outbound-vm-test \
#   --allow tcp:587 \
#   --direction=EGRESS \
#   --destination-ranges=0.0.0.0/0 \
#   --target-tags=smtp-outbound-vm \
#   --project="$PROJECT_ID" || true

echo "Creating VM instance..."

gcloud compute instances create "$VM_NAME" \
  --project="$PROJECT_ID" \
  --zone="$ZONE" \
  --machine-type="$MACHINE_TYPE" \
  --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
  --metadata=enable-osconfig=TRUE \
  --can-ip-forward \
  --maintenance-policy=MIGRATE \
  --provisioning-model=STANDARD \
  --service-account="$SERVICE_ACCOUNT" \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --tags=airflow-port-test,allow-dns-test,allow-ssh-test,http-server,https-server,smtp-outbound-vm-test \
  --create-disk=auto-delete=yes,boot=yes,device-name="$VM_NAME",disk-resource-policy="$DISK_POLICY",image="$IMAGE",mode=rw,size="$DISK_SIZE",type=pd-balanced \
  --no-shielded-secure-boot \
  --shielded-vtpm \
  --shielded-integrity-monitoring \
  --labels=goog-ops-agent-policy=v2-x86-template-1-4-0,goog-ec-src=vm_add-script \
  --reservation-affinity=any \
  --metadata-from-file=ssh-keys="$SSH_KEY_PATH" \
  --metadata-from-file=startup-script=startup_script.sh 


# === CREATE OPS AGENT POLICY ===
# echo "Creating Ops Agent Policy..."

# printf 'agentsRule:\n  packageState: installed\n  version: latest\ninstanceFilter:\n  inclusionLabels:\n  - labels:\n      goog-ops-agent-policy: v2-x86-template-1-4-0\n' > config.yaml \
# && \
# gcloud compute instances ops-agents policies create goog-ops-agent-v2-x86-template-1-4-0-us-central1-c \
#     --project=linkedlens \
#     --zone=us-central1-c \
#     --file=config.yaml

# cat <<EOF > config.yaml
# agentsRule:
#   packageState: installed
#   version: latest
# instanceFilter:
#   inclusionLabels:
#   - labels:
#       goog-ops-agent-policy: $OPS_AGENT_POLICY
# EOF

# gcloud compute instances ops-agents policies update goog-ops-agent-${OPS_AGENT_POLICY}-${ZONE} \
#   --project="$PROJECT_ID" \
#   --zone="$ZONE" \
#   --file=config.yaml || true

echo "🔁 Restarting VM to apply Docker group changes..."
gcloud compute instances reset "$VM_NAME" --zone "$ZONE"

# === GET EXTERNAL IP ===
VM_IP=$(gcloud compute instances describe "$VM_NAME" \
  --zone="$ZONE" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "✅ VM '$VM_NAME' created successfully!"
echo "🌐 External IP: $VM_IP"