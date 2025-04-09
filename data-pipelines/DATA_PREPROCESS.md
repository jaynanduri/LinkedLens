# Data Preprocessing and Data Versioning

This section explains how to preprocess Kaggle job postings data, version it using DVC, and upload it to a GCP bucket. It also outlines how to pull the data from GCP and upload it for use in data pipelines.

## 1. Prerequisites
### Credentials
You will need a GCP Service Account to authenticate and interact with the GCP bucket and FirestoreDB, Cloud logging and Trigger events.

### Steps to Create Service Account and Key:
1. Go to the Google Cloud Console and select project.
2. Create Service Account
   - Navigate to Service Accounts. 
   - Create new Service Account > Enter name > Create and Continue 
3. Assign required roles:
   - Assign the following roles - `Storage Object User`, `Cloud Datastore User`, `Log Writer`, `Eventarc Event Receiver`. 

4. Download the service account key (JSON file).
   - Locate the newly created service account
   - Actions > Manage Keys > Add Key > JSON
   - Save the generated JSON securely
5. Store JSON file
   - Create a folder `credentials` inside `project-root/data-pipelines/`
   - Place the JSON file in `credentials` folder with name `linkedlens-firestore-srvc-acc.json`

## Buckets
  1. Go to Google Cloud Console > Cloud Storage > Buckets
  2. Create Bucket:
     - Click Create
     - Enter Name
     - Add Region
     - Click Create
  3. Create two buckets - `linkedlens_data` and `linkedlens-airflow-logs`

## 2. Data Preprocessing
The `preprocessing.py` script is responsible for cleaning and preparing the data. It performs the following tasks:

  - Downloads the [Kaggle dataset](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings).
  - Cleans the data files as needed.
  - Filters for technical roles/jobs, ensuring that only relevant positions are included in the final dataset.
  - Stores the cleaned data in the local directory `project-root/data-pipelines/data/`.
  ### Output Folder Structure
```bash
  data/
  |___ raw_data/           # Original dataset
  |___ preprocessed_data/  # Preprocessed data
  |___ filtered_data/      # Data filtered to include only technical roles/jobs
```

## 3. DVC
We use DVC (Data Version Control) to track and version our data. Since we are pushing the data to a private GCP bucket, follow the steps below to version the data.

**Note:** The GCP bucket is not public. You need to configure access for your GCP project to allow data pulling.

#### Initialize DVC in your project directory:
```bash
dvc init
dvc config core.autostage true # Automatically stages files added with dvc add
```

#### Configure Remote Storage
Add a remote storage location (replace with your bucket name and path):

```bash
dvc remote add -d myremote gs://<mybucket>/<path>
```

#### Set Up Credentials
Modify the remote configuration to specify the path to your service account credentials file:

```bash
dvc remote modify --local myremote credentialpath 'path/to/project-XXX.json'
```

#### Add Your Data
```bash
dvc add data-pipelines/data/
```

#### Commit and Push Changes
```bash
git commit -m "Add data tracking with dvc"
git push origin main
```

#### Push Data to Remote
Finally, push your data to the configured remote storage:
```bash
dvc push
```

#### To Pull Data
If you only need to retrieve the data and the GCP bucket is accessible
```bash
dvc pull
```

## 4. Upload to GCP
The `upload_to_gcp.py` script uploads the processed data to the GCP bucket, making it available for use by downstream pipelines. The data is uploaded with the same structure as the output of the data preprocessing step to the `linkedlens_data` GCP bucket.

**Note:** After the data has been successfully uploaded, the script will delete the local data folder 