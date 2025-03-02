# ChromaDB UI Guide

This guide explains how to use [Chroma UI](https://chroma-ui.vercel.app) with your ESL Teaching Assistant application to visualize and interact with your vector database.

## What is ChromaDB?

ChromaDB is a vector database that stores embeddings of your data, allowing for semantic search and retrieval. In this application, it stores:

1. **Homework Templates** - Vector embeddings of homework templates for semantic matching
2. **Activity Templates** - Vector embeddings of activity templates for semantic matching
3. **Student Profiles** - Vector embeddings of student profiles for better student-content matching

## Starting the ChromaDB Server

Before you can connect to the ChromaDB UI, you need to start a ChromaDB server. There are several ways to do this:

### Option 1: Using the ChromaDB CLI directly (Recommended)

```bash
chroma run --host localhost --port 8000 --path ./chroma_db
```

### Option 2: Using the wrapper script

```bash
python run_chroma_server.py --host localhost --port 8000 --persist-dir ./chroma_db
```

### Option 3: Using the multi-approach script

```bash
python chroma_server.py --host localhost --port 8000 --persist-dir ./chroma_db
```

### Option 4: Using the main.py script (Not recommended due to dependency issues)

```bash
python main.py server --host localhost --port 8000 --persist-dir ./chroma_db
```

Parameters:
- `--host`: The host to bind the server to (default: localhost)
- `--port`: The port to bind the server to (default: 8000)
- `--persist-dir` or `--path`: The directory where ChromaDB data is stored (default: ./chroma_db)

**Note**: If you want to access the ChromaDB server from another machine, you should set the host to `0.0.0.0` instead of `localhost`.

## Connecting to ChromaDB UI

1. Start the ChromaDB server as described above
2. Open [Chroma UI](https://chroma-ui.vercel.app) in your web browser
3. Enter the connection URL: `http://localhost:8000` (or whatever host/port you specified)
4. Click "Connect"

## Using ChromaDB UI

Once connected, you can:

1. **Browse Collections**: View the three collections in your database:
   - `homework_templates`
   - `activity_templates`
   - `student_profiles`

2. **Explore Documents**: Click on a collection to see the documents it contains

3. **Search**: Use the search functionality to find documents based on semantic similarity

4. **View Metadata**: See the metadata associated with each document

5. **Visualize Embeddings**: Use the visualization tools to see how your documents are clustered in the embedding space

## Troubleshooting

If you encounter issues connecting to the ChromaDB UI:

1. **Check the server**: Make sure the ChromaDB server is running and there are no errors in the console
2. **Check the URL**: Ensure you're using the correct URL (http://localhost:8000 by default)
3. **CORS issues**: If you encounter CORS errors, try using a browser extension to disable CORS for testing
4. **Firewall**: If connecting from another machine, check that your firewall allows connections to the specified port

### Server Initialization Errors

If you see errors like:
```
Error starting server: Can't instantiate abstract class Server without an implementation for abstract method '__init__'
```

Or:
```
ImportError: cannot import name 'ServerSettings' from 'chromadb.config'
```

Or:
```
No module named chromadb.server.__main__; 'chromadb.server' is a package and cannot be directly executed
```

Or:
```
ImportError: cannot import name 'LangSmithParams' from 'langchain_core.language_models.chat_models'
```

These errors are due to API changes in ChromaDB or dependency conflicts. The most reliable solution is to:

1. **Use the direct CLI command** (recommended):
   ```bash
   chroma run --host localhost --port 8000 --path ./chroma_db
   ```

2. **Try the `run_chroma_server.py` script** which uses multiple approaches to start the server

3. **Update ChromaDB** to the latest version:
   ```bash
   pip install -U chromadb
   ```

### Additional Troubleshooting Steps

If you still encounter issues:

1. **Check your ChromaDB version**:
   ```bash
   pip show chromadb
   ```

2. **Clear the ChromaDB directory**:
   ```bash
   rm -rf ./chroma_db
   ```

3. **Try a different port**: The default port (8000) might be in use by another application

4. **Check for database corruption**: If you see a message about vacuuming your database, run:
   ```bash
   python -m chromadb utils vacuum --path ./chroma_db
   ```

5. **Check Python version compatibility**: ChromaDB requires Python 3.8 or higher

## Limitations

The ChromaDB UI is a third-party tool and may not support all ChromaDB features. It's primarily designed for visualization and exploration, not for making changes to your database.

## Additional Resources

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Chroma UI GitHub Repository](https://github.com/chroma-core/chroma-ui) 