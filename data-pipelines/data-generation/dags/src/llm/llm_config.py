
# {
#     "provider1": {
#         same as config below
#     },
#     "provider2": {
#         same as config below
#     }
# }


LLM_CONFIGS = {

    "openai": {
        'recruiter-post': {
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
        'user-post-generation': {
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
        'basic-user-details': {
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
    },

    "gemini": {
        'recruiter-post': {
            "model_name": "gemini-2.0-flash-001",
            "params": {
                "temperature":1.2,
                "max_tokens": 50000,
                "top_p":1.0,
                # "frequency_penalty": 1.0,
                # "presence_penalty": 0.0,
                "timeout": 60
            }
        },
        'user-post-generation': {
            "model_name": "gemini-2.0-flash-001",
            "params": {
                "temperature":1.2,
                "max_tokens": 50000,
                "top_p":1.0,
                # "frequency_penalty": 1.0,
                # "presence_penalty": 0.0,
                "timeout": 60
            }
        },
        'basic-user-details': {
            "model_name": "gemini-2.0-flash-001",
            "params": {
                "temperature":1.2,
                "max_tokens": 50000,
                "top_p":1.0,
                # "frequency_penalty": 1.0,
                # "presence_penalty": 0.0,
                "timeout": 60
            }
        },
    }
}

# 'user-recruiter-generation': {
#         "model_name": "meta-llama/llama-3.3-70b-instruct:free",
#         "params": {
#             "temperature":1.2,
#             "max_tokens": 50000,
#             "top_p":1.0,
#             "frequency_penalty": 1.0,
#             "presence_penalty": 0.0,
#             "request_timeout": 60
#         }
#     },