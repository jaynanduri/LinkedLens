from graph.state import State
from logger import logger, with_logging
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any
from langchain.schema import HumanMessage, AIMessage
from clients.embedding_client import EmbeddingClient
from clients.pinecone_client import PineconeClient
from collections import defaultdict
from datetime import datetime, timezone
from langsmith import traceable
from config.settings import settings

class QueryAnalysis(BaseModel):
    standalone_query: str = Field(..., description="A rewritten, standalone query that is clear and self-contained.")
    query_type: str = Field(..., description="The type of the query: either 'generic' or 'retrieve'.")
    vector_namespace: List[str] = Field(
        ...,
        description="List of relevant namespaces chosen from ['job', 'user_post', 'recruiter_post']. If unsure, include all."
    )


@with_logging
@traceable
def query_analyzer_node(state: State, chain)->dict:
  """
  Process the user query to generate a standalone query and set the query_type.
  In a real use case, this would call an LLM.
  """
  # Assuming a pair is two messages, take the last 6 messages.
  dialogue_msgs = [
      f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
      for msg in state["messages"][-6:]
      if isinstance(msg, (HumanMessage, AIMessage))
  ]
  dialogue_context = "\n".join(dialogue_msgs)
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
@traceable
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
    current_time = int(datetime.now(timezone.utc).timestamp())

    for namespace in state['vector_namespace']:
        filter_conditions = {"ttl": {"$gt": current_time}} if namespace!='user' else {}
        # Query the Pinecone index for the current namespace
        query_response = pinecone_client.query_similar(
            query_vector=query_embedding,
            top_k=10,
            namespace=namespace,
            filter=filter_conditions,
            include_metadata=True,
            include_values=False
        )
        # Process the response: assuming each match has metadata with a "text" field.
        threshold = settings.pinecone.namesapce_threshold.get(namespace, 0)
        for match in query_response.get('matches', []):
            if match and match.get("score", 0) >= threshold:
                match_dict = {
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match['metadata']
                }
                if match_dict:
                    retrieved_results.append(match_dict)
    return {'retrieved_docs': retrieved_results}

# @traceable
# def fetch_complete_doc_text(matches: List[dict], pinecone_client: PineconeClient)-> Dict[str, str]:
#     """
#     Fetch all chunks for each retrieved doc and returns the complete raw_data of each doc.
#     """
#     # extract all firestorIds and total #chunks of the doc
#     unique_ids = defaultdict(list)
#     for doc in matches:
#         metadata = doc.get("metadata", {})
#         firestore_id = metadata.get("firestoreId")
#         total_chunks = int(metadata.get("total_chunks"))
#         namespace = metadata.get("docType")
#         unique_ids[namespace].append((firestore_id, total_chunks))

#     # prepare list of vector ids for all chunks of each doc
#     ns_vector_ids = {}
#     for namespace, ids in unique_ids.items():
#       vector_ids = set()
#       for firestoreId, total_chunks in ids:
#         for i in range(1, total_chunks + 1):
#           vector_ids.add(f"{firestoreId}_chunk_{i}")
#       ns_vector_ids[namespace] = list(vector_ids)

#     # Fetch all chunks for each doc and extract chunk number and raw_data
#     all_docs_dict = {}
#     for namespace, vector_ids in ns_vector_ids.items():
#         response = pinecone_client.fetch_by_vector_ids(vector_id_list=vector_ids, namespace=namespace)
#         for vector_id, vector_obj in response.vectors.items():
#             metadata = vector_obj.metadata
#             firestore_id = metadata.get("firestoreId")
#             chunk_id = int(metadata.get("chunk"))
#             raw_text = metadata.get("raw_data")
            
#             if firestore_id not in all_docs_dict:
#                 all_docs_dict[firestore_id] = []
            
#             all_docs_dict[firestore_id].append((chunk_id, raw_text))
    
#     # Sort the chunks in order adn combine the raw_data for each doc
#     for firestore_id in all_docs_dict:
#         all_docs_dict[firestore_id].sort(key=lambda x: x[0])
#         final_text = " ".join(text for _, text in all_docs_dict[firestore_id])
#         all_docs_dict[firestore_id] = final_text
#     return all_docs_dict

# @traceable
# def process_retrieved_docs(matches: List[dict], pinecone_client: PineconeClient) -> Dict[str, dict]:
#     """
#     Processes a list of Pinecone matches and aggregates them by unique Firestore ID.
#     For each unique Firestore ID (within its namespace):
#       - Groups the retrieved chunks.
#       - Sorts chunks by their "chunk" number.
#       - Combines the 'raw_data' fields.
#       - Cleans metadata based on namespace rules.
#           * For 'job': remove "chunk", "total_chunks", "createdAt", "updatedAt", "ttl", and remove "author" if blank.
#           * For 'user_post' and 'recruiter_post': similar cleanup (author remains).
#           * For 'user': remove "createdAt" and "updatedAt".
#       - Extracts the creation date (if available) and converts it to a YYYY-MM-DD string.
#       - Generates a URL based on the namespace.
    
#     Returns:
#         A dictionary where each key is a Firestore ID and its value is the processed document data.
#     """
#     final_doc_text = fetch_complete_doc_text(matches, pinecone_client)
    
#     final_docs = {}

#     for doc in matches:
#         metadata = doc.get("metadata", {})
#         namespace = metadata.get("docType")
#         firestore_id = metadata.get("firestoreId")
#         if not (firestore_id and namespace):
#             continue
        
#         # If this is the first chunk seen for this Firestore ID, create a new entry.
#         if firestore_id not in final_docs:
#             base_score = doc.get("score", 0)
#             combined_raw_text = final_doc_text.get(firestore_id, "")
#             # Copy metadata and remove unwanted fields.
#             doc_metadata = dict(metadata)
#             for field in ["chunk", "total_chunks", "createdAt", "updatedAt", "ttl", "firestoreId"]:
#                 doc_metadata.pop(field, None)
#             # For 'job' namespace, remove 'author' if it's blank. - check
#             if namespace == "job" and not doc_metadata.get("author"):
#                 doc_metadata.pop("author", None)
#             # # Convert creation timestamp to a date string, if available.
#             # created_at = metadata.get("createdAt")
#             # date_str = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d") if created_at else "N/A"
#             # Generate URL.
#             base_url = settings.NAMESPACE_URLS.get(namespace)
#             url = f"{base_url}/{firestore_id}"
            
#             final_docs[firestore_id] = {
#                 "score": base_score,
#                 **doc_metadata,
#                 "combined_raw_text": combined_raw_text,
#                 "url": url,
#             }
#         else:
#             # If the Firestore ID already exists, update the entry.
#             entry = final_docs[firestore_id]
#             new_score = doc.get("score", 0)
#             # Update the score if the new chunk has a higher score.
#             if new_score > entry["score"]:
#                 entry["score"] = new_score
#     return final_docs

@traceable
def format_context_for_llm(matches: List[Dict], max_docs: int = 20) -> str:
    """
    Formats the processed documents into a string for use as context in an LLM prompt.
    
    The final format for each document is:
    
    [Metadata] Source: <namespace>, Date: <date>, Relevance: <score>
    [Content] <combined raw text>
    
    Only the top max_docs documents (sorted by descending score) are included.
    """
    
    context_lines = []
    for doc in matches:
        if len(context_lines) >= max_docs:
            break
        metadata = doc.get("metadata", {})
        namespace = metadata.get("docType")
        firestore_id = metadata.get("firestoreId")
        raw_text = metadata.get("raw_data")
        # Extract Metadata based on type
        doc_metadata = ""
        if namespace == "job":
            # company_name, location, title
            location = metadata.get("location", "")
            company_name = metadata.get("company_name", "")
            title = metadata.get("title", "")
            if company_name:
                doc_metadata += f"Company Name: {company_name}, "
            if title:
                doc_metadata += f"Title: {title}, "
            if location:
                doc_metadata += f"Location: {location}, "

        elif namespace == "user_post" or namespace == "recruiter_post":
            # Author id-> url
            author = metadata.get("author", "")
            # job id if exists
            job_id = metadata.get("job_id", "")
            if author:
                base_url = settings.NAMESPACE_URLS.get("user")
                author_url = f"{base_url}/{author}"
                doc_metadata += f"Author Profile URL: {author_url}, "
            if job_id:
                base_url = settings.NAMESPACE_URLS.get("job")
                job_url = f"{base_url}/{job_id}"
                doc_metadata += f"Job URL: {job_url}, "
        else:
            # user company name, user type
            company_name = metadata.get("company_name", "")
            user_type = metadata.get("user_type", "")
            if company_name:
                doc_metadata += f"Company Name: {company_name}, "
            if user_type:
                doc_metadata += f"User Type: {user_type}, "

        # add url
        base_url = settings.NAMESPACE_URLS.get(namespace)
        url = f"{base_url}/{firestore_id}"
        doc_metadata = f"Source: {url}, " + doc_metadata

        # add score
        score = doc.get("score", 0)
        doc_metadata += f"Relevance: {score:.2f}"
        # add text
        line = (
            f"[Metadata] {doc_metadata}\n"
            f"[Content] {raw_text}\n\n"
        )

        context_lines.append(line)

    return "\n".join(context_lines)

@with_logging
@traceable
def augmentation_node(state: State)-> Dict[str, str]:
    """
    Augments retrieved docs and prepares the final context used to generate response.
    """
    final_context = format_context_for_llm(state['retrieved_docs'], settings.pinecone.max_docs)
    return {"final_context": final_context}


@with_logging
@traceable
def final_response_node(state: State, chain):
    """
    Final node that produces the assistant response.
    """
    dialogue_msgs = [
      f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
      for msg in state["messages"][-6:]
      if isinstance(msg, (HumanMessage, AIMessage))
    ]
    dialogue_context = "\n".join(dialogue_msgs)

    response = chain.invoke({"retrieved_context": state['final_context'], "user_query": state['query'], "conversation_history": dialogue_context})
    if response.content:
        state["messages"].append(AIMessage(content=response.content))
    return {"response": response.content}
