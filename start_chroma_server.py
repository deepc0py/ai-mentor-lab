#!/usr/bin/env python3
"""
Start a ChromaDB server for UI access.

This script starts a ChromaDB server that can be accessed by Chroma UI
(https://chroma-ui.vercel.app) for visualization and interaction.

Usage:
    python start_chroma_server.py [--host HOST] [--port PORT] [--persist-dir DIR]

Options:
    --host HOST         Host to bind the server to (default: localhost)
    --port PORT         Port to bind the server to (default: 8000)
    --persist-dir DIR   Directory where ChromaDB data is stored (default: ./chroma_db)
"""

import argparse
import sys
import os
import subprocess

def start_server(persist_directory: str, host: str, port: int):
    """Start a ChromaDB server for UI access using the CLI."""
    # Create directory if it doesn't exist
    os.makedirs(persist_directory, exist_ok=True)
    
    # Use the chromadb CLI to start the server
    cmd = [
        sys.executable, "-m", "chromadb.server",
        "--host", host,
        "--port", str(port),
        "--path", persist_directory
    ]
    
    # Start the server process (this will block until the server is stopped)
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Start a ChromaDB server for UI access")
    parser.add_argument("--host", type=str, default="localhost", 
                        help="Host to bind the server to (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, 
                        help="Port to bind the server to (default: 8000)")
    parser.add_argument("--persist-dir", type=str, default="./chroma_db", 
                        help="Directory where ChromaDB data is stored (default: ./chroma_db)")
    
    args = parser.parse_args()
    
    print("Starting ChromaDB server...")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Persist directory: {args.persist_dir}")
    print("\nConnect to this server using Chroma UI at https://chroma-ui.vercel.app")
    print(f"Use the following connection URL: http://{args.host}:{args.port}")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        # Start the ChromaDB server directly
        start_server(
            persist_directory=args.persist_dir,
            host=args.host,
            port=args.port
        )
    except KeyboardInterrupt:
        print("\nServer stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\nError starting server: {e}")
        print("\nTrying alternative method...")
        
        try:
            # Try using the ChromaDBManager as a fallback
            from rag.chroma_setup import ChromaDBManager
            ChromaDBManager.start_chroma_server(
                persist_directory=args.persist_dir,
                host=args.host,
                port=args.port
            )
        except Exception as e2:
            print(f"\nError with alternative method: {e2}")
            print("\nPlease check your ChromaDB installation and version.")
            sys.exit(1)

if __name__ == "__main__":
    main() 