# RAG App Backend

This section explains how the backend of the Retrieval-Augmented Generation (RAG) application functions.

# Model Pipeline

The model pipeline is set up to process queries, retrieve relevant users posts, and repond to user queries. The pipeline receives a user's chat history at the API endpoint, and runs LangGraph workflow to generate an appropriate response. The pipeline utilizes the LLM `gemini-2.0-flash`.

![Model Pipeline flow](/images/model_pipeline.png)

## LangGraph Overview

1. Query Analyzer Node
    - Processes the user's chat history and either redirects the flow to retrieval using tool calling (`retrieval`) or directly responds if the query did not require any search (`generic`).
    - the retrieval tool receives rewritten query and the types of content to search for `job`, `user_post` or `recruiter_post`.
2. Retrieval Node
    - Generates embeddings for the rewritten query.
    - Executes the query against the vector store, ensuring that only relevant chunks that have not yet expired (based on their TTL) are retrieved.
3. Augmentation Node
    - Filters and post-processses (enriches with metadata) the retrieved chunk for the final LLM call.
4. Final Response Node
    - Calls the LLM with the augmented context and the user query.


## Evaluation Strategy

Evaluation is an ongoing part of the model lifecycle and is carried out in three stages—real-time, pre-deployment, and post-deployment. Each stage plays a role in ensuring the quality and reliability of the system.

## Evaluation Metrics
We focus on three core metrics to assess the effectiveness of our RAG pipeline:

### Response Relevance: 
Measures how well the model’s response aligns with the user’s query. Higher scores mean the response is more directly useful and complete.

### Faithfulness: 
Checks whether the response is factually consistent with the retrieved context. It ranges from 0 to 1, where 1 indicates high factual accuracy.

### Context Relevance: 
Evaluates how relevant each retrieved chunk is to the rewritten query. We compute chunk-level scores and aggregate them to get an overall measure of retrieval quality. This provides both fine-grained and system-level insights.

We use LLM-as-a-judge for high-accuracy evaluations through platforms like **RAGAS** and **EvidentlyAI**.


## Evaluation Stages
### Real-Time Evaluation:
During live queries, we compute cosine similarity as a lightweight proxy for relevance and consistency, allowing us to evaluate performance without invoking an LLM. This includes:
- Response vs. Query: To approximate response relevance
- Context vs. Query: To gauge context relevance
- Response vs. Context: To estimate faithfulness


### Pre-Evaluation (CI Testing):
As part of our CI pipeline, we run synthetic tests on sample documents. Using RAGAS `TestGenerator`, we create test queries, pass them through the model, and evaluate the results. We’ve set strict thresholds for each metric, and the deployment proceeds only if all metrics meet the defined standards, ensuring the model maintains a high level of quality before going live.

### Post-Evaluation (Daily Batch):
A scheduled Cloud Run job runs daily at 1 AM to evaluate conversations from the previous day. This helps monitor performance trends, track regressions, and decide when adjustments or prompt tuning may be needed.

To set this up, we use the script located at `model-development/eval/setup.sh`. This script:
- Builds the evaluation container
- Pushes it to Artifact Registry
- Creates the Cloud Run job
- Schedules it to run daily

Before running the script, make sure to:

Add the required secrets to Secret Manager:
`LANGSMITH_API_KEY`, `HF_TOKEN`, `GEMINI_API_KEY`

Ensure the `.env` file is properly configured

Update script variables only if necessary

Run Script:

```bash
cd model-development/eval
./setup.sh
```

## Models Used
  - LLM: `gemini-2.0-flash`
  - Embedding Model: `sentence-transformers/all-MiniLM-L6-v2`
  
## Deployment

The model pipeline is deployed to a [Google Kubernetes Engine cluster](/docs/GKE-Setup.md). The workflow `deploy-to-gke.yml` makes use of the `Dockerfile`, `deployment.yaml`, and `service.yaml` to deploy the model pipeline with 3 replicas and a LoadBalancer service that exposes port `6000` externally as an API endpoint. The CD workflow [deploy-to-gke.yaml](/.github/workflows/deploy-to-gke.yml) is used to [automate deployment](/docs/CI_CD_Workflows.md) to the GKE cluster. 

The model pipeline can be locally deployed by running the docker container with the following commands:

```
docker build -t model-image:latest .

docker run -it -p 80:80 model-image:latest
```

## Logging & Tracing
  - All steps are logged to GCP Cloud Logging. [Ref](/monitoring/README.md)
  - LangSmith tracks each graph run, including input, output, and metadata.
  - Monitoring is done using Grafana. 

## FastAPI Endpoint

We expose two FastAPI endpoints to support health checks and user query processing.

### `GET /health`
This endpoint is used for health checks to confirm that the service is up and running.

Response
```bash
{ "status": "healthy" }
```

### POST /invoke
This is the primary endpoint for processing user queries via our LangGraph-powered model pipeline.

**Functionality:**
  - Accepts a list of chat messages, where the latest message is treated as the active user query.
  - Executes the LangGraph workflow, which includes query analysis, document retrieval, augmentation, and final response generation.
  - Returns the model's response along with retrieved documents and relevant metadata.
  - Our [OpenwebUI deployment](/docs/) is calling this endpoint to get the response for the user query.

**Request Input:**

The /invoke endpoint expects a JSON payload containing user, session, and chat identifiers, along with a list of chat messages. The latest message in the list is treated as the active user query.

```json
{
  "user_id": "<user_id>",
  "session_id": "<session_id>",
  "chat_id": "<chat_id>",
  "messages": [
    { "type": "user", "content": "What roles are open for data scientists?" }
  ]
}
```
**Important:**
- The last message in the messages list must be of type "user" as it represents the current query.
- The messages should reflect the full conversation history in alternating sequence of "user" and "ai" types, starting with a "user" message. This ensures the model can follow the context of the conversation accurately.

Example:
```json
"messages": [
  { "type": "user", "content": "Hi, I'm looking for job opportunities." },
  { "type": "ai", "content": "Sure! Are you interested in any specific role or location?" },
  { "type": "user", "content": "Yes, data scientist roles in California." }
]
```
After receiving the LLM response, append it as an "ai" message to maintain this sequence for the next request. Only when running the backend separately.

**Response Output:**
```json
{
  "query": "What roles are open for data scientists?",
  "retrieved_docs": [/* list of relevant retrieved chunks */],
  "response": "Here are some current openings for data scientists at various companies..."
}
```