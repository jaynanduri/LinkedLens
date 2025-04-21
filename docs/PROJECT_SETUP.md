# Project Setup

This guide explains how to set up the project locally for development or testing.

## Instruction and Setup 
### Prerequisites

Make sure you have the following installed:

- **Python** ≥ 3.12  
- **pip** for package management  

## Getting Started

Follow the steps below to get the project up and running:

### 1. Clone the Repository

```bash
git clone https://github.com/jaynanduri/LinkedLens.git
cd LinkedLens
```

###  2. Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Required Packages
```bash
pip install -r requirements.txt
```

### 4. Set Up the Environment File

Create a .env file in the project root:
```bash
touch .env
```
Open the .env file and add all required keys and values, following the structure in .env_template:
```bash
KEY=<value>
```

Some values may require Google Cloud setup.
Please refer to [GCP Setup](/docs/GCP_Setup.md) Instructions for details.

Create HuggingFace API KEY

Create Pinecone API KEY [Pinecone Setup](/docs/ESSENTIAL_SERVICES_SETUP.md)


**Note:** `OPENAI_API_KEY` is optional

### 5. Run locally with Python

and then the following command to run the model pipeline:

```bash
cd model-development/src

python main.py
```
### 6. Run locally with docker
Alternatively, the pipeline can be run using the Dockerfile provided

```bash

cd model-development/src

docker build -t model-image:latest .

docker run -it -p 80:80 model-image:latest
```