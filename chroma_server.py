#!/usr/bin/env python3
"""
Start a ChromaDB server for UI access.

This script starts a ChromaDB server that can be accessed by Chroma UI
(https://chroma-ui.vercel.app) for visualization and interaction.

Usage:
    python chroma_server.py [--host HOST] [--port PORT] [--persist-dir DIR]

Options:
    --host HOST         Host to bind the server to (default: localhost)
    --port PORT         Port to bind the server to (default: 8000)
    --persist-dir DIR   Directory where ChromaDB data is stored (default: ./chroma_db)
"""

import argparse
import sys
import os
import subprocess
import importlib.util

def is_module_available(module_name):
    """Check if a module is available for import."""
    return importlib.util.find_spec(module_name) is not None

def start_server_direct(host, port, persist_dir):
    """Start the ChromaDB server directly using the Python API."""
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Create directory if it doesn't exist
        os.makedirs(persist_dir, exist_ok=True)
        
        # Create a persistent client
        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Try to access the server module
        if hasattr(chromadb, 'serve'):
            # Newer versions of ChromaDB
            chromadb.serve(
                host=host,
                port=port,
                client=client
            )
        else:
            print("ChromaDB server module not found. Please try a different approach.")
            return False
            
        return True
    except Exception as e:
        print(f"Error starting server directly: {e}")
        return False

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
    
    # Get the path to the Python executable in the virtual environment
    python_executable = sys.executable
    
    # Try different approaches to start the server
    
    # Approach 1: Try using the direct API
    print("Trying to start server using direct API...")
    if start_server_direct(args.host, args.port, args.persist_dir):
        return
    
    # Approach 2: Try different module paths
    module_paths = [
        "chromadb.server",
        "chromadb.server.app",
        "chromadb.app",
        "chromadb"
    ]
    
    for module_path in module_paths:
        print(f"Trying to start server using module: {module_path}...")
        
        cmd = [
            python_executable, "-m", module_path,
            "--host", args.host,
            "--port", str(args.port),
            "--path", args.persist_dir
        ]
        
        try:
            # Start the server process
            subprocess.run(cmd)
            # If we get here, the server started successfully
            return
        except KeyboardInterrupt:
            print("\nServer stopped")
            sys.exit(0)
        except Exception as e:
            print(f"Error with module {module_path}: {e}")
            continue
    
    # If all approaches failed, try a direct import and execution
    print("\nAll module approaches failed. Trying direct import...")
    try:
        import chromadb
        print("ChromaDB version:", chromadb.__version__)
        
        # Check if there's a CLI command available
        if hasattr(chromadb, 'cli'):
            print("Found ChromaDB CLI. Trying to start server...")
            chromadb.cli.start_server(host=args.host, port=args.port, path=args.persist_dir)
            return
    except Exception as e:
        print(f"Error with direct import: {e}")
    
    # If we get here, all approaches failed
    print("\nAll approaches failed. Please try running the server directly with one of these commands:")
    print(f"1. {python_executable} -m chromadb.server --host {args.host} --port {args.port} --path {args.persist_dir}")
    print(f"2. {python_executable} -m chromadb --host {args.host} --port {args.port} --path {args.persist_dir}")
    print(f"3. {python_executable} -c 'import chromadb; chromadb.Server(chromadb.PersistentClient(\"{args.persist_dir}\"), host=\"{args.host}\", port={args.port}).run()'")
    
    # Check installed packages to help with debugging
    print("\nInstalled packages that might help:")
    subprocess.run([python_executable, "-m", "pip", "list", "|", "grep", "chroma"], shell=True)
    
    sys.exit(1)

if __name__ == "__main__":
    main() 