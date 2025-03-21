from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Literal, Dict, Any
from logger import logger
from graph.graph_builder import Graph
from graph.state import State
from langchain.schema import HumanMessage, AIMessage


class Message(BaseModel):
    type: Literal["user", "ai"]
    content: str

class InvokePayload(BaseModel):
    user_id: str
    session_id: str
    messages: List[Message]

def create_default_state() -> State:
  """Creates a default State dictionary."""
  return {
      "query": "",
      "standalone_query": "",
      "query_type": "",
      "vector_namespace": [],
      "retrieved_docs": [],
      "final_context": "",
      "response": "",
      "messages": []
  }

def prepare_state_object(messages: List[Message]) -> State:
    try:
        state = create_default_state()
        state_messages = []
        for message in messages:
            if message.type == "user":
                state_messages.append(HumanMessage(content=message.content))
            elif message.type == "ai":
                state_messages.append(AIMessage(content=message.content))
            else:
                raise HTTPException(status_code=400, detail="Expected message type [user, ai] not found.")
        
        state["messages"] = state_messages
        return state
    except Exception as e:
        logger.error(f"Failed to prepare state object: {e}")
        raise HTTPException(status_code=400, detail="Failed to extarct state object: {e}")

def convert_response_state(response_state: State)->Dict[str, Any]:
    response_dict = response_state.copy()
    messages = []
    for message in response_state["messages"]:
        if isinstance(message, HumanMessage):
            messages.append({"type":"user", "content":message.content})
        elif isinstance(message, AIMessage):
            messages.append({"type":"ai", "content":message.content})
    response_dict['messages'] = messages

    return response_dict


class ClientApp:
    def __init__(self):
        logger.info("Initializing graph")
        self.graph_builder = Graph()
        self.graph = self.graph_builder.build_graph(isMemory=False)
        logger.info("Initializing graph complete")

clapp = ClientApp()

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.post("/invoke")
async def invoke(payload: InvokePayload = Body(...)):
    # Prepare state object
    state = prepare_state_object(payload.messages)
    # ensure user type
    if payload.messages[-1].type == "user":
        new_query = payload.messages[-1].content
    if not new_query:
        raise HTTPException(status_code=400, detail="Latest message content is empty or not a user query")
    state["query"] = new_query
    
    logger.info(f"Invoke called for user {payload.user_id} and session {payload.session_id} with query: {new_query}")
    
    config = {"configurable": {"thread_id": payload.session_id}}

    try:
        response_state = await clapp.graph.ainvoke(state, config=config)
        response_json = convert_response_state(response_state)
        # include ids
        response_json["user_id"] = payload.user_id
        response_json["session_id"] = payload.session_id
    except Exception as e:
        logger.error(f"Error during graph processing: {e}")
        raise HTTPException(status_code=500, detail="Error processing query")
    
    return JSONResponse(content=response_json, status_code=200)