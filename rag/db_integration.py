from sqlmodel import Session, select
from app.db.database import engine
from app.db.models import (
    Student, HomeworkTemplate, ActivityTemplate, 
    PersonalizedHomework, ActivityGroup
)
from typing import Dict, List, Any, Optional
import json

from .chroma_setup import ChromaDBManager

class RAGDatabaseIntegration:
    """Integrates PostgreSQL and ChromaDB for the ESL RAG application."""
    
    def __init__(self, chroma_persist_dir: str = "./chroma_db"):
        """Initialize with both databases."""
        self.engine = engine
        self.chroma_manager = ChromaDBManager(persist_directory=chroma_persist_dir)
        self.collections = self.chroma_manager.create_collections()
    
    def sync_all_homework_templates(self):
        """Sync all homework templates from PostgreSQL to ChromaDB."""
        with Session(self.engine) as session:
            # Get all homework templates
            statement = select(HomeworkTemplate)
            results = session.exec(statement).all()
            
            synced_ids = []
            for template in results:
                # Format for ChromaDB
                template_id = self.chroma_manager.add_homework_template(
                    template_id=template.template_id,
                    name=template.name,
                    objective=template.objective,
                    questions=template.questions,
                    class_id=template.class_id,
                    proficiency_level=template.proficiency_level
                )
                synced_ids.append(template_id)
            
            return synced_ids
    
    def sync_all_activity_templates(self):
        """Sync all activity templates from PostgreSQL to ChromaDB."""
        with Session(self.engine) as session:
            # Get all activity templates
            statement = select(ActivityTemplate)
            results = session.exec(statement).all()
            
            synced_ids = []
            for template in results:
                # Format for ChromaDB
                template_id = self.chroma_manager.add_activity_template(
                    template_id=template.template_id,
                    name=template.name,
                    objective=template.objective,
                    conversation_template=template.conversation_template,
                    class_id=template.class_id,
                    proficiency_level=template.proficiency_level
                )
                synced_ids.append(template_id)
            
            return synced_ids
    
    def sync_all_student_profiles(self):
        """Sync all student profiles from PostgreSQL to ChromaDB."""
        with Session(self.engine) as session:
            # Get all students
            statement = select(Student)
            results = session.exec(statement).all()
            
            synced_ids = []
            for student in results:
                # Get complete student data
                student_data = self._get_complete_student_data(session, student.student_id)
                
                # Add to ChromaDB
                profile_id = self.chroma_manager.add_student_profile(
                    student_id=student.student_id,
                    student_data=student_data
                )
                synced_ids.append(profile_id)
            
            return synced_ids
    
    def _get_complete_student_data(self, session: Session, student_id: int) -> Dict[str, Any]:
        """Get complete student data including all related information."""
        # Get the student
        statement = select(Student).where(Student.student_id == student_id)
        student = session.exec(statement).first()
        
        if not student:
            raise ValueError(f"Student with ID {student_id} not found")
            
        # Compile all student data into a dictionary
        student_data = {
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "email": student.email,
            "proficiency_level": student.proficiency_level,
            "basic_info": student.basic_info,
            "personal_background": student.personal_background,
            "professional_background": student.professional_background,
            "learning_context": student.learning_context,
            "interests": student.interests,
            "cultural_elements": student.cultural_elements,
            "social_aspects": student.social_aspects
        }
        
        return student_data
    
    def generate_personalized_homework(self, 
                                      student_id: int, 
                                      template_id: Optional[int] = None,
                                      class_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate personalized homework for a student using RAG approach."""
        with Session(self.engine) as session:
            # Get student profile
            student = session.exec(select(Student).where(Student.student_id == student_id)).first()
            if not student:
                return {"error": f"Student with ID {student_id} not found"}
            
            # Get complete student data
            student_data = self._get_complete_student_data(session, student_id)
            
            # If template_id is provided, use that specific template
            if template_id:
                template = session.exec(
                    select(HomeworkTemplate).where(HomeworkTemplate.template_id == template_id)
                ).first()
                
                if not template:
                    return {"error": f"Homework template with ID {template_id} not found"}
                
                # Return template with student context
                return {
                    "template_id": template.template_id,
                    "student_id": student_id,
                    "template_name": template.name,
                    "student_name": f"{student.first_name} {student.last_name}",
                    "proficiency_level": student.proficiency_level,
                    "template_questions": template.questions,
                    "personalized_questions": template.questions,  # Placeholder, to be implemented with LLM
                    "student_data": student_data
                }
            
            # If class_id is provided, find templates for that class
            filter_criteria = {}
            if class_id:
                filter_criteria["class_id"] = str(class_id)
            
            # Find suitable homework templates for this student
            query = f"Student: {student.first_name} {student.last_name}, "
            query += f"Proficiency Level: {student.proficiency_level}, "
            
            # Add more context from student profile
            if student.interests:
                interests = [interest.get("name", "") for interest in student.interests]
                query += f"Interests: {', '.join(interests)}, "
            
            if student.professional_background:
                query += f"Occupation: {student.professional_background.get('current_occupation', '')}, "
            
            if student.learning_context:
                query += f"Learning Goals: {student.learning_context.get('learning_goals', '')}"
            
            # Search for templates
            template_results = self.chroma_manager.search_homework_templates(
                query=query,
                n_results=3,
                filter_criteria=filter_criteria
            )
            
            if not template_results["ids"][0]:
                return {"error": "No suitable homework templates found"}
            
            # Get the best matching template ID
            template_id = int(template_results["metadatas"][0][0]["template_id"])
            
            # Get the template from database
            template = session.exec(
                select(HomeworkTemplate).where(HomeworkTemplate.template_id == template_id)
            ).first()
            
            # Return template with student context
            return {
                "template_id": template.template_id,
                "student_id": student_id,
                "template_name": template.name,
                "student_name": f"{student.first_name} {student.last_name}",
                "proficiency_level": student.proficiency_level,
                "template_questions": template.questions,
                "personalized_questions": template.questions,  # Placeholder, to be implemented with LLM
                "student_data": student_data
            }
    
    def generate_activity_pairings(self, 
                                  class_id: int,
                                  activity_template_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate student pairings for conversation activities."""
        with Session(self.engine) as session:
            # Get all students in the class
            # Note: Since we don't have a Class model, we're assuming students would have a class_id field
            # or there would be a separate ClassStudent relationship model.
            # For now, we'll just get all students
            students = session.exec(select(Student)).all()
            
            if len(students) < 2:
                return {"error": "Not enough students for pairings"}
            
            # If template_id is provided, use that specific template
            if activity_template_id:
                template = session.exec(
                    select(ActivityTemplate).where(ActivityTemplate.template_id == activity_template_id)
                ).first()
                
                if not template:
                    return {"error": f"Activity template with ID {activity_template_id} not found"}
            else:
                # Find a suitable activity template
                template = session.exec(
                    select(ActivityTemplate).where(ActivityTemplate.class_id == class_id)
                ).first()
                
                if not template:
                    return {"error": f"No activity templates found for class {class_id}"}
            
            # Create pairings (simple approach - consecutive pairs)
            pairings = []
            for i in range(0, len(students) - 1, 2):
                if i + 1 < len(students):
                    student1 = students[i]
                    student2 = students[i + 1]
                    
                    pairings.append({
                        "student1_id": student1.student_id,
                        "student1_name": f"{student1.first_name} {student1.last_name}",
                        "student2_id": student2.student_id,
                        "student2_name": f"{student2.first_name} {student2.last_name}",
                        "activity_template": {
                            "template_id": template.template_id,
                            "name": template.name,
                            "objective": template.objective
                        }
                    })
            
            # If odd number of students, add the last one to a group of 3
            if len(students) % 2 != 0 and pairings:
                last_student = students[-1]
                pairings[-1]["student3_id"] = last_student.student_id
                pairings[-1]["student3_name"] = f"{last_student.first_name} {last_student.last_name}"
            
            return {"pairings": pairings}