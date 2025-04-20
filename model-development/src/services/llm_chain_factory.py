from services.llm_provider import LLMProvider
# from langchain import PromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate
from langchain.tools import tool
from typing import List


@tool
def retrieval_tool(standalone_query: str, vector_namespace: List[str]) -> dict:
    """
    Use this tool to retrieve documents that help answer job-related queries.

    This tool searches across specified namespaces to return relevant documents 
    that can assist with questions about job postings, recruiter activity, or user-shared experiences. 
    It is typically used when the user's query cannot be answered using conversation history alone.

    Args:
        standalone_query: A rewritten, standalone version of the user's query. It should be clear,
                          context-independent, and suitable for searching.
        vector_namespace: A list of data sources to search in. Choose from:
                          - 'job': job listings and roles
                          - 'recruiter_post': recruiter hiring or job announcements
                          - 'user_post': posts from users sharing interview experiences or advice
                          - 'user': (optional) information about individual users or recruiters

    Returns:
        A dictionary containing the standalone_query, the namespaces searched, and an indicator that this 
        was a retrieval-type query.
    """
    return {
        "standalone_query": standalone_query,
        "vector_namespace": vector_namespace,
        "query_type": "retrieve"
    }

class LLMChainFactory:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    def create_query_analysis_chain(self, prompt_text: str, output_model, include_raw: bool = True):

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_text),
            ("human", "{query}")
        ])

        llm = self.llm_provider.get_llm()
        llm_with_tools = llm.bind_tools([retrieval_tool])
        return prompt | llm_with_tools
    
        # prompt = PromptTemplate(
        #     input_variables=["conversation", "query"],
        #     template=prompt_text
        # )
        # llm = self.llm_provider.get_llm()
        # return prompt | llm.with_structured_output(output_model, include_raw=include_raw)

    def create_final_response_chain(self, system_prompt: str):

        prompt = PromptTemplate(
            input_variables=["conversation_history", "user_query", "retrieved_context"],
            template=system_prompt
        )

        llm = self.llm_provider.get_llm()
        return prompt | llm