import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChromaDBManager:
    """Manages ChromaDB operations for the ESL RAG application."""
    
    def __init__(self, persist_directory: str = "./chroma_db", start_server: bool = False, server_host: str = "localhost", server_port: int = 8000):
        """Initialize ChromaDB with persistence.
        
        Args:
            persist_directory: Directory to store ChromaDB data
            start_server: Whether to start a ChromaDB server (for UI access)
            server_host: Host to bind the server to
            server_port: Port to bind the server to
        """
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        if start_server:
            # Initialize the ChromaDB server for UI access
            self.client = chromadb.HttpClient(
                host=server_host,
                port=server_port
            )
            print(f"ChromaDB server started at http://{server_host}:{server_port}")
            print(f"You can connect to this server using Chroma UI at https://chroma-ui.vercel.app")
            print(f"Use the following connection URL: http://{server_host}:{server_port}")
        else:
            # Initialize the ChromaDB client with persistence (local mode)
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
        
        # Set up embedding function (using sentence-transformers)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"  # Lightweight model, good for local deployment
        )
        
        # Collection names
        self.HOMEWORK_COLLECTION = "homework_templates"
        self.ACTIVITY_COLLECTION = "activity_templates"
        self.STUDENT_PROFILES_COLLECTION = "student_profiles"
    
    @staticmethod
    def start_chroma_server(persist_directory: str = "./chroma_db", host: str = "localhost", port: int = 8000):
        """Start a ChromaDB server for UI access.
        
        This is a standalone method that can be called to start a ChromaDB server
        without initializing the full ChromaDBManager.
        
        Args:
            persist_directory: Directory where ChromaDB data is stored
            host: Host to bind the server to
            port: Port to bind the server to
        """
        import subprocess
        import sys
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        print(f"Starting ChromaDB server at http://{host}:{port}")
        print(f"You can connect to this server using Chroma UI at https://chroma-ui.vercel.app")
        print(f"Use the following connection URL: http://{host}:{port}")
        
        # Use the chromadb CLI to start the server
        # This is more reliable than using the Python API directly
        cmd = [
            sys.executable, "-m", "chromadb.server",
            "--host", host,
            "--port", str(port),
            "--path", persist_directory
        ]
        
        # Start the server process
        subprocess.run(cmd)
        
    def create_collections(self):
        """Create collections if they don't exist."""
        # Create or get collections
        self.homework_collection = self.client.get_or_create_collection(
            name=self.HOMEWORK_COLLECTION,
            embedding_function=self.embedding_function
        )
        
        self.activity_collection = self.client.get_or_create_collection(
            name=self.ACTIVITY_COLLECTION,
            embedding_function=self.embedding_function
        )
        
        self.student_profiles_collection = self.client.get_or_create_collection(
            name=self.STUDENT_PROFILES_COLLECTION,
            embedding_function=self.embedding_function
        )
        
        return {
            "homework": self.homework_collection,
            "activity": self.activity_collection,
            "student_profiles": self.student_profiles_collection
        }
    
    def add_homework_template(self, 
                              template_id: int, 
                              name: str, 
                              objective: str, 
                              questions: List[Dict],
                              class_id: int,
                              proficiency_level: str,
                              metadata: Optional[Dict[str, Any]] = None):
        """Add a homework template to the vector database."""
        # Combine all questions into a single text for embedding
        questions_text = "\n".join([
            f"Question: {q.get('question', '')}\n"
            f"Instructions: {q.get('instructions', '')}\n"
            f"Expected Answer: {q.get('expected_answer', '')}"
            for q in questions
        ])
        
        # Combine template metadata
        document_text = f"Template Name: {name}\nObjective: {objective}\n{questions_text}"
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "template_id": str(template_id),
            "class_id": str(class_id),
            "proficiency_level": proficiency_level,
            "template_name": name,
            "objective": objective,
            "added_at": datetime.now().isoformat()
        })
        
        # Add to collection
        self.homework_collection.add(
            documents=[document_text],
            metadatas=[metadata],
            ids=[f"homework_template_{template_id}"]
        )
        
        return f"homework_template_{template_id}"
    
    def add_activity_template(self, 
                             template_id: int, 
                             name: str, 
                             objective: str, 
                             conversation_template: Dict,
                             class_id: int,
                             proficiency_level: str,
                             metadata: Optional[Dict[str, Any]] = None):
        """Add an activity template to the vector database."""
        # Extract conversation parts
        if isinstance(conversation_template, dict):
            prompts = conversation_template.get("prompts", [])
            instructions = conversation_template.get("instructions", "")
            scenario = conversation_template.get("scenario", "")
            
            prompts_text = "\n".join([f"- {prompt}" for prompt in prompts])
            conversation_text = f"Scenario: {scenario}\nInstructions: {instructions}\nPrompts:\n{prompts_text}"
        else:
            conversation_text = str(conversation_template)
        
        # Combine template metadata
        document_text = f"Template Name: {name}\nObjective: {objective}\n{conversation_text}"
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "template_id": str(template_id),
            "class_id": str(class_id),
            "proficiency_level": proficiency_level,
            "template_name": name,
            "objective": objective,
            "added_at": datetime.now().isoformat()
        })
        
        # Add to collection
        self.activity_collection.add(
            documents=[document_text],
            metadatas=[metadata],
            ids=[f"activity_template_{template_id}"]
        )
        
        return f"activity_template_{template_id}"
    
    def add_student_profile(self, student_id: int, student_data: Dict[str, Any]):
        """Add a student profile to the vector database for better matching."""
        # Extract relevant profile information
        first_name = student_data.get("first_name", "")
        last_name = student_data.get("last_name", "")
        proficiency_level = student_data.get("proficiency_level", "")
        
        # Get additional profile information if available
        basic_info = student_data.get("basic_info", {})
        personal_background = student_data.get("personal_background", {})
        professional_background = student_data.get("professional_background", {})
        learning_context = student_data.get("learning_context", {})
        interests = student_data.get("interests", [])
        cultural_elements = student_data.get("cultural_elements", {})
        social_aspects = student_data.get("social_aspects", {})
        
        # Create a comprehensive student profile text
        profile_sections = [
            f"Student: {first_name} {last_name}",
            f"Proficiency Level: {proficiency_level}",
            f"Native Language: {basic_info.get('native_language', '')}",
            f"Country of Origin: {personal_background.get('country_of_origin', '')}",
            f"Hometown: {personal_background.get('hometown', '')}",
            f"Occupation: {professional_background.get('current_occupation', '')} at {professional_background.get('company', '')}",
            f"Industry: {professional_background.get('industry', '')}",
            f"Education Level: {professional_background.get('education_level', '')}",
            f"Learning Goals: {learning_context.get('learning_goals', '')}",
            f"Learning Style: {learning_context.get('preferred_learning_style', '')}",
            f"Strengths: {learning_context.get('strengths', '')}",
            f"Areas for Improvement: {learning_context.get('areas_for_improvement', '')}",
            f"Cultural Background: {cultural_elements.get('cultural_background', '')}",
            f"Communication Style: {social_aspects.get('communication_style', '')}"
        ]
        
        # Add interests
        interest_texts = []
        for interest in interests:
            interest_texts.append(
                f"Interest/Hobby: {interest.get('name', '')} ({interest.get('category', '')})"
                f" - {interest.get('description', '')}"
            )
        
        if interest_texts:
            profile_sections.append("Interests and Hobbies:")
            profile_sections.extend(interest_texts)
            
        # Combine into a single document
        profile_text = "\n".join(profile_sections)
        
        # Create metadata
        metadata = {
            "student_id": str(student_id),
            "first_name": first_name,
            "last_name": last_name,
            "proficiency_level": proficiency_level,
            "native_language": basic_info.get("native_language", ""),
            "added_at": datetime.now().isoformat()
        }
        
        # Add to collection
        self.student_profiles_collection.add(
            documents=[profile_text],
            metadatas=[metadata],
            ids=[f"student_profile_{student_id}"]
        )
        
        return f"student_profile_{student_id}"
    
    def search_homework_templates(self, 
                                query: str, 
                                n_results: int = 5,
                                filter_criteria: Optional[Dict[str, Any]] = None):
        """Search for similar homework templates based on query."""
        results = self.homework_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_criteria
        )
        
        return results
    
    def search_activity_templates(self, 
                                query: str, 
                                n_results: int = 5,
                                filter_criteria: Optional[Dict[str, Any]] = None):
        """Search for similar activity templates based on query."""
        results = self.activity_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_criteria
        )
        
        return results
    
    def find_compatible_students(self, 
                               student_id: int, 
                               n_results: int = 5,
                               filter_criteria: Optional[Dict[str, Any]] = None):
        """Find students who would be compatible for paired activities."""
        # First retrieve the student profile
        student_results = self.student_profiles_collection.get(
            ids=[f"student_profile_{student_id}"]
        )
        
        if not student_results["documents"]:
            raise ValueError(f"Student profile with ID {student_id} not found")
            
        student_profile = student_results["documents"][0]
        
        # Use the student profile as a query to find compatible students
        # Exclude the same student from results
        exclude_filter = {"student_id": {"$ne": str(student_id)}}
        
        # Combine with additional filters if provided
        if filter_criteria:
            combined_filter = {**exclude_filter, **filter_criteria}
        else:
            combined_filter = exclude_filter
            
        # Find similar students
        results = self.student_profiles_collection.query(
            query_texts=[student_profile],
            n_results=n_results,
            where=combined_filter
        )
        
        return results
    
    def update_homework_template(self, template_id: int, updated_data: Dict[str, Any]):
        """Update a homework template in the vector database."""
        # First delete the existing template
        self.homework_collection.delete(ids=[f"homework_template_{template_id}"])
        
        # Then add the updated template
        return self.add_homework_template(
            template_id=template_id,
            name=updated_data.get("name"),
            objective=updated_data.get("objective"),
            questions=updated_data.get("questions", []),
            class_id=updated_data.get("class_id"),
            proficiency_level=updated_data.get("proficiency_level"),
            metadata=updated_data.get("metadata", {})
        )
    
    def update_activity_template(self, template_id: int, updated_data: Dict[str, Any]):
        """Update an activity template in the vector database."""
        # First delete the existing template
        self.activity_collection.delete(ids=[f"activity_template_{template_id}"])
        
        # Then add the updated template
        return self.add_activity_template(
            template_id=template_id,
            name=updated_data.get("name"),
            objective=updated_data.get("objective"),
            conversation_template=updated_data.get("conversation_template", {}),
            class_id=updated_data.get("class_id"),
            proficiency_level=updated_data.get("proficiency_level"),
            metadata=updated_data.get("metadata", {})
        )
    
    def update_student_profile(self, student_id: int, updated_data: Dict[str, Any]):
        """Update a student profile in the vector database."""
        # First delete the existing profile
        self.student_profiles_collection.delete(ids=[f"student_profile_{student_id}"])
        
        # Then add the updated profile
        return self.add_student_profile(
            student_id=student_id,
            student_data=updated_data
        )