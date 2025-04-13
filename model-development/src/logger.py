import logging
import sys
import os
import time
from google.cloud import logging as gcloud_logging
from google.oauth2 import service_account
from google.cloud.logging.handlers import CloudLoggingHandler
from config.settings import settings
from functools import wraps
import json
import asyncio


def get_logger(env: str="prod", name:str =settings.LOG_NAME):
    # Initialize Google Cloud Logging client
    gcp_client = gcloud_logging.Client()
    gcp_handler = CloudLoggingHandler(gcp_client, name=name)

    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)
    
    # Log format
    # log_formatter = logging.Formatter("[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s")
    
    # Google Cloud Logging
    # gcp_handler.setFormatter(log_formatter)

    # clear handlers to avoid duplicate logs
    logger.handlers.clear()

    logger.addHandler(gcp_handler)
    
    # Stdout logging (only for development)
    if env == "dev":
        stdout_handler = logging.StreamHandler(sys.stdout)
        # stdout_handler.setFormatter(log_formatter)
        logger.addHandler(stdout_handler)
    
    return logger

# Set up logger (Change env to 'prod' when deploying)
logger = get_logger(env="prod", name=settings.LOG_NAME)

def set_logger(name:str=settings.LOG_NAME, env:str="prod"):
    """
    Set up the logger with Google Cloud Logging and stdout logging.
    
    Args:
        name (str): The name of the logger.
        env (str): The environment ('prod' or 'dev').
    """
    global logger
    logger = get_logger(name=name, env=env)
    print(f"Logger HANDLERS : {logger.handlers}")

def with_logging(func):
    @wraps(func)
    def wrapper(state:dict, *args, **kwargs):
        pre_state = state.copy()
        str_pre_state = str(pre_state)
        start = time.time_ns()
        try:
            func_output = func(state, *args, **kwargs)
            str_func_output = str(func_output)
        except Exception as e:
            duration_ns = time.time_ns() - start
            error_log = {
                "event": "node_error",
                "node": func.__name__,
                "duration_ns": duration_ns,
                "pre_state": str_pre_state,
                "error": str(e),
                "timestamp": time.time_ns()
            }
            logger.error(f"Node Process Failed : {json.dumps(error_log)}", 
                         extra={"json_fields": {"error":error_log}})
            raise
        
        duration_ns = time.time_ns() - start
        log_data = {
            "event": "node_executed",
            "node": func.__name__,
            "duration_ns": duration_ns,
            "pre_state": str_pre_state,
            "func_output": str_func_output,
            "timestamp": time.time_ns()
        }
        logger.info(f"Node Executed: {json.dumps(log_data)}",
                    extra={"json_fields": {"event": log_data}})
        
        print(f"Scheduled log write for {func.__name__}")
        return func_output
    return wrapper