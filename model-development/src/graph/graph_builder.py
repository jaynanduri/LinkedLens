from functools import partial
from langgraph.graph import StateGraph, START, END
from services.prompt_manager import PromptManager
from langgraph.checkpoint.memory import MemorySaver
from services.llm_provider import LLMProvider
from services.llm_chain_factory import LLMChainFactory
from graph.nodes import augmentation_node, check_query_type, final_response_node, query_analyzer_node, retrieval_node, QueryAnalysis
from clients.embedding_client import EmbeddingClient
from clients.pinecone_client import PineconeClient
from graph.state import State
from config.settings import settings

class Graph:
    def __init__(self):
        self.builder = StateGraph(State)
        self._initialize_components()
    
    def _initialize_components(self):
        # Instantiate the LLM provider and chain factory
        self.llm_provider = LLMProvider(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL_NAME)
        self.chain_factory = LLMChainFactory(self.llm_provider)
        self.prompt_manager = PromptManager()

        # Create chains using the factory
        query_analysis_prompt = self.prompt_manager.get_prompt("query_analysis_prompt")
        self.query_analysis_chain = self.chain_factory.create_query_analysis_chain(query_analysis_prompt, QueryAnalysis, include_raw=True)


        final_system_prompt = self.prompt_manager.get_prompt("final_system_prompt")
        self.final_response_chain = self.chain_factory.create_final_response_chain(final_system_prompt)

        # Instantiate clients
        self.embedding_client = EmbeddingClient()
        self.pinecone_client = PineconeClient()
    
    def build_graph(self, isMemory=False):
        memory = MemorySaver()
        # Add nodes to the workflow
        self.builder.add_node("query_analyzer_node", partial(query_analyzer_node, 
                                                             chain=self.query_analysis_chain))
        
        self.builder.add_node("retrieval_node", partial(retrieval_node, 
                                                        embedding_client=self.embedding_client, 
                                                        pinecone_client=self.pinecone_client))
        
        self.builder.add_node("augmentation_node", partial(augmentation_node, 
                                                           pinecone_client=self.pinecone_client))
        
        self.builder.add_node("final_response_node", partial(final_response_node, 
                                                             chain=self.final_response_chain))

        # Define edges
        self.builder.add_edge(START, "query_analyzer_node")
        self.builder.add_conditional_edges(
            "query_analyzer_node",
            check_query_type, 
            {"retrieve": "retrieval_node", "generic": "final_response_node"}
            )
        self.builder.add_edge("retrieval_node", "augmentation_node")
        self.builder.add_edge("augmentation_node", "final_response_node")
        self.builder.add_edge("final_response_node", END)

        graph = self.builder.compile(checkpointer=memory) if isMemory else self.builder.compile()
        return graph

        
