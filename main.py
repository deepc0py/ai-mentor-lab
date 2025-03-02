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
    parser = argparse.ArgumentParser(description="ESL RAG Application")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize ChromaDB")
    init_parser.add_argument("--persist-dir", type=str, default="./chroma_db", help="ChromaDB persistence directory")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync data from PostgreSQL to ChromaDB")
    sync_parser.add_argument("--persist-dir", type=str, default="./chroma_db", help="ChromaDB persistence directory")
    
    # Generate homework command
    homework_parser = subparsers.add_parser("homework", help="Generate personalized homework")
    homework_parser.add_argument("--student-id", type=int, required=True, help="Student ID")
    homework_parser.add_argument("--template-id", type=int, help="Homework template ID (optional)")
    homework_parser.add_argument("--class-id", type=int, help="Class ID (optional)")
    homework_parser.add_argument("--no-save", action="store_true", help="Don't save to database")
    homework_parser.add_argument("--persist-dir", type=str, default="./chroma_db", help="ChromaDB persistence directory")
    homework_parser.add_argument("--output", type=str, help="Output file for JSON results")
    homework_parser.add_argument("--api-key", type=str, help="OpenAI API key (overrides environment variable)")
    
    # Generate pairings command
    pairings_parser = subparsers.add_parser("pairings", help="Generate student pairings for activities")
    pairings_parser.add_argument("--class-id", type=int, required=True, help="Class ID")
    pairings_parser.add_argument("--template-id", type=int, help="Activity template ID (optional)")
    pairings_parser.add_argument("--no-save", action="store_true", help="Don't save to database")
    pairings_parser.add_argument("--persist-dir", type=str, default="./chroma_db", help="ChromaDB persistence directory")
    pairings_parser.add_argument("--output", type=str, help="Output file for JSON results")
    pairings_parser.add_argument("--api-key", type=str, help="OpenAI API key (overrides environment variable)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check for OpenAI API key
    openai_api_key = args.api_key if hasattr(args, 'api_key') and args.api_key else os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key and args.command in ["homework", "pairings"]:
        print("Error: OPENAI_API_KEY environment variable not set and --api-key not provided")
        return
    else:
        if openai_api_key:
            print(f"OpenAI API key is set {'from command line' if hasattr(args, 'api_key') and args.api_key else 'from environment'}")
            os.environ["OPENAI_API_KEY"] = openai_api_key
    
    # Execute commands
    if args.command == "init":
        print(f"Initializing databases...")
        # Initialize SQL database
        print("Initializing SQL database...")
        init_db()
        print("SQL database initialized successfully")
        
        # Initialize ChromaDB
        print(f"Initializing ChromaDB in {args.persist_dir}...")
        init_chroma_db(args.persist_dir)
        print("ChromaDB initialized successfully")
    
    elif args.command == "sync":
        print(f"Syncing data to ChromaDB in {args.persist_dir}...")
        db_integration = RAGDatabaseIntegration(chroma_persist_dir=args.persist_dir)
        results = sync_data_to_chroma(db_integration)
        print(f"Sync completed: {json.dumps(results, indent=2)}")
    
    elif args.command == "homework":
        print(f"Generating personalized homework for student {args.student_id}...")
        db_integration = RAGDatabaseIntegration(chroma_persist_dir=args.persist_dir)
        generator = HomeworkGenerator(openai_api_key=openai_api_key, db_integration=db_integration)
        
        result = generate_homework(
            generator=generator,
            student_id=args.student_id,
            template_id=args.template_id,
            class_id=args.class_id,
            save_to_db=not args.no_save
        )
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
                print(f"Results saved to {args.output}")
        else:
            print(json.dumps(result, indent=2))
    
    elif args.command == "pairings":
        print(f"Generating student pairings for class {args.class_id}...")
        db_integration = RAGDatabaseIntegration(chroma_persist_dir=args.persist_dir)
        
        result = generate_activity_pairings(
            db_integration=db_integration,
            class_id=args.class_id,
            activity_template_id=args.template_id,
            save_to_db=not args.no_save
        )
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
                print(f"Results saved to {args.output}")
        else:
            print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()