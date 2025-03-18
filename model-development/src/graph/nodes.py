from graph.state import State
from logger import *
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any
from langchain.schema import HumanMessage, AIMessage
from clients.embedding_client import EmbeddingClient
from clients.pinecone_client import PineconeClient
from collections import defaultdict



class QueryAnalysis(BaseModel):
    standalone_query: str = Field(..., description="A rewritten, standalone query that is clear and self-contained.")
    query_type: str = Field(..., description="The type of the query: either 'generic' or 'retrieve'.")
    vector_namespace: List[str] = Field(
        ...,
        description="List of relevant namespaces chosen from ['user', 'job', 'user_post', 'recruiter_post']. If unsure, include all."
    )


@with_logging
def query_analyzer_node(state: State, chain)->dict:
  """
  Process the user query to generate a standalone query and set the query_type.
  In a real use case, this would call an LLM.
  """
  # Assuming a pair is two messages, take the last 6 messages.
  dialogue_msgs = [
      f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
      for msg in state["messages"]
      if isinstance(msg, (HumanMessage, AIMessage))
  ]
  dialogue_context = "\n".join(dialogue_msgs[-6:])
  query = state["query"]
  
  try:
        # Run the LLM chain with the conversation context and latest query.
        result: QueryAnalysis = chain.invoke({"conversation":dialogue_context, "query":query})
        parsed_obj = result['parsed']
        output = {
            "standalone_query": parsed_obj.standalone_query,
            "query_type": parsed_obj.query_type,
            "vector_namespace": parsed_obj.vector_namespace
        }
  except Exception as e:
      output = {
          "standalone_query": query,
          "query_type": "retrieve",
          "vector_namespace": ["user", "job", "user_post", "recruiter_post"]
      }

  return output


@with_logging
def check_query_type(state: State) -> Literal['retrieve', 'generic']:
    """
    Determines the branch to follow based on the query type.

    Args:
        state (State): The current state of the conversation.

    Returns:
        Literal['retrieve', 'generic']: The branch to follow.
    """
    return 'retrieve' if state.get('query_type', '').lower() == 'retrieve' else 'generic'



@with_logging
def retrieval_node(
    state: State,
    embedding_client: EmbeddingClient,
    pinecone_client: PineconeClient,
) -> Dict:
    """
    Retrieves relevant documents based on the standalone query.

    Args:
        state (State): The current state of the conversation.
        embedding_client (EmbeddingClient): Client to generate embeddings from text.
        pinecone_client (PineconeClient): Client to query the Pinecone index.

    Returns:
        Dict: Retrieved documents with metadata.
    """
    # Generate the embedding for the standalone query
    query_embedding = embedding_client.generate_embedding(state['standalone_query'])

    retrieved_results = []
    for namespace in state['vector_namespace']:
        # Query the Pinecone index for the current namespace
        query_response = pinecone_client.query_similar(
            query_vector=query_embedding,
            top_k=10,
            namespace=namespace,
            include_metadata=True,
            include_values=False
        )
        # Process the response: assuming each match has metadata with a "text" field.
        for match in query_response.get('matches', []):
            if match:
                match_dict = {
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match['metadata']
                }
                retrieved_results.append(match_dict)
    return {'retrieved_docs': retrieved_results}

