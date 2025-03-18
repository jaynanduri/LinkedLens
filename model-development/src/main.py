from logger import logger, with_logging
from config.settings import settings
from langgraph.graph import StateGraph
from graph.state import State
from langchain.schema import HumanMessage, AIMessage
from graph.graph_builder import Graph

def chat_loop(graph: StateGraph, initial_state: State, config:dict):
    state = initial_state
    print("Chat session started. Type 'exit' to end the conversation.")
    
    while True:
        user_input = input("User: ").strip()
        
        if user_input.lower() == 'exit':
            print("Ending chat session.")
            break
        
        state["query"] = user_input
        state["messages"].append(HumanMessage(content=user_input))

        # Process through the graph
        for step in graph.stream(state, config=config, stream_mode="values"):
          state = step
            
        if state.get("response"):
            print(f"Assistant: {state['response']}")
        
        # Reset query and response for the next iteration.
        state["query"] = ""
        state["response"] = ""

    print(f"Final state: {state}")

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

if __name__ == "__main__":
    config_user1 = {"configurable": {"thread_id": "user1"}}
    state = create_default_state()
    graph_builder = Graph()
    # build graph 
    graph = graph_builder.build_graph(isMemory=True)
    chat_loop(graph, state, config_user1)