# Pinecone Setup
  1. Sign Up
     - Go to [Pinecone](https://app.pinecone.io/) and create an account.
  2. Create/Rename Project
     - Navigate to the Projects section.
     - Rename the default project to `LinkedLens` (or create a new one with that name).
  3. Generate API Key
     - Open the `LinkedLens` project.
     - Under the Get Started section, click “Generate API Key”.
     - Copy the API key.
  4. Set Environment Variables
     - Add the following to your .env file 
     ```bash
     PINECONE_API_KEY=your-api-key-here
     ```

# GCP Setup for Data Pipelines

## Create GCP Project
*If you have already created a GCP project for this setup, you can skip this step.*
1. Go to the Google Cloud Console
2. In the top navigation bar, click on the project selector (next to the Google Cloud logo).
3. Click New Project.
4. Enter the following details:
    - Project Name: Choose a unique name for your project. `Name: LinkedLens`

    - Billing Account: Select an existing billing account or create a new one.

    - Organization & Location: If applicable, select your organization or leave it as "No organization".

5. Click Create. 


## Create Service Accounts

Create **two** service accounts:
- **Data Pipelines**: Create and save key `json`
- **Infrastructure Management**: `Editor` (to create Firestore DB, VM, and bucket)

### Steps to create service account and key
1. Go to the Google Cloud Console and select project.
2. Create Service Account
   - Navigate to Service Accounts. 
   - Create new Service Account > Enter name > Create and Continue 
3. Assign required roles:
   - Assign the following roles for **Data Pipelines account** - `Storage Object User`, `Cloud Datastore User`, `Log Writer`, `Eventarc Event Receiver`.
   - Assign `Editor` role for **Infrastructure Management**.

4. Download the service account key (JSON file).
   - Locate the newly created service account
   - Actions > Manage Keys > Add Key > JSON
   - Save the generated JSON securely
5. Store JSON file
   - Create a folder `credentials` inside `project-root/`
   - Place the JSON file in `credentials` folder with name `linkedlens-firestore-srvc-acc.json`

## Create [GCP Bucket](https://cloud.google.com/storage/docs/creating-buckets)
1. Go to Google Cloud Console > Cloud Storage > Buckets
2. Create Bucket:
    - Click Create
    - Enter Name
    - Add Region
    - Click Create
3. Create two buckets - `linkedlens_data` and `linkedlens-airflow-logs`

    

## Create [Firestore DB](https://firebase.google.com/docs/firestore/quickstart)
1. In the search bar at the top Google Console, type "Firestore" and select Firestore from the results.
2. Click Create Database.
3. Choose Native Mode (recommended for scalable queries).
4. Select a Cloud Firestore location closest to your users. (us-central1)
5. Click `Create Database`

### Add Composite Index
1. Navigate to the Firestore database you just created.
2. In the left panel, click on **Indexes**.
3. Select the **Composite** tab (default view).
4. Click **Create** Index and enter the following details:
    - **Collection ID**: `posts`
    - **Field 1**: `vectorized`
    - **Field 2**: `job_id`

## Create [VM Instance](https://cloud.google.com/compute/docs/create-linux-vm-instance) on Compute Engine

### Prerequisites Before Creating the VM

#### Generate an SSH Key on Your Local System
Before creating the VM, generate an SSH key on your local machine to allow secure access.

#### Configure Firewall Rules

| **Rule Name**         | **Direction** | **IP Ranges**   | **Protocols / Ports**   |
|-----------------------|--------------|-----------------|-------------------------|
| **allow-ssh**        | Ingress      | `0.0.0.0/0`     | `tcp:22`                |
| **airflow-port**     | Ingress      | `0.0.0.0/0`     | `tcp:8080, 9090`        |
| **allow-dns**        | Egress       | `0.0.0.0/0`     | `tcp:53, udp:53`        |
| **smtp-outbound-vm** | Egress       | `0.0.0.0/0`     | `tcp:587`               |


#### Steps to Add Firewall Rules
1. Open the Google Cloud Console.
2. In the search bar, type "VPC network" and select Firewall.
3. Click Create Firewall Rule and enter the required details:
    - Name: (e.g., allow-ssh, airflow-port)
    - Direction: Choose Ingress or Egress as needed.
    - IP Range: Enter 0.0.0.0/0.
    - Protocols & Ports: Specify the corresponding TCP/UDP ports from the table above.
4. Click Create.


### Create VM
1. Configure Machine Settings
    - Go to Compute Engine > VM Instances.
    - Click Create Instance.
    - Enter a Name for the VM.
    - Select the Region (choose the one closest to your location).
    - Machine Family: E2
    - Machine Type: Select Custom
    - Set vCPUs to 8 and Memory to 32GB.
2. Configure OS & Storage
    -In the left panel, click Configure OS & Storage
    - click Change.
    - Select the desired Operating System. (Debian-based)
    - Increase the disk size to 30GB (if deploying both DAGs on the same VM).

3. Configure Networking
    - Navigate to the Networking tab.
    - Check Allow HTTP and HTTPS traffic.
    - Network tags, add the following: `airflow-port`, `allow-dns`, `allow-ssh`, `http-server`, `https-server`, `smtp-outbound-vm`
    - Enable IP Forwarding.

4. Configure Observability & Security
Observability Tab:
    - Check Install Ops Agent for Monitoring and Logging.

5. Security Tab:
    - Under Access Scope, select Allow full access to all Cloud APIs.

6. Click Create
7. Add SSH Key
    - Edit the created VM and add the SSH key generated (your_key.pub)

8. Start the VM and SSH into the VM


#### Configure VM
- Verify that the ssh is added. If not create `.ssh` folder and add ssh in `authorized_keys` file.
- Install Docker on VM: Follow Docker installation guide: [Docker Docs](https://docs.docker.com/engine/install/debian/)
- Add your user to the Docker group to run Docker commands without `sudo`:
```bash
sudo usermod -aG docker $USER
```
- Restart the VM

  
6. Create Cloud Run Function
    - Cloud Run is used to trigger DAG runs on the Compute Engine.
    - Follow the [steps](../cloud-functions/functions/dag-trigger/README.md) to set up and run functions


7. Add Secrets to GitHub
    - Go to GitHub Repository
    - Navigate to Settings
    - Select `Secrets` under Security
    - Add New Secret
  Add all .env variables and the ones mentioned below:
  - `HOST_NAME`: VM name
  - `SERVER_IP`: Public IP of VM
  - `SERVER_USERNAME`: $USER
  - `SSH_PORT`: 22
  - `SERVER_KEY`: Private SSH Key