# Model Pipeline

The model pipeline is set up to process queries, retrieve relevant users posts, and repond to user queries. The pipeline receives a query at the API endpoint, and uses LangGraph to generate an appropriate response. The pipeline utilizes the LLM `gemini-1.5-pro`.

![Model Pipeline flow](/images/model_pipeline.png)

## LangGraph Overview

1. Query Analyzer Node
    - Processes the user query and rewrites it into a standalone query for the vector store.
    - Utilizes previous messages in the conversation for context.
    - Determines the query_type:
        - `generic` (does not require retrieval).
        - `retrieval` (requires retrieval).
    - Identifies the vector namespaces to be queried.
2. Branching Based on Query Type
    - If `query_type` is generic, the query is directed to the Final Response Node.
    - If `query_type` is retrieval, it is directed to the Retrieval Node.
3. Retrieval Node
    - Generates embeddings for the rewritten query.
    - Executes the query against the vector store.
4. Augmentation Node
    - Processes retrieved chunks and filters those meeting a threshold.
    - Retrieves all chunks from the same document to form a complete context.
5. Final Response Node
    - If `query_type` is generic, generates a general response.
    - If `query_type` is retrieval, generates a response based on the retrieved context.

## Models Used
  - LLM: gemini-1.5-pro
  - Embedding Model: sentence-transformers/all-MiniLM-L6-v2
  
## Deployment

The model pipeline is deployed to a Google Kubernetes Engine cluster. The workflow `deploy-to-gke.yml` makes use of the 

## Logging & Tracing
  - All steps are logged to GCP Cloud Logging.
  - LangSmith tracks each graph run, including input, output, and metadata.

## API Endpoint
  - FastAPI-based /invoke endpoint
      - Accepts a list of user messages.
      - Treats the latest message as the user query.
      - Constructs the state and executes the graph.
