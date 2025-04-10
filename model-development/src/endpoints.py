from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError, field_validator, ValidationInfo
from typing import List, Literal, Dict, Any
from pydantic.functional_validators import BeforeValidator
from typing import Annotated, Literal, List

from logger import logger
from graph.graph_builder import Graph
from graph.state import State
from langchain.schema import HumanMessage, AIMessage
from langsmith  import traceable
import langsmith as ls
from services.rag_evaluator import RAGEvaluator
import json
from starlette.status import (
    HTTP_200_OK,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


def strip_and_validate_nonempty(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("content cannot be empty or whitespace")
    return stripped

NonEmptyStr = Annotated[str, BeforeValidator(strip_and_validate_nonempty)]
class Message(BaseModel):
    type: Literal["user", "ai"]
    content: NonEmptyStr

class InvokePayload(BaseModel):
    user_id: NonEmptyStr
    session_id: NonEmptyStr
    chat_id: NonEmptyStr
    messages: List[Message] = Field(..., min_items=1)


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
    response_dict = {}
    response_dict["query"] = response_state.get("query", "")
    response_dict["final_context"] = response_state.get("final_context", "")
    response_dict["response"] = response_state.get("response", "")
    return response_dict


class ClientApp:
    def __init__(self):
        logger.info("Initializing graph")
        self.graph_builder = Graph()
        self.rag_evaluator = RAGEvaluator()
        self.graph = self.graph_builder.build_graph(isMemory=True)
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

    state["query"] = new_query
    
    logger.info(f"Invoke called for user {payload.user_id} and session {payload.session_id} with query: {new_query}")
    
    config = {"configurable": {"thread_id": payload.session_id, "user_id": payload.user_id, "chat_id": payload.chat_id}}

    try:
        response_state = await clapp.graph.ainvoke(state, config=config)
        response_json = convert_response_state(response_state)
        # include ids
        response_json["user_id"] = payload.user_id
        response_json["session_id"] = payload.session_id
        response_json["chat_id"] = payload.chat_id
        # Log metrics
        try:
            metrics = clapp.rag_evaluator.evaluate(
                query=response_json["query"],
                standalone_query=response_state["standalone_query"],
                context=response_json["final_context"],
                response=response_json["response"]
            )
        except Exception as e:
            logger.error(f"RAG evaluation failed: {e}")
            metrics = {
                "retrieval_relevance": None,
                "response_relevance": None,
                "faithfulness": None
            }
        metric_data = {
            "user_id": payload.user_id,
            "session_id": payload.session_id,
            "chat_id": payload.chat_id,
            **metrics
        }
        logger.info(f"Evaluation metrics: 'metrics_data':{json.dumps(metric_data)}")
    except Exception as e:
        logger.error(f"Error during graph processing: {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": f"Error processing query: {e}" })
    
    return JSONResponse(content=response_json, status_code=HTTP_200_OK)