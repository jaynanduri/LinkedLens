from functools import partial
from langgraph.graph import StateGraph, START, END

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

        # Create chains using the factory
        # TODO - fetch from prompt mgmt..
        query_analysis_prompt = """
        You are an expert query rewriter and information retriever. Your task is to analyze the provided conversation context and the latest user query, then output:
        1. The query type: if the query requires additional document retrieval or external context, output "retrieve"; otherwise, output "generic" for any greeting message.
        2. A standalone query that is clear and self-contained. Only if retrieval is required, else it is same as query
        3. The relevant namespaces from the following list: ["user", "job", "user_post", "recruiter_post"]. If you are not sure, output all namespaces.

        Instructions:
        - Use all provided conversation context, including system messages and the last few turns of dialogue.
        - The conversation context will include system messages (prefixed with "System:"), user messages (prefixed with "User:"), and assistant messages (prefixed with "Assistant:").
        - Do not include any extra text beyond the JSON.
        - If namespace identification fails, default to all available namespaces: ["user", "job", "user_post", "recruiter_post"].

        Conversation Context:
        {conversation}

        Latest Query:
        {query}

        Provide your output now.
        """
        
        self.query_analysis_chain = self.chain_factory.create_query_analysis_chain(query_analysis_prompt, QueryAnalysis, include_raw=True)

        final_system_prompt = (
        f'''
        You are Alpha, a highly knowledgeable and efficient chatbot assistant designed to help users with questions related to recruiting, hiring, and candidate experience. 
        Your primary role is to assist users by providing concise, accurate, and insightful responses based on the job/post/review information available to you.
        If you don’t have the necessary information to answer the question, simply say that you don’t know and apologize.
        
        When a user (e.g., a job seeker or candidate) asks a question, their query might have first been routed through a Query analyzer, Retriever and Aungentation.
        
        Your objective is to analyze the job/posts provided in the context, then provide clear, concise, and helpful advice. 
        If the context is insufficient or if the query is not clearly related to recruiting/hiring or candidate experience (e.g., generic greetings), respond appropriately:
        - For generic queries (e.g., “Hey, I’m John”), respond in a friendly manner.
        - For queries lacking adequate context, politely state that you don’t have enough information and apologize.
        
        The context provided to you below includes the aggregated and processed information. Use this context, along with the user's query, to generate your response.
        '''
        "{context}"
        )

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
        
        self.builder.add_node("augmentation_node", augmentation_node)
        
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

        
