# Pinecone settings
PINECONE_CLOUD = 'aws'
PINECONE_REGION = 'us-east-1'
PINECONE_INDEX_NAME = 'linkedlens-index'
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

# Embedding settings
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# LLM Model name
GEMINI_MODEL_NAME = "gemini-1.5-pro"

# log name for gcp client
LOG_NAME="linkedlens_chat"

# URLS:
BASE_URL = 'https://yourdomain.com'
NAMESPACE_URLS= {
        "job": BASE_URL+"/job",
        "user_post": BASE_URL+"/post",
        "recruiter_post": BASE_URL+"/post",
        "user": BASE_URL+"/user"
    }

