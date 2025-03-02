#!/usr/bin/env python3
"""
Start a ChromaDB server using direct API calls.

This script starts a ChromaDB server that can be accessed by Chroma UI
(https://chroma-ui.vercel.app) for visualization and interaction.

Usage:
    python run_chroma_server.py [--host HOST] [--port PORT] [--persist-dir DIR]

Options:
    --host HOST         Host to bind the server to (default: localhost)
    --port PORT         Port to bind the server to (default: 8000)
    --persist-dir DIR   Directory where ChromaDB data is stored (default: ./chroma_db)
"""

import argparse
import os
import sys
import subprocess
import shutil

def main():
    parser = argparse.ArgumentParser(description="Start a ChromaDB server for UI access")
    parser.add_argument("--host", type=str, default="localhost", 
                        help="Host to bind the server to (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, 
                        help="Port to bind the server to (default: 8000)")
    parser.add_argument("--persist-dir", type=str, default="./chroma_db", 
                        help="Directory where ChromaDB data is stored (default: ./chroma_db)")
    
    args = parser.parse_args()
    
    # Create directory if it doesn't exist
    os.makedirs(args.persist_dir, exist_ok=True)
    
    print("Starting ChromaDB server...")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Persist directory: {args.persist_dir}")
    print("\nConnect to this server using Chroma UI at https://chroma-ui.vercel.app")
    print(f"Use the following connection URL: http://{args.host}:{args.port}")
    print("\nPress Ctrl+C to stop the server")
    
    # Try to import ChromaDB to check version
    try:
        import chromadb
        print(f"ChromaDB version: {chromadb.__version__}")
        
        # Check if the chroma CLI command is available
        chroma_cmd = shutil.which("chroma")
        if chroma_cmd:
            print("Using 'chroma run' command")
            cmd = [
                chroma_cmd,
                "run",
                "--host", args.host,
                "--port", str(args.port),
                "--path", args.persist_dir
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            subprocess.run(cmd)
            return
        
        # If chroma command is not available, try other approaches
        print("'chroma' command not found, trying alternative approaches")
        
        # For version 0.4.x, try different approaches
        if chromadb.__version__.startswith("0.4."):
            # Try using the API directly
            print("Trying to start server using API directly")
            from chromadb.config import Settings
            
            # Create a persistent client
            client = chromadb.PersistentClient(
                path=args.persist_dir,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            # Try to access the server class
            if hasattr(chromadb, 'Server'):
                print("Using chromadb.Server API")
                server = chromadb.Server(
                    client,
                    host=args.host,
                    port=args.port
                )
                server.run()
                return
        
        # For newer versions, try different approaches
        if hasattr(chromadb, 'serve'):
            print("Using chromadb.serve API")
            from chromadb.config import Settings
            
            # Create a persistent client
            client = chromadb.PersistentClient(
                path=args.persist_dir,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            chromadb.serve(
                host=args.host,
                port=args.port,
                client=client
            )
            return
        
        # If all else fails, try the python module approach
        python_executable = sys.executable
        module_paths = [
            "chromadb.server",
            "chromadb.app",
            "chromadb"
        ]
        
        for module_path in module_paths:
            print(f"Trying module path: {module_path}")
            cmd = [
                python_executable, 
                "-m", 
                module_path,
                "--host", args.host,
                "--port", str(args.port),
                "--path", args.persist_dir
            ]
            
            try:
                print(f"Running command: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
                return
            except subprocess.CalledProcessError:
                print(f"Failed to start server with module path: {module_path}")
                continue
            
    except ImportError as e:
        print(f"Error importing ChromaDB: {e}")
        print("Please make sure ChromaDB is installed correctly.")
    except Exception as e:
        print(f"Error starting server: {e}")
    
    # If we get here, all approaches failed
    print("\nAll approaches failed. Please try running the server directly with:")
    print("chroma run --host localhost --port 8000 --path ./chroma_db")
    print("Or update ChromaDB with: pip install -U chromadb")
    
    sys.exit(1)

if __name__ == "__main__":
    main() 