def process_retrieved_docs(matches: List[dict]) -> Dict[str, dict]:
    """
    Processes a list of Pinecone matches and aggregates them by unique Firestore ID.
    For each unique Firestore ID (within its namespace):
      - Groups the retrieved chunks.
      - Sorts chunks by their "chunk" number.
      - Combines the 'raw_data' fields.
      - Cleans metadata based on namespace rules.
          * For 'job': remove "chunk", "total_chunks", "createdAt", "updatedAt", "ttl", and remove "author" if blank.
          * For 'user_post' and 'recruiter_post': similar cleanup (author remains).
          * For 'user': remove "createdAt" and "updatedAt".
      - Extracts the creation date (if available) and converts it to a YYYY-MM-DD string.
      - Generates a URL based on the namespace.
    
    Returns:
        A dictionary where each key is a Firestore ID and its value is the processed document data.
    """
    # Group matches by (namespace, firestoreId)
    unique_ids = defaultdict(list)
    for doc in matches:
        metadata = doc.get("metadata", {})
        firestore_id = metadata.get("firestoreId")
        namespace = metadata.get("docType")
        if firestore_id and namespace:
            if firestore_id not in unique_ids[namespace]:
                unique_ids[namespace].append(firestore_id)

    base_urls = {
        "job": "https://yourdomain.com/job",
        "user_post": "https://yourdomain.com/post",
        "recruiter_post": "https://yourdomain.com/post",
        "user": "https://yourdomain.com/user"
    }
    
    final_docs = {}

    for doc in matches:
        metadata = doc.get("metadata", {})
        namespace = metadata.get("docType")
        firestore_id = metadata.get("firestoreId")
        if not (firestore_id and namespace):
            continue
        
        # If this is the first chunk seen for this Firestore ID, create a new entry.
        if firestore_id not in final_docs:
            base_score = doc.get("score", 0)
            combined_raw_text = doc.get("metadata").get("raw_data", "")
            # Copy metadata and remove unwanted fields.
            doc_metadata = dict(metadata)
            for field in ["chunk", "total_chunks", "createdAt", "updatedAt", "ttl"]:
                doc_metadata.pop(field, None)
            # For 'job' namespace, remove 'author' if it's blank.
            if namespace == "job" and not doc_metadata.get("author"):
                doc_metadata.pop("author", None)
            # # Convert creation timestamp to a date string, if available.
            # created_at = metadata.get("createdAt")
            # date_str = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d") if created_at else "N/A"
            # Generate URL.
            base_url = base_urls.get(namespace, "https://yourdomain.com")
            url = f"{base_url}/{firestore_id}"
            
            final_docs[firestore_id] = {
                "namespace": namespace,
                "score": base_score,
                **doc_metadata,
                "combined_raw_text": combined_raw_text,
                "url": url,
            }
        else:
            # If the Firestore ID already exists, update the entry.
            entry = final_docs[firestore_id]
            new_score = doc.get("score", 0)
            # Update the score if the new chunk has a higher score.
            if new_score > entry["score"]:
                entry["score"] = new_score
            additional_text = doc.get("metadata", {}).get("raw_data", "")
            if additional_text:
                entry["combined_raw_text"] += " " + additional_text
    
    return final_docs

def format_context_for_llm(processed_docs: Dict[str, dict], max_docs: int = 10) -> str:
    """
    Formats the processed documents into a string for use as context in an LLM prompt.
    
    The final format for each document is:
    
    [Metadata] Source: <namespace>, Date: <date>, Relevance: <score>
    [Content] <combined raw text>
    
    Only the top max_docs documents (sorted by descending score) are included.
    """
    # Sort documents by score (highest first) and take the top max_docs.
    sorted_docs = sorted(processed_docs.values(), key=lambda d: d.get("score", 0), reverse=True)[:max_docs]
    
    context_lines = []
    for doc in sorted_docs:
        # Optionally truncate raw text to control token usage.
        raw_text = doc["combined_raw_text"]
        line = (
            f"[Metadata] Source: {doc['url']}, Relevance: {doc['score']:.2f}\n"
            f"[Content] {raw_text}\n"
        )

        context_lines.append(line)
    
    return "\n".join(context_lines)

@with_logging
def augmentation_node(state: State):
    """
    Augments retrieved docs and prepares the final context used to generate response.
    """
    cleaned_docs = process_retrieved_docs(state['retrieved_docs'])
    final_context = format_context_for_llm(cleaned_docs, 10)
    return {"final_context": final_context}


@with_logging
def final_response_node(state: State, chain):
    """
    Final node that produces the assistant response.
    """
    response = chain.invoke({"context": state['final_context'], "input": state['query']}).content
    if response:
        state["messages"].append(AIMessage(content=response))


    return {"response": response}