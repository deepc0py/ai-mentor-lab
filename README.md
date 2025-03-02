# ESL RAG Application

A Retrieval-Augmented Generation (RAG) application for generating personalized ESL homework and student activity pairings.

## Overview

This application helps ESL teachers create personalized homework assignments and conversation activities for their students by:

1. Storing homework templates, activity templates, and student profiles in PostgreSQL
2. Creating vector embeddings of all content using ChromaDB
3. Using LLMs (via LangChain and OpenAI) to generate personalized homework questions
4. Creating optimized student pairings for conversation activities

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL database
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/esl-rag-app.git
cd esl-rag-app
```

2. Install dependencies:
```bash
pip install chromadb langchain langchain-openai sentence-transformers sqlmodel python-dotenv psycopg2-binary
```

3. Configure environment variables:
Create a `.env` file in the root directory with:
```
OPENAI_API_KEY=your_openai_api_key_here
```

4. Initialize the database:
```bash
python main.py init
```

## Usage

### Syncing Data

After adding templates and student profiles to your PostgreSQL database, sync them to ChromaDB:

```bash
python main.py sync
```

### Generating Personalized Homework

```bash
python main.py homework --student-id 1 --output homework_result.json
```

Optional parameters:
- `--template-id`: Specify a particular homework template
- `--class-id`: Filter by class ID
- `--no-save`: Don't save the generated homework to PostgreSQL

### Generating Student Pairings

```bash
python main.py pairings --class-id 1 --output pairings_result.json
```

Optional parameters:
- `--template-id`: Specify a particular activity template
- `--no-save`: Don't save the generated pairings to PostgreSQL

## Project Structure

```
esl_rag_app/
├── app/
│   └── db/
│       ├── database.py   # Database connection
│       └── models.py     # SQLAlchemy models
├── rag/
│   ├── __init__.py
│   ├── chroma_setup.py      # ChromaDB setup
│   ├── db_integration.py    # Integration between PostgreSQL and ChromaDB
│   └── homework_generator.py # RAG-based homework generator
├── main.py                  # Main application
├── .env                     # Environment variables
└── README.md
```

## Database Models

- **Student**: ESL student profiles with personal, professional, and learning information
- **HomeworkTemplate**: Templates for homework assignments
- **PersonalizedHomework**: Generated personalized homework assignments
- **ActivityTemplate**: Templates for conversation activities
- **ActivityGroup**: Student pairings for conversation activities

## Customization

You can customize the application by:

1. Modifying the prompts in `homework_generator.py`
2. Adding new student pairing algorithms in `db_integration.py`
3. Extending the database models in `app/db/models.py`
4. Using different embedding models in `chroma_setup.py`

## Troubleshooting

If you encounter issues:

1. Check that your OpenAI API key is valid
2. Ensure your database is properly connected
3. Check that you have sufficient student profiles and templates in your database
4. For ChromaDB issues, try recreating the collections with `python main.py init`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
