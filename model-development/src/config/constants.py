# Pinecone settings
PINECONE_CLOUD = 'aws'
PINECONE_REGION = 'us-east-1'
PINECONE_INDEX_NAME = 'linked-lens-index'
PINECONE_NAMESPACE_COLLECTION = {
    "user": "users",
    "user_post": "posts",
    "recruiter_post": "posts",
    "job": "jobs",
}
PINECONE_METADATA_FIELDS = {
    # firestoreId, createdAt, updatedAt included by default for all
    "job": ["title", "company_name", "author", "location", "ttl"],
    "user_post": ["author", "ttl"],
    "user": ["company", "account_type"],
    "recruiter_post": ["author", "job_id", "ttl"],
}
# threshold for namespace
PINECONE_NAMESPACE_THRESHOLD = {
    'job': 0.60,
    'recruiter_post':0.50,
    'user_post' : 0.50,
}
PINECONE_MAX_DOCS=20

# Firestore settings
FIRESTORE_COLLECTIONS = ["users", "jobs", "posts"]
FIRESTORE_TEST_DATA= {
    "jobs": {
        "ids": ["3884430949", "3857848893", "175485704", "3884434198"],
        "field_paths": ["title", "company_name", "description", "location"]
        },
    "posts": {
            "ids": ["6aeed728-fbd7-11ef-abe2-0242ac120004", "7f918036-fbcd-11ef-95bc-0242ac120007", "f949aab4-fbe8-11ef-a638-0242ac120004",
              "0ab66f9a-fbcf-11ef-b993-0242ac120007", "1b6a59c6-fbdb-11ef-a750-0242ac120005", "293c7d6a-fbcf-11ef-b993-0242ac120007",
              "2d33612a-fbdb-11ef-a750-0242ac120005"],
            "field_paths": ["content", "job_id"]
              }
}

# Embedding settings
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"

# LLM Model name
GEMINI_MODEL_NAME = "gemini-2.0-flash-001" #"gemini-1.5-pro"

# log name for gcp client
LOG_NAME="linkedlens_chat"
PRE_EVAL_LOG_NAME="linkedlens_pre_eval_test"
POST_EVAL_LOG_NAME = "linkedlens_post_eval_test"
TEST_LOG_NAME = "linkedlens_test"

PROD_RUN_ENV="prod"
TEST_RUN_ENV="test"

# URLS:
BASE_URL = 'https://yourdomain.com'
NAMESPACE_URLS= {
        "job": BASE_URL+"/job",
        "user_post": BASE_URL+"/post",
        "recruiter_post": BASE_URL+"/post",
        "user": BASE_URL+"/user"
    }

RAGAS_SIMPLE_QUERIES = 0.65
RAGAS_MULTI_HOP_DIRECT = 0.25
RAGAS_MULTI_HOP_COMPLEX =0.10

TEST_METRIC_THRESHOLD = {
    "faithfulness": 0.5, 
    "response_relevancy": 0.5, 
    "retrieval_relevance": 0.5
}
