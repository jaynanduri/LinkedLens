from typing import Dict, Any
from src.llm.llm_config import LLM_CONFIGS
from src.config.config import settings
from langchain_openai import ChatOpenAI
from src.logger import logger
from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm(config_key: str, provider_name: str = 'gemini'):
    provider_config = LLM_CONFIGS.get(provider_name, None)
    if not provider_config:
        raise ValueError(f"Model Configurations for {provider_name} not found.")
    
    if provider_name == 'gemini':
        return get_gemini_llm(config_key, provider_config)
    else:
        return get_open_router_llm(config_key, provider_config)



def get_gemini_llm(config_key: str, provider_config: Dict[str, Any]) -> ChatGoogleGenerativeAI:

    """Initializes an Gemini LLM model.
    
    Args:
        provider_config (Dict[str, Dict]): The llm configuration for openai provider from LLM_CONFIGS
        config_key (str): The key to fetch model configuration from provider_config.

    Returns:
        ChatGoogleGenerativeAI: An instance of the ChatGoogleGenerativeAI model with the specified configuration.

    Raises:
        ValueError: If the configuration key or model name is missing.
    """

    llm_params = provider_config[config_key]
    if not llm_params:
        raise ValueError(f"Configuration for {config_key} not found.")
    model_name = llm_params["model_name"]
    model_params = llm_params["params"]

    if not model_name:
        raise ValueError(f"Model name not found for {config_key}.")
    
    llm = ChatGoogleGenerativeAI(
        api_key = settings.GEMINI_API_KEY,
        model = llm_params["model_name"],
        **model_params
    )
    logger.info(f"\nLLm: \n {llm}")
    return llm


def get_open_router_llm(config_key: str, provider_config: Dict[str, Any]) -> ChatOpenAI:

    """Retrieves and initializes an LLM model using OpenRouter settings.
    
    Args:
        provider_config (Dict[str, Dict]): The llm configuration for openai provider from LLM_CONFIGS
        config_key (str): The key to fetch model configuration from provider_config.

    Returns:
        ChatOpenAI: An instance of the ChatOpenAI model with the specified configuration.

    Raises:
        ValueError: If the configuration key or model name is missing.
    """

    open_router_base_url = settings.OPEN_ROUTER_BASE_URL
    llm_params = provider_config[config_key]
    if not llm_params:
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
    logger.info(f"\nLLm: \n {llm}")
    return llm


