from src.llm.llm_config import LLM_CONFIGS
from src.config.config import settings
from langchain_openai import ChatOpenAI
from src.logger import logger

def get_open_router_llm(config_key):

    """Retrieves and initializes an LLM model using OpenRouter settings.
    
    Args:
        config_key (str): The key to fetch model configuration from LLM_CONFIGS.

    Returns:
        ChatOpenAI: An instance of the ChatOpenAI model with the specified configuration.

    Raises:
        ValueError: If the configuration key or model name is missing.
    """

    open_router_base_url = settings.OPEN_ROUTER_BASE_URL
    llm_params = LLM_CONFIGS[config_key]
    if not settings:
        raise ValueError(f"Configuration for {config_key} not found.")
    model_name = llm_params["model_name"]
    model_params = llm_params["params"]

    if not model_name:
        raise ValueError(f"Model name not found for {config_key}.")
    
    llm = ChatOpenAI(
        model_name = llm_params["model_name"],
        openai_api_base = open_router_base_url,
        openai_api_key = settings.OPENAI_API_KEY,
        **model_params
    )
    logger.info("\nLLm: \n", llm)
    return llm


