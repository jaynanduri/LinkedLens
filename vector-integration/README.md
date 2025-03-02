# LinkedLens Vector Integration

Integration between Firestore and Pinecone Vector DB for the LinkedLens

## Overview

This system connects Firestore with Pinecone Vector Database, maintaining a synchronized vector index of all content. It:

1. Detects new data in Firestore (users, jobs, posts)
2. Processes that data into vector embeddings using Sentence Transformers
3. Stores those embeddings in Pinecone
4. Provides mapping between Firestore documents and their corresponding vectors

## Features

- 🔄 **Real-time Synchronization**: Automatically detects and processes new or updated documents
- 🔍 **Vector Search**: Query similar documents across collections
- 🧠 **Sentence Transformers Integration**: High-quality embeddings without API dependencies
- 🔌 **Modular Architecture**: Clean, modular Python implementation
- 🔄 **Bidirectional References**: Store vector IDs in Firestore and document IDs in Pinecone
- 📊 **Document Processing**: Intelligent document transformation for optimal embedding generation

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
python scripts/init_pinecone.py
```

This creates a new index in Pinecone with the appropriate configuration.

### Running Data Sync

To sync all collections:

```bash
python scripts/sync_data.py
```

To sync only a specific collection:

```bash
python scripts/sync_data.py --collection users  # Sync users
python scripts/sync_data.py --collection jobs    # Sync jobs
python scripts/sync_data.py --collection posts   # Sync posts
```

To sync only new documents (not already vectorized):

```bash
python scripts/sync_data.py --only-new
```

## Architecture

### Directory Structure

```
linkedlens-vector-integration/
├── config/                 # Configuration files
│   ├── settings.py         # Settings using Pydantic
│   └── db-credentials.json # Firestore credentials
├── src/                    # Source code
│   ├── clients/            # API clients
│   │   ├── firestore_client.py
│   │   ├── pinecone_client.py
│   │   └── embedding_client.py
│   ├── processors/         # Document processing
│   │   └── document_processor.py
│   ├── utils/              # Utilities
│   │   └── logger.py
│   └── main.py             # Main entry point
├── scripts/                # Utility scripts
│   ├── init_pinecone.py    # Initialize Pinecone
│   ├── test_connections.py # Test connections
│   └── sync_data.py        # Sync data
└── README.md
```

### Data Flow

1. **Document Creation/Update**: When a document is created or updated in Firestore, it's detected
2. **Document Processing**: The document is transformed into a format suitable for embedding
3. **Embedding Generation**: Sentence Transformers generates embeddings
4. **Vector Storage**: The embedding is stored in Pinecone with metadata
5. **Reference Update**: The Firestore document is updated with vector information

## Configuration

All configuration is in `config/settings.py`:

- **Pinecone Settings**: API configuration, index settings, collection mappings
- **Firestore Settings**: Collection names, batch sizes
- **Embedding Settings**: Model selection, input limits
- **Processing Options**: Concurrent operations, update strategies

## Troubleshooting

### Common Issues

- **Missing Credentials**: Ensure all environment variables and credential files are in place
- **API Limits**: Pinecone has rate limits that might be hit during large sync operations
- **Memory Issues**: Large batch sizes may cause memory problems, adjust as needed

### Logs

Logs are written to the console and optionally to a file. To increase log verbosity:

```
LOG_LEVEL=DEBUG python scripts/sync_data.py
```

## Extending

### Adding New Collections

1. Add the collection name to `settings.firestore.collections`
2. Add the mapping in `settings.pinecone.collections`
3. Add relevant fields to `settings.pinecone.metadata_fields`
4. Add text extraction logic in `document_processor.py`

## License

MIT
   git clone <repository-url>
   cd linkedlens-vector-integration
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash