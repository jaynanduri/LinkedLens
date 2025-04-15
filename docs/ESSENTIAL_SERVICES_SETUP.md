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
# Docker and Docker Compose Setup

> 🛠️ **Note:** Docker is only required if you plan to run the **Data Pipelines locally**. It is not needed for cloud-based deployments.

**Install Docker and Docker Compose**  
   Follow the official Docker installation guide for your operating system:  
   [Install Docker Engine](https://docs.docker.com/engine/install/)