LLM_CONFIGS = {
    'user-recruiter-generation': {
        "model_name": "meta-llama/llama-3.3-70b-instruct:free",
        "params": {
            "temperature":1.2,
            "max_tokens": 50000,
            "top_p":1.0,
            "frequency_penalty": 1.0,
            "presence_penalty": 0.0,
            "request_timeout": 60
        }
    },
}