from sqlmodel import create_engine, SQLModel, Session

# Configure the database connection URL
# For a production environment, this should come from environment variables
DATABASE_URL = "sqlite:///./esl_app.db"

# Create the SQLModel engine
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Initialize the database, creating all tables defined in models."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get a database session."""
    with Session(engine) as session:
        yield session
