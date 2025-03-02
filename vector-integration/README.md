# LinkedLens Vector Integration

Integration between Firestore and Pinecone Vector DB for the LinkedLens

## Overview

This system connects Firestore with Pinecone Vector Database, maintaining a synchronized vector index of all content. It:

1. Detects new data in Firestore (users, jobs, posts)
2. Processes that data into vector embeddings using Sentence Transformers
3. Stores those embeddings in Pinecone
4. Provides mapping between Firestore documents and their corresponding vectors

## Setup

### Prerequisites

1. Python 3.8+
2. Firebase project with Firestore
3. Pinecone account and API key
4. A Firestore database with LinkedLens data (users, jobs, posts)

### Installation

1. Clone the repository:
   ```bash
   cp .env.template .env
   # Edit .env with your credentials
   ```

5. Set up Firestore credentials:
   ```bash
   mkdir -p config
   # Add your db-credentials.json file to the config directory
   ```

### Initializing Pinecone

Before syncing data, you need to initialize the Pinecone index:

```bash
python src/main.py init 
```

This creates a new index or (retrieves the existing) in Pinecone with the appropriate configuration.

### Testing Conections

To Test Pinecone, FireStore and Embedding connections

```bash
python src/main.py test
```

To sync:

```bash
python src/main.py sync
```

To search from VectorDB:

```bash
python src/main.py search "Python developer" --type job
```

## Architecture

### Data Flow

1. **Document Creation/Update**: When a document is created or updated in Firestore, it's detected
2. **Document Processing**: The document is transformed into a format suitable for embedding
3. **Embedding Generation**: Sentence Transformers generates embeddings
4. **Vector Storage**: The embedding is stored in Pinecone with metadata
5. **Reference Update**: The Firestore document is updated with vector information

## Configuration

- **Pinecone Settings**: API configuration, index settings, collection mappings
- **Firestore Settings**: Collection names, batch sizes
- **Embedding Settings**: Model selection, input limits
- **Processing Options**: Concurrent operations, update strategies

## Troubleshooting

### Logs

Logs are written to the console and optionally to a file. To increase log verbosity:

```
LOG_LEVEL=DEBUG python scripts/sync_data.py
```