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

# Firestore settings
FIRESTORE_COLLECTIONS = ["users", "jobs", "posts"]

# Embedding settings
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# LLM Model name
GEMINI_MODEL_NAME = "gemini-1.5-pro"