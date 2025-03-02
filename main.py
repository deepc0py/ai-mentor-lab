import os
import argparse
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from sqlmodel import Session, select
from app.db.database import engine, init_db
from app.db.models import (
    PersonalizedHomework, HomeworkTemplate, Student, 
    ActivityGroup, ActivityTemplate
)

from rag.chroma_setup import ChromaDBManager
from rag.db_integration import RAGDatabaseIntegration
from rag.homework_generator import HomeworkGenerator

import sys
import subprocess

# Load environment variables
load_dotenv()

def init_chroma_db(persist_dir: str = "./chroma_db") -> ChromaDBManager:
    """Initialize ChromaDB."""
    chroma_manager = ChromaDBManager(persist_directory=persist_dir)
    chroma_manager.create_collections()
    return chroma_manager

def sync_data_to_chroma(db_integration: RAGDatabaseIntegration) -> Dict[str, Any]:
    """Sync all relevant data from PostgreSQL to ChromaDB."""
    results = {}
    
    # Sync homework templates
    print("Syncing homework templates...")
    homework_results = db_integration.sync_all_homework_templates()
    results["homework_templates"] = len(homework_results)
    
    # Sync activity templates
    print("Syncing activity templates...")
    activity_results = db_integration.sync_all_activity_templates()
    results["activity_templates"] = len(activity_results)
    
    # Sync student profiles
    print("Syncing student profiles...")
    student_results = db_integration.sync_all_student_profiles()
    results["student_profiles"] = len(student_results)
    
    return results

def generate_homework(
    generator: HomeworkGenerator,
    student_id: int,
    template_id: Optional[int] = None,
    class_id: Optional[int] = None,
    save_to_db: bool = True
) -> Dict[str, Any]:
    """Generate personalized homework for a student and optionally save to database."""
    # Generate the homework
    result = generator.generate_personalized_homework(
        student_id=student_id,
        template_id=template_id,
        class_id=class_id
    )
    
    # Save to database if requested
    if save_to_db and not result.get("error"):
        with Session(engine) as session:
            # Create a new personalized homework entry
            homework = PersonalizedHomework(
                template_id=result["template_id"],
                student_id=result["student_id"],
                generated_at=datetime.now(),
                generation_status="Completed",
                personalized_questions=result["personalized_questions"]
            )
            
            session.add(homework)
            session.commit()
            session.refresh(homework)
            
            # Add the homework ID to the result
            result["homework_id"] = homework.homework_id
    
    return result

def generate_activity_pairings(
    db_integration: RAGDatabaseIntegration,
    class_id: int,
    activity_template_id: Optional[int] = None,
    save_to_db: bool = True
) -> Dict[str, Any]:
    """Generate student pairings for activities and optionally save to database."""
    # Generate the pairings
    result = db_integration.generate_activity_pairings(
        class_id=class_id,
        activity_template_id=activity_template_id
    )
    
    # Save to database if requested
    if save_to_db and result.get("pairings"):
        with Session(engine) as session:
            saved_groups = []
            
            for pairing in result["pairings"]:
                if not pairing.get("activity_template") or not pairing["activity_template"].get("template_id"):
                    continue
                    
                # Create a new activity group
                group = ActivityGroup(
                    activity_template_id=pairing["activity_template"]["template_id"],
                    student_id_1=pairing["student1_id"],
                    student_id_2=pairing["student2_id"],
                    completion_date=datetime.now().date()  # Set to today as default
                )
                
                session.add(group)
                session.commit()
                session.refresh(group)
                
                # Add the group ID to the pairing
                pairing["group_id"] = group.group_id
                saved_groups.append({
                    "group_id": group.group_id,
                    "student1_id": pairing["student1_id"],
                    "student2_id": pairing["student2_id"],
                    "activity_template_id": pairing["activity_template"]["template_id"]
                })
            
            result["saved_groups"] = saved_groups
    
    return result

def main():
    """Main function to run the ESL RAG application."""
    parser = argparse.ArgumentParser(description="ESL Teaching Assistant CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Initialize database command
    init_parser = subparsers.add_parser("init", help="Initialize ChromaDB")
    init_parser.add_argument("--persist-dir", type=str, default="./chroma_db", help="ChromaDB persistence directory")
    
    # Sync data command
    sync_parser = subparsers.add_parser("sync", help="Sync data from PostgreSQL to ChromaDB")
    sync_parser.add_argument("--persist-dir", type=str, default="./chroma_db", help="ChromaDB persistence directory")
    
    # Generate homework command
    homework_parser = subparsers.add_parser("homework", help="Generate personalized homework")
    homework_parser.add_argument("--student-id", type=int, required=True, help="Student ID")
    homework_parser.add_argument("--template-id", type=int, help="Homework template ID (optional)")
    homework_parser.add_argument("--class-id", type=int, help="Class ID (optional)")
    homework_parser.add_argument("--persist-dir", type=str, default="./chroma_db", help="ChromaDB persistence directory")
    homework_parser.add_argument("--no-save", action="store_true", help="Don't save to database")
    
    # Generate activity pairings command
    pairings_parser = subparsers.add_parser("pairings", help="Generate activity pairings")
    pairings_parser.add_argument("--class-id", type=int, required=True, help="Class ID")
    pairings_parser.add_argument("--template-id", type=int, help="Activity template ID (optional)")
    pairings_parser.add_argument("--persist-dir", type=str, default="./chroma_db", help="ChromaDB persistence directory")
    pairings_parser.add_argument("--no-save", action="store_true", help="Don't save to database")
    
    # Start ChromaDB server command
    server_parser = subparsers.add_parser("server", help="Start ChromaDB server for UI access")
    server_parser.add_argument("--host", type=str, default="localhost", help="Host to bind the server to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    server_parser.add_argument("--persist-dir", type=str, default="./chroma_db", help="ChromaDB persistence directory")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize the database if needed
    if args.command == "init":
        # Initialize ChromaDB
        print(f"Initializing ChromaDB in {args.persist_dir}...")
        init_chroma_db(args.persist_dir)
        print("ChromaDB initialized successfully")
    
    elif args.command == "sync":
        print(f"Syncing data to ChromaDB in {args.persist_dir}...")
        db_integration = RAGDatabaseIntegration(chroma_persist_dir=args.persist_dir)
        results = sync_data_to_chroma(db_integration)
        print(f"Sync complete. Synced {results['homework_templates']} homework templates, "
              f"{results['activity_templates']} activity templates, and "
              f"{results['student_profiles']} student profiles.")
    
    elif args.command == "homework":
        db_integration = RAGDatabaseIntegration(chroma_persist_dir=args.persist_dir)
        generator = HomeworkGenerator(db_integration)
        
        result = generate_homework(
            generator=generator,
            student_id=args.student_id,
            template_id=args.template_id,
            class_id=args.class_id,
            save_to_db=not args.no_save
        )
        
        print(json.dumps(result, indent=2))
    
    elif args.command == "pairings":
        db_integration = RAGDatabaseIntegration(chroma_persist_dir=args.persist_dir)
        
        result = generate_activity_pairings(
            db_integration=db_integration,
            class_id=args.class_id,
            activity_template_id=args.template_id,
            save_to_db=not args.no_save
        )
        
        print(json.dumps(result, indent=2))
    
    elif args.command == "server":
        print(f"Starting ChromaDB server at http://{args.host}:{args.port}")
        print(f"Connect to this server using Chroma UI at https://chroma-ui.vercel.app")
        print(f"Use the following connection URL: http://{args.host}:{args.port}")
        print("\nPress Ctrl+C to stop the server")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(args.persist_dir, exist_ok=True)
            
            # Use the chromadb CLI to start the server
            cmd = [
                sys.executable, "-m", "chromadb.server",
                "--host", args.host,
                "--port", str(args.port),
                "--path", args.persist_dir
            ]
            
            # Start the server process
            subprocess.run(cmd)
            
        except KeyboardInterrupt:
            print("\nServer stopped")
        except Exception as e:
            print(f"\nError starting server: {e}")
            print("\nTrying alternative method...")
            
            try:
                # Try using the ChromaDBManager as a fallback
                ChromaDBManager.start_chroma_server(
                    persist_directory=args.persist_dir,
                    host=args.host,
                    port=args.port
                )
            except Exception as e2:
                print(f"\nError with alternative method: {e2}")
                print("\nPlease check your ChromaDB installation and version.")

if __name__ == "__main__":
    main()