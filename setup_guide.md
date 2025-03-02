# ESL RAG Application Setup Guide

This guide will help you set up the RAG (Retrieval-Augmented Generation) component for your ESL homework generation application.

## Prerequisites

- Python 3.8+
- PostgreSQL database (already set up with your schema)
- OpenAI API key

## Installation

### 1. Install Required Packages

```bash
pip install chromadb langchain langchain-openai sentence-transformers sqlmodel python-dotenv psycopg2-binary
```

### 2. Project Structure

Create the following file structure:

```
esl_rag_app/
├── app/
│   └── db/
│       ├── database.py   # Your existing database connection
│       └── models.py     # Your existing SQLAlchemy models
├── rag/
│   ├── __init__.py
│   ├── chroma_setup.py      # ChromaDB setup module
│   ├── db_integration.py    # Integration between PostgreSQL and ChromaDB
│   └── homework_generator.py # RAG-based homework generator
├── main.py                  # Main application
├── .env                     # Environment variables
└── README.md
```

### 3. Environment Setup

Create a `.env` file with your API key:

```
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the Application

### 1. Initialize ChromaDB

```bash
python main.py init --persist-dir ./chroma_db
```

This creates the ChromaDB collections and prepares them for storing your data.

### 2. Sync Data from PostgreSQL to ChromaDB

```bash
python main.py sync --persist-dir ./chroma_db
```

This command will:
- Extract homework templates from PostgreSQL
- Extract activity templates from PostgreSQL
- Extract student profiles from PostgreSQL
- Create vector embeddings for all data
- Store everything in ChromaDB

### 3. Generate Personalized Homework

```bash
python main.py homework --student-id 1 --output homework_result.json
```

Optional parameters:
- `--template-id`: Specify a particular homework template
- `--class-id`: Filter by class ID
- `--no-save`: Don't save the generated homework to PostgreSQL

### 4. Generate Student Pairings for Activities

```bash
python main.py pairings --class-id 1 --output pairings_result.json
```

Optional parameters:
- `--template-id`: Specify a particular activity template
- `--no-save`: Don't save the generated pairings to PostgreSQL

## Integrating with Your Frontend

The RAG system now provides these key endpoints that your frontend can use:

1. **Personalized Homework Generation**: Generate customized homework questions based on student profiles
2. **Student Pairing**: Create optimized student pairings for conversation activities
3. **Template Retrieval**: Find the most relevant templates for specific students or learning objectives

## Adding New Content

As you add new content to your PostgreSQL database, you should periodically sync it to ChromaDB:

```bash
python main.py sync
```

This will update the vector database with new homework templates, activity templates, and student profiles.

## Troubleshooting

### ChromaDB Connection Issues

If you encounter issues connecting to ChromaDB, try:

```bash
rm -rf ./chroma_db
python main.py init
python main.py sync
```

This recreates the ChromaDB from scratch.

### Missing Student Profiles

If you get errors about missing student profiles, ensure you've completed all the profile information in PostgreSQL before syncing.

### Large File Handling

For large databases, the sync process might take time. For better performance:

1. Use a more powerful embedding model (change in `chroma_setup.py`)
2. Implement incremental syncing (only new/changed records)
3. Optimize the PostgreSQL queries for faster data retrieval

## Next Steps

Consider implementing these enhancements:

1. Add an API layer (FastAPI or Flask) for web integration
2. Implement caching for frequently used embeddings
3. Add user authentication for the RAG system
4. Create a feedback mechanism to improve personalizations over time