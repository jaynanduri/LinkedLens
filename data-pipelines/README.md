# Data Preprocessing and Generation Pipeline

### Overview 
We process a [Kaggle dataset](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) containing job postings, preprocess the data, and store it in a GCP bucket. Using this preprocessed data, we generate synthetic user profiles, recruiter job posts, and interview experience posts using LLM APIs. The generated data is validated using Pydantic before loading it into Firestore DB.