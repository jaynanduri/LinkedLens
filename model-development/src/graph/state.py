from typing import TypedDict, List
from langchain.schema import BaseMessage
from langgraph.graph.message import add_messages
from typing import Annotated

class State(TypedDict):
    query: str
    standalone_query: str
    query_type: str
    vector_namespace: List[str]
    retrieved_docs: List[dict]
    final_context: str
    response: str
    messages: Annotated[List[BaseMessage], add_messages]


    # Add filter messages.. 