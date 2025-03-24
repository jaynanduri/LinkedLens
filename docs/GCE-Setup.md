## Running DAGs on Google Compute Engine
### Initial Setup

1. Create a GCP Project `Name: LinkedLens`
2. Create Service Accounts with roles:

    - **Data Processing**: `Cloud Datastore User`, `Storage Object User`. Create and save key `json`
    - **Infrastructure Management**: `Editor` (to create Firestore DB, VM, and bucket)

3. Create [Firestore DB](https://firebase.google.com/docs/firestore/quickstart)

4. Create [VM Instance](https://cloud.google.com/compute/docs/create-linux-vm-instance) on Compute Engine

    - Debian-based VM
    - 20GB persistent memory
    - Allow HTTP & HTTPS
    - Enable IP forwarding
    - Add firewall rules to allow:
        ```
        - **allow-ssh** (Ingress) → `tcp:22`  
        - **airflow-port** (Ingress) → `tcp:8080`  
        - **airflow-port** (Ingress) → `tcp:8080` and `tcp:9090`  
        - **allow-dns** (Egress) → `tcp:53, udp:53`  
        - **smtp-outbound-vm** (Egress) → `tcp:587`
        ```
    - Ensure network tags are assigned to the VM.
    - Install Docker on VM: Follow Docker installation guide: [Docker Docs](https://docs.docker.com/engine/install/debian/)

5. Create [GCS Bucket](https://cloud.google.com/storage/docs/creating-buckets):
    - Bucket Name: `linkedlens_data`
    - Purpose: Stored raw and preprocessed data.
      
6. Create Cloud Run Function
    - Cloud Run is used to trigger DAG runs on the Compute Engine.
    - Follow the [steps](gcp-deploy/functions/dag-trigger/README.md) to set up and run functions