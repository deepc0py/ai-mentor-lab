from typing import Optional, List, Dict, Any
from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from datetime import datetime, date
from pydantic import validator

class Student(SQLModel, table=True):
    """Student model representing an ESL learner."""
    student_id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(unique=True, index=True)
    proficiency_level: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    basic_info: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    personal_background: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    professional_background: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    learning_context: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    interests: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    cultural_elements: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    social_aspects: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    # Relationships
    homeworks: List["PersonalizedHomework"] = Relationship(back_populates="student")
    activity_groups_1: List["ActivityGroup"] = Relationship(
        back_populates="student1",
        sa_relationship_kwargs={"foreign_keys": "ActivityGroup.student_id_1"}
    )
    activity_groups_2: List["ActivityGroup"] = Relationship(
        back_populates="student2",
        sa_relationship_kwargs={"foreign_keys": "ActivityGroup.student_id_2"}
    )
    
    class Config:
        arbitrary_types_allowed = True


class HomeworkTemplate(SQLModel, table=True):
    """Template for generating personalized homework assignments."""
    template_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    objective: str
    proficiency_level: str
    class_id: int = Field(index=True)
    questions: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    homeworks: List["PersonalizedHomework"] = Relationship(back_populates="template")


class PersonalizedHomework(SQLModel, table=True):
    """Personalized homework assignment for a student."""
    homework_id: Optional[int] = Field(default=None, primary_key=True)
    template_id: int = Field(foreign_key="homeworktemplate.template_id")
    student_id: int = Field(foreign_key="student.student_id")
    generated_at: datetime = Field(default_factory=datetime.now)
    generation_status: str  # "Queued", "Processing", "Completed", "Failed"
    personalized_questions: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    
    # Relationships
    template: HomeworkTemplate = Relationship(back_populates="homeworks")
    student: Student = Relationship(back_populates="homeworks")


class ActivityTemplate(SQLModel, table=True):
    """Template for paired speaking/conversation activities."""
    template_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    objective: str
    proficiency_level: str
    class_id: int = Field(index=True)
    conversation_template: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    activity_groups: List["ActivityGroup"] = Relationship(back_populates="activity_template")


class ActivityGroup(SQLModel, table=True):
    """Group of students paired for an activity."""
    group_id: Optional[int] = Field(default=None, primary_key=True)
    activity_template_id: int = Field(foreign_key="activitytemplate.template_id")
    student_id_1: int = Field(foreign_key="student.student_id")
    student_id_2: int = Field(foreign_key="student.student_id")
    completion_date: date
    notes: Optional[str] = None
    
    # Relationships
    activity_template: ActivityTemplate = Relationship(back_populates="activity_groups")
    student1: Student = Relationship(
        back_populates="activity_groups_1",
        sa_relationship_kwargs={"foreign_keys": "ActivityGroup.student_id_1"}
    )
    student2: Student = Relationship(
        back_populates="activity_groups_2",
        sa_relationship_kwargs={"foreign_keys": "ActivityGroup.student_id_2"}
    )
