# Model Pipeline

The model pipeline is set up to process queries, retrieve relevant users posts, and repond to user queries. The pipeline receives a user's chat history at the API endpoint, and runs LangGraph workflow to generate an appropriate response. The pipeline utilizes the LLM `gemini-2.0-flash`.

![Model Pipeline flow](/images/model_pipeline.png)

## LangGraph Overview

1. Query Analyzer Node
    - Processes the user's chat history and either redirects the flow to retrieval using tool calling (`retrieval`) or directly responds if the query did not require any search (`generic`).
    - the retrieval tool receives rewritten query and the types of content to search for `job`, `user_post` or `recruiter_post`.
2. Retrieval Node
    - Generates embeddings for the rewritten query.
    - Executes the query against the vector store.
3. Augmentation Node
    - Filters and post-processses (enriches with metadata) the retrieved chunk for the final LLM call.
4. Final Response Node
    - Calls the LLM with the augmented context and the user query.


## Evaluation Strategy

The evaluaton of the model is done at two phases, before and after deployment. 

### Pre-Deployment Evaluations:
- We have test set targeted for each step (node) of the graph.
- These queries are executed against the graph, and evaluations are conducted accordingly.

### Post-Deployment Evaluations:
- LangSmith is used to log all intermediary traces of the model pipeline.
- Based on these logs, the evaluators, explained below, are run to evaluate the performance of the model in production.

### Evaluators (`model-development\eval\evaluators.py`) :
These evaluators are used to evaluate the performance of the responses provided by the LLM (post-deployment) checking for the following criterion:
- FaithfulnessLLMEval(): Evaluates whether the response remains faithful to the given context, identifying hallucinations or unsupported claims.
- CompletenessLLMEval(): Assesses whether the response fully utilizes the information provided in the context.
- RetrievalEvaluator(): Aggregating chunk-level scores into a mean relevance metric, offering a system-wide performance snapshot. This dual approach, assessing individual chunks and computing an average, balances precision and scalability, ensuring high-quality retrievals and consistent overall performance.

## Models Used
  - LLM: `gemini-1.5-pro`
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

## FastAPI Endpoint
  - Accepts a list of user messages.
  - Treats the latest message as the user query.
  - Executes the LangGraph workflow and responds with the final response together with retrieved documents and other metadata
  - Our [OpenwebUI deployment](/docs/) is calling this endpoint to get the response for the user query.