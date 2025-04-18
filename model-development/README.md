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


<!-- # 
- query analyzer: Bind with tool(retrieval) :
- check query analyzer: if prev call was tool call: pass "retrieve" else return output
- retrieval tool 
- augmentation node.. 
- final respomse - case of  -->
## Evaluation Strategy

The evaluaton of the model is done at two phases, before and after deployment. 

### Pre-Deployment Evaluations:
- We have test queries designed for each step of the graph.
- These queries are executed against the graph, and evaluations are conducted accordingly.

### Post-Deployment Evaluations:
- LangSmith is used to log all traces of the model pipeline.
- Based on these logs, the evaluators, explained below, are run to evaluate the performance of the model.

### Evaluators (`model-development\eval\evaluators.py`) :
These evaluators are used to evaluate the performance of the responses provided by the LLM (post-deployment) checking for the following criterion:
- FaithfulnessLLMEval(): Evaluates whether the response remains faithful to the given context, identifying hallucinations or unsupported claims.
- CompletenessLLMEval(): Assesses whether the response fully utilizes the information provided in the context.
- RetrievalEvaluator(): Aggregating chunk-level scores into a mean relevance metric, offering a system-wide performance snapshot. This dual approach, assessing individual chunks and computing an average, balances precision and scalability, ensuring high-quality retrievals and consistent overall performance.

## Models Used
  - LLM: gemini-1.5-pro
  - Embedding Model: sentence-transformers/all-MiniLM-L6-v2
  
## Deployment

The model pipeline is deployed to a [Google Kubernetes Engine cluster](/docs/GKE-Setup.md). The workflow `deploy-to-gke.yml` makes use of the `Dockerfile`, `deployment.yaml`, and `service.yaml` to deploy the model pipeline with 3 replicas and a LoadBalancer service that exposes port `6000` externally as an API endpoint.

The model pipeline can be locally deployed by running the docker container with the following commands:

```
docker build -t model-image:latest .

docker run -it -p 80:80 model-image:latest
```

## Logging & Tracing
  - All steps are logged to GCP Cloud Logging.
  - LangSmith tracks each graph run, including input, output, and metadata.

## API Endpoint
  - FastAPI-based /invoke endpoint
      - Accepts a list of user messages.
      - Treats the latest message as the user query.
      - Constructs the state and executes the graph.