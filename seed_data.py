from sqlmodel import Session, select
from app.db.database import engine
from app.db.models import (
    Student, HomeworkTemplate, ActivityTemplate
)
from datetime import datetime

def seed_database():
    """Seed the database with test data."""
    
    with Session(engine) as session:
        # Create a student
        student = Student(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            proficiency_level="Intermediate",
            basic_info={
                "native_language": "Spanish",
                "age": 30,
                "location": "Mexico City"
            },
            personal_background={
                "country_of_origin": "Mexico",
                "hometown": "Mexico City",
                "years_learning_english": 5
            },
            professional_background={
                "current_occupation": "Software Engineer",
                "company": "Tech Solutions",
                "industry": "Technology",
                "education_level": "Bachelor's Degree"
            },
            learning_context={
                "learning_goals": "Improve business communication and presentation skills",
                "preferred_learning_style": "Visual and practical",
                "strengths": "Good reading comprehension and vocabulary",
                "areas_for_improvement": "Pronunciation and speaking fluency"
            },
            interests=[
                {
                    "name": "Programming",
                    "category": "Technology",
                    "description": "Enjoys coding in Python and JavaScript"
                },
                {
                    "name": "Soccer",
                    "category": "Sports",
                    "description": "Plays soccer on weekends and follows international leagues"
                },
                {
                    "name": "Travel",
                    "category": "Leisure",
                    "description": "Likes to explore new countries and cultures"
                }
            ],
            cultural_elements={
                "cultural_background": "Mexican",
                "important_traditions": "Día de los Muertos, family gatherings"
            },
            social_aspects={
                "communication_style": "Reserved but friendly",
                "group_dynamics": "Prefers small groups"
            }
        )
        
        session.add(student)
        session.commit()
        session.refresh(student)
        print(f"Added student: {student.first_name} {student.last_name} (ID: {student.student_id})")
        
        # Create a homework template
        template = HomeworkTemplate(
            name="Business English Communication",
            objective="Practice professional email writing and business vocabulary",
            proficiency_level="Intermediate",
            class_id=1,
            questions=[
                {
                    "question": "Write a professional email to a client explaining a project delay.",
                    "instructions": "Use appropriate business email format, include apologies, explanation, and next steps.",
                    "expected_answer": "A properly formatted business email with appropriate tone, vocabulary, and structure."
                },
                {
                    "question": "Complete the following sentences with the correct business idioms.",
                    "instructions": "Choose from: 'ball park figure', 'touch base', 'in the loop', 'on the same page'",
                    "expected_answer": "1. Let's ___ before the meeting to discuss our strategy.\n2. Can you give me a ___ for the project cost?\n3. Please keep me ___ regarding the client's feedback.\n4. We need to make sure we're all ___ before presenting to the client."
                },
                {
                    "question": "Write a short presentation introducing your company to potential clients.",
                    "instructions": "Include: company background, services/products, unique selling points, and call to action.",
                    "expected_answer": "A well-structured 2-3 paragraph presentation with clear introduction, service description, and conclusion."
                }
            ],
            created_at=datetime.now()
        )
        
        session.add(template)
        session.commit()
        session.refresh(template)
        print(f"Added homework template: {template.name} (ID: {template.template_id})")
        
        # Create an activity template
        activity_template = ActivityTemplate(
            name="Business Meeting Simulation",
            objective="Practice vocabulary and phrases used in business meetings",
            proficiency_level="Intermediate",
            class_id=1,
            conversation_template={
                "scenario": "A product development meeting to discuss new features",
                "instructions": "Student 1 plays the role of meeting chair, Student 2 plays the role of product manager. Discuss 3 potential new features for your product and decide which one to implement first.",
                "prompts": [
                    "Discuss advantages and disadvantages of each feature",
                    "Use phrases for agreeing and disagreeing politely",
                    "Practice summarizing points and asking for clarification",
                    "Reach a conclusion and outline next steps"
                ]
            },
            created_at=datetime.now()
        )
        
        session.add(activity_template)
        session.commit()
        session.refresh(activity_template)
        print(f"Added activity template: {activity_template.name} (ID: {activity_template.template_id})")

if __name__ == "__main__":
    seed_database() 