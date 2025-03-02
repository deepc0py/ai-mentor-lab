from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import re
import traceback

from .db_integration import RAGDatabaseIntegration

class HomeworkGenerator:
    """
    RAG-based ESL homework generator that creates personalized content
    based on student profiles and homework templates.
    """
    
    def __init__(self, openai_api_key: str, db_integration: RAGDatabaseIntegration):
        """Initialize with OpenAI API key and database integration."""
        try:
            self.openai_api_key = openai_api_key
            os.environ["OPENAI_API_KEY"] = openai_api_key
            
            print(f"Initializing ChatOpenAI with model gpt-4o")
            # Set up language model
            self.llm = ChatOpenAI(
                temperature=0.7,
                model_name="gpt-4o",  # Use a capable model for education content
                api_key=openai_api_key
            )
            print(f"ChatOpenAI initialized successfully: {self.llm}")
            
            # Store database integration
            self.db_integration = db_integration
        except Exception as e:
            print(f"Error initializing HomeworkGenerator: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def generate_personalized_homework(self, 
                                      student_id: int, 
                                      template_id: Optional[int] = None,
                                      class_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate personalized homework for a specific student."""
        try:
            # Get template and student data from DB integration
            template_data = self.db_integration.generate_personalized_homework(
                student_id=student_id,
                template_id=template_id,
                class_id=class_id
            )
            
            # If there was an error, return it
            if "error" in template_data:
                return template_data
            
            # Extract template and student information
            student_name = template_data["student_name"]
            template_name = template_data["template_name"]
            proficiency_level = template_data["proficiency_level"]
            template_questions = template_data["template_questions"]
            
            print(f"Creating personalization prompt for student: {student_name}")
            # Create personalization prompt for the LLM
            personalization_prompt = self._create_personalization_prompt(
                student_data=template_data["student_data"],
                template_metadata={
                    "name": template_name,
                    "proficiency_level": proficiency_level
                },
                base_questions=template_questions
            )
            
            print(f"Generating personalized content with LLM")
            # Generate personalized questions using LLM
            generated_content = self._generate_content(personalization_prompt)
            
            print(f"Extracting questions from generated content")
            # Extract questions from the generated content
            personalized_questions = self._extract_questions_from_text(generated_content)
            
            # Update the template data with personalized questions
            template_data["personalized_questions"] = personalized_questions
            template_data["generation_timestamp"] = datetime.now().isoformat()
            
            return template_data
            
        except Exception as e:
            print(f"Error generating personalized homework: {str(e)}")
            print(traceback.format_exc())
            return {
                "error": f"Error generating personalized homework: {str(e)}",
                "student_id": student_id,
                "template_id": template_id
            }
    
    def _extract_questions_from_document(self, document: str) -> List[Dict[str, Any]]:
        """Extract question objects from a document string."""
        try:
            # Handle case where document might be a JSON string
            if document.startswith("[") and document.endswith("]"):
                try:
                    return json.loads(document)
                except:
                    pass
            
            # Split the document into lines
            lines = document.split("\n")
            
            questions = []
            current_question = {}
            current_key = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for question markers
                if line.startswith("Question:") or line.startswith("Question "):
                    # Save previous question if exists
                    if current_question:
                        questions.append(current_question)
                    current_question = {"question": line.split(":", 1)[1].strip() if ":" in line else ""}
                    current_key = "question"
                elif line.startswith("Instructions:") or line.startswith("Instructions "):
                    current_question["instructions"] = line.split(":", 1)[1].strip() if ":" in line else ""
                    current_key = "instructions"
                elif line.startswith("Expected Answer:") or line.startswith("Expected Answer "):
                    current_question["expected_answer"] = line.split(":", 1)[1].strip() if ":" in line else ""
                    current_key = "expected_answer"
                elif current_key:
                    # Append to current field
                    current_question[current_key] += " " + line
            
            # Add the last question
            if current_question:
                questions.append(current_question)
                
            return questions
        
        except Exception as e:
            print(f"Error extracting questions from document: {str(e)}")
            return []
    
    def _create_personalization_prompt(self, 
                                      student_data: Dict[str, Any],
                                      template_metadata: Dict[str, Any],
                                      base_questions: List[Dict[str, Any]]) -> str:
        """Create a prompt for personalizing homework questions."""
        # Extract relevant student information
        student_name = f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}"
        proficiency_level = student_data.get('proficiency_level', '')
        
        # Extract interests, if available
        interests = []
        if student_data.get('interests'):
            interests = [interest.get('name', '') for interest in student_data.get('interests', [])]
        
        # Extract learning context, if available
        learning_goals = ""
        strengths = ""
        areas_for_improvement = ""
        
        if student_data.get('learning_context'):
            learning_context = student_data.get('learning_context', {})
            learning_goals = learning_context.get('learning_goals', '')
            strengths = learning_context.get('strengths', '')
            areas_for_improvement = learning_context.get('areas_for_improvement', '')
        
        # Extract professional background, if available
        occupation = ""
        industry = ""
        
        if student_data.get('professional_background'):
            prof_bg = student_data.get('professional_background', {})
            occupation = prof_bg.get('current_occupation', '')
            industry = prof_bg.get('industry', '')
        
        # Cultural background, if available
        cultural_background = ""
        if student_data.get('cultural_elements'):
            cultural_background = student_data.get('cultural_elements', {}).get('cultural_background', '')
        
        # Format base questions
        formatted_questions = ""
        for i, q in enumerate(base_questions):
            formatted_questions += f"Question {i+1}: {q.get('question', '')}\n"
            if 'instructions' in q:
                formatted_questions += f"Instructions: {q.get('instructions', '')}\n"
            if 'expected_answer' in q:
                formatted_questions += f"Expected Answer: {q.get('expected_answer', '')}\n"
            formatted_questions += "\n"
        
        # Create the prompt template
        prompt_template = """
        You are an expert ESL teacher creating personalized homework for your students.
        
        STUDENT PROFILE:
        - Name: {student_name}
        - Proficiency Level: {proficiency_level}
        - Learning Goals: {learning_goals}
        - Strengths: {strengths}
        - Areas for Improvement: {areas_for_improvement}
        - Interests: {interests}
        - Occupation: {occupation}
        - Industry: {industry}
        - Cultural Background: {cultural_background}
        
        HOMEWORK TEMPLATE:
        - Title: {template_name}
        - Proficiency Level: {template_proficiency_level}
        
        BASE QUESTIONS:
        {base_questions}
        
        TASK:
        Create personalized versions of each question that would be more engaging, relevant, and effective for this specific student.
        
        For each question:
        1. Adapt the content to match the student's interests, profession, and cultural background
        2. Keep the same grammatical structure and language learning objectives
        3. Match the difficulty to the student's proficiency level
        4. Address the student's specific learning goals and areas for improvement
        5. Include clear instructions and expected answers
        
        Use the EXACT same format as the base questions, with "Question:", "Instructions:", and "Expected Answer:" labels.
        Return ONLY the personalized questions without any additional text or explanations.
        """
        
        # Format the prompt
        prompt = prompt_template.format(
            student_name=student_name,
            proficiency_level=proficiency_level,
            learning_goals=learning_goals,
            strengths=strengths,
            areas_for_improvement=areas_for_improvement,
            interests=", ".join(interests) if interests else "Not specified",
            occupation=occupation or "Not specified",
            industry=industry or "Not specified",
            cultural_background=cultural_background or "Not specified",
            template_name=template_metadata.get("name", ""),
            template_proficiency_level=template_metadata.get("proficiency_level", ""),
            base_questions=formatted_questions
        )
        
        return prompt
    
    def _generate_content(self, prompt: str) -> str:
        """Generate personalized content using LLM."""
        try:
            # Create a prompt template
            prompt_template = PromptTemplate(
                template=prompt,
                input_variables=[]
            )
            
            # Format the prompt
            formatted_prompt = prompt_template.format()
            
            # Generate content directly with the LLM
            response = self.llm.invoke(formatted_prompt)
            
            # Extract the content from the response
            return response.content
        except Exception as e:
            print(f"Error generating content: {str(e)}")
            return ""
    
    def _extract_questions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract structured questions from generated text."""
        # Regular expressions for question parts
        question_pattern = r"Question(?:\s\d+)?:(.+?)(?=Instructions:|Question\s|$)"
        instructions_pattern = r"Instructions:(.+?)(?=Expected Answer:|Question\s|$)"
        expected_answer_pattern = r"Expected Answer:(.+?)(?=Question\s|$)"
        
        # Find all questions
        questions = []
        
        # Find all question starts
        for match in re.finditer(r"Question(?:\s\d+)?:", text):
            start_pos = match.start()
            end_pos = len(text)
            
            # Find the next question or end of text
            next_match = re.search(r"Question(?:\s\d+)?:", text[start_pos + 8:])
            if next_match:
                end_pos = start_pos + 8 + next_match.start()
            
            # Extract this question block
            question_block = text[start_pos:end_pos].strip()
            
            # Extract question parts
            q_match = re.search(question_pattern, question_block, re.DOTALL)
            i_match = re.search(instructions_pattern, question_block, re.DOTALL)
            a_match = re.search(expected_answer_pattern, question_block, re.DOTALL)
            
            question_obj = {}
            
            if q_match:
                question_obj["question"] = q_match.group(1).strip()
            
            if i_match:
                question_obj["instructions"] = i_match.group(1).strip()
            
            if a_match:
                question_obj["expected_answer"] = a_match.group(1).strip()
            
            if question_obj:
                questions.append(question_obj)
        
        return questions