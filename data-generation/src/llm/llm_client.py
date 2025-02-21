from llm.llm_config import LLM_CONFIGS
from config.config import config
from langchain_openai import ChatOpenAI

def get_open_router_llm(config_key):
    open_router_base_url = "https://openrouter.ai/api/v1"
    llm_params = LLM_CONFIGS[config_key]
    if not config:
        raise ValueError(f"Configuration for {config_key} not found.")
    model_name = llm_params["model_name"]
    model_params = llm_params["params"]

    if not model_name:
        raise ValueError(f"Model name not found for {config_key}.")
    
    llm = ChatOpenAI(
        model_name = llm_params["model_name"],
        openai_api_base = open_router_base_url,
        openai_api_key = config.OPENAI_API_KEY,
        **model_params
    )
    print("\nLLm Used: \n", llm)
    return llm


