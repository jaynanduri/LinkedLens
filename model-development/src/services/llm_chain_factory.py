from services.llm_provider import LLMProvider
# from langchain import PromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate

class LLMChainFactory:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    def create_query_analysis_chain(self, prompt_text: str, output_model, include_raw: bool = True):
        prompt = PromptTemplate(
            input_variables=["conversation", "query"],
            template=prompt_text
        )
        llm = self.llm_provider.get_llm()
        return prompt | llm.with_structured_output(output_model, include_raw=include_raw)

    def create_final_response_chain(self, system_prompt: str):

        prompt = PromptTemplate(
            input_variables=["conversation_history", "user_query", "retrieved_context"],
            template=system_prompt
        )

        llm = self.llm_provider.get_llm()
        return prompt | llm