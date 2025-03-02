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
