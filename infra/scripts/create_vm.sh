#!/bin/bash

PROJECT_ID="linkedlens"
ZONE="us-central1-c"
VM_NAME="test"
MACHINE_TYPE="e2-custom-8-32768"
DISK_SIZE=100
IMAGE="projects/debian-cloud/global/images/debian-12-bookworm-v20250415"
DISK_POLICY="projects/linkedlens/regions/us-central1/resourcePolicies/default-schedule-1"
SERVICE_ACCOUNT="1099036781287-compute@developer.gserviceaccount.com"
SSH_KEY_PATH="$HOME/.ssh/gcp_vm_key.pub" # modify path as needed
OPS_AGENT_POLICY="v2-x86-template-1-4-0"
POLICY_NAME="goog-ops-agent-${OPS_AGENT_POLICY}-${ZONE}"


echo "Creating firewall rules..."


declare -A FIREWALL_RULES=(
  ["allow-ssh-test"]="--allow tcp:22 --direction=INGRESS --source-ranges=0.0.0.0/0 --target-tags=allow-ssh-test"
  ["airflow-port-test"]="--allow tcp:8080,tcp:9090 --direction=INGRESS --source-ranges=0.0.0.0/0 --target-tags=airflow-port-test"
  ["allow-dns-test"]="--allow tcp:53,udp:53 --direction=EGRESS --destination-ranges=0.0.0.0/0 --target-tags=allow-dns-test"
  ["smtp-outbound-vm-test"]="--allow tcp:587 --direction=EGRESS --destination-ranges=0.0.0.0/0 --target-tags=smtp-outbound-vm-test"
)

for RULE_NAME in "${!FIREWALL_RULES[@]}"; do
  echo ""
  if ! gcloud compute firewall-rules describe "$RULE_NAME" --project="$PROJECT_ID" &> /dev/null; then
    echo "Creating firewall rule: $RULE_NAME"
    gcloud compute firewall-rules create "$RULE_NAME" ${FIREWALL_RULES[$RULE_NAME]} --project="$PROJECT_ID"
  else
    echo "Firewall rule already exists: $RULE_NAME — skipping."
  fi
done

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
  --labels=goog-ops-agent-policy=$OPS_AGENT_POLICY,goog-ec-src=vm_add-script \
  --reservation-affinity=any \
  --metadata-from-file=ssh-keys="$SSH_KEY_PATH" \
  --metadata-from-file=startup-script=startup_script.sh 


# === CREATE OPS AGENT POLICY ===
if ! gcloud compute instances ops-agents policies describe "$POLICY_NAME" \
    --zone="$ZONE" \
    --project="$PROJECT_ID" &> /dev/null; then
  echo "🔧 Ops Agent Policy not found. Creating..."

  printf 'agentsRule:\n  packageState: installed\n  version: latest\ninstanceFilter:\n  inclusionLabels:\n  - labels:\n      goog-ops-agent-policy: v2-x86-template-1-4-0\n' > config.yaml \
  && \
  gcloud compute instances ops-agents policies create $POLICY_NAME \
      --project=linkedlens \
      --zone=us-central1-c \
      --file=config.yaml

  gcloud compute instances ops-agents policies update goog-ops-agent-${OPS_AGENT_POLICY}-${ZONE} \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --file=config.yaml || true
else
  echo "✅ Ops Agent Policy already exists: $POLICY_NAME"
fi

echo "🔁 Restarting VM to apply Docker group changes..."
gcloud compute instances reset "$VM_NAME" --zone "$ZONE"

# === GET EXTERNAL IP ===
VM_IP=$(gcloud compute instances describe "$VM_NAME" \
  --zone="$ZONE" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "✅ VM '$VM_NAME' created successfully!"
echo "🌐 External IP: $VM_IP"