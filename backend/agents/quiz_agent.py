from typing import List, Dict, Optional
from datetime import datetime
import uuid
import random
import json
from loguru import logger
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from models import (
    QuizGenerationRequest, QuizResponse, QuizQuestion,
    AnswerSubmission, AnswerFeedback, QuizGrading,
    QuestionType, QuizMode, Citation
)
from services import (
    chroma_service, ollama_service, embedding_service
)
from config import settings

class QuizAgent:
    """
    Quiz Agent - Generates and grades quizzes.
    Supports multiple question types and grading with citations.
    """
    
    def __init__(self):
        self.chroma = chroma_service
        self.ollama = ollama_service
        self.embedding = embedding_service
        self.active_quizzes: Dict[str, QuizResponse] = {}
    
    def _extract_topic_documents(self, topic: Optional[str] = None) -> List[Dict]:
        """Extract documents relevant to a specific topic or all documents."""
        if topic:
            results = self.chroma.query_similar(
                query_text=topic,
                n_results=20
            )
            documents = []
            if results['documents'] and results['documents'][0]:
                for doc, metadata in zip(
                    results['documents'][0],
                    results['metadatas'][0]
                ):
                    documents.append({
                        'text': doc,
                        'metadata': metadata
                    })
        else:
            # Get random documents
            all_docs = self.chroma.get_all_documents()
            documents = []
            if all_docs['documents']:
                for doc, metadata in zip(
                    all_docs['documents'][:50],  # Limit to first 50
                    all_docs['metadatas'][:50]
                ):
                    documents.append({
                        'text': doc,
                        'metadata': metadata
                    })
        
        return documents
    
    def _generate_mcq(self, context: str, metadata: dict) -> Optional[QuizQuestion]:
        """Generate a multiple-choice question from context."""
        prompt = f"""Based on the following network security content, create ONE multiple-choice question with 4 options.

Content: {context[:1000]}

Generate the question in this EXACT JSON format:
{{
    "question": "Your question here",
    "options": ["A) option 1", "B) option 2", "C) option 3", "D) option 4"],
    "correct_answer": "A) correct option",
    "topic": "main topic of question"
}}

Only output valid JSON, nothing else."""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                temperature=0.8
            )
            
            # Extract JSON from response
            json_match = response.strip()
            # Try to find JSON in the response
            if '{' in json_match and '}' in json_match:
                start = json_match.find('{')
                end = json_match.rfind('}') + 1
                json_match = json_match[start:end]
            
            data = json.loads(json_match)
            
            return QuizQuestion(
                id=str(uuid.uuid4()),
                type=QuestionType.MULTIPLE_CHOICE,
                question=data['question'],
                options=data['options'],
                correct_answer=data['correct_answer'],
                topic=data.get('topic', 'Network Security'),
                citation=Citation(
                    source=metadata.get('source', 'Unknown'),
                    content=context[:300],
                    page=metadata.get('page'),
                    confidence=0.9
                )
            )
        except Exception as e:
            logger.error(f"Error generating MCQ: {e}")
            return None
    
    def _generate_true_false(self, context: str, metadata: dict) -> Optional[QuizQuestion]:
        """Generate a true/false question from context."""
        prompt = f"""Based on the following network security content, create ONE true/false question.

Content: {context[:1000]}

Generate the question in this EXACT JSON format:
{{
    "question": "Your statement here",
    "correct_answer": "True" or "False",
    "topic": "main topic"
}}

Only output valid JSON, nothing else."""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                temperature=0.8
            )
            
            # Extract JSON
            json_match = response.strip()
            if '{' in json_match and '}' in json_match:
                start = json_match.find('{')
                end = json_match.rfind('}') + 1
                json_match = json_match[start:end]
            
            data = json.loads(json_match)
            
            return QuizQuestion(
                id=str(uuid.uuid4()),
                type=QuestionType.TRUE_FALSE,
                question=data['question'],
                options=["True", "False"],
                correct_answer=data['correct_answer'],
                topic=data.get('topic', 'Network Security'),
                citation=Citation(
                    source=metadata.get('source', 'Unknown'),
                    content=context[:300],
                    page=metadata.get('page'),
                    confidence=0.9
                )
            )
        except Exception as e:
            logger.error(f"Error generating T/F question: {e}")
            return None
    
    def _generate_open_ended(self, context: str, metadata: dict) -> Optional[QuizQuestion]:
        """Generate an open-ended question from context."""
        prompt = f"""Based on the following network security content, create ONE open-ended question that requires a detailed answer.

Content: {context[:1000]}

Generate the question in this EXACT JSON format:
{{
    "question": "Your question here",
    "correct_answer": "Expected detailed answer",
    "topic": "main topic"
}}

Only output valid JSON, nothing else."""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                temperature=0.8
            )
            
            # Extract JSON
            json_match = response.strip()
            if '{' in json_match and '}' in json_match:
                start = json_match.find('{')
                end = json_match.rfind('}') + 1
                json_match = json_match[start:end]
            
            data = json.loads(json_match)
            
            return QuizQuestion(
                id=str(uuid.uuid4()),
                type=QuestionType.OPEN_ENDED,
                question=data['question'],
                options=None,
                correct_answer=data['correct_answer'],
                topic=data.get('topic', 'Network Security'),
                citation=Citation(
                    source=metadata.get('source', 'Unknown'),
                    content=context[:300],
                    page=metadata.get('page'),
                    confidence=0.9
                )
            )
        except Exception as e:
            logger.error(f"Error generating open-ended question: {e}")
            return None
    
    def generate_quiz(self, request: QuizGenerationRequest) -> QuizResponse:
        """
        Generate a quiz based on the request parameters.
        
        Args:
            request: QuizGenerationRequest with mode, topic, and question types
            
        Returns:
            QuizResponse with generated questions
        """
        logger.info(f"Generating quiz: mode={request.mode}, topic={request.topic}")
        
        # Extract relevant documents
        documents = self._extract_topic_documents(request.topic)
        
        if not documents:
            logger.warning("No documents found for quiz generation")
            return QuizResponse(
                quiz_id=str(uuid.uuid4()),
                questions=[]
            )
        
        # Generate questions
        questions = []
        attempts = 0
        max_attempts = request.num_questions * 3  # Try 3x the requested number
        
        while len(questions) < request.num_questions and attempts < max_attempts:
            attempts += 1
            
            # Select random document
            doc = random.choice(documents)
            
            # Select random question type
            question_type = random.choice(request.question_types)
            
            # Generate question based on type
            question = None
            if question_type == QuestionType.MULTIPLE_CHOICE:
                question = self._generate_mcq(doc['text'], doc['metadata'])
            elif question_type == QuestionType.TRUE_FALSE:
                question = self._generate_true_false(doc['text'], doc['metadata'])
            elif question_type == QuestionType.OPEN_ENDED:
                question = self._generate_open_ended(doc['text'], doc['metadata'])
            
            if question:
                questions.append(question)
        
        # Create quiz response
        quiz_id = str(uuid.uuid4())
        quiz_response = QuizResponse(
            quiz_id=quiz_id,
            questions=questions
        )
        
        # Store quiz for grading
        self.active_quizzes[quiz_id] = quiz_response
        
        logger.info(f"Generated quiz {quiz_id} with {len(questions)} questions")
        return quiz_response
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        try:
            emb1 = self.embedding.embed_text(text1)
            emb2 = self.embedding.embed_text(text2)
            
            similarity = cosine_similarity(
                np.array([emb1]),
                np.array([emb2])
            )[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def _grade_answer(
        self,
        question: QuizQuestion,
        user_answer: str
    ) -> AnswerFeedback:
        """Grade a single answer with detailed feedback."""
        is_correct = False
        similarity_score = None
        feedback = ""
        grade = "F"
        
        # Normalize answers
        user_answer_clean = user_answer.strip()
        correct_answer_clean = question.correct_answer.strip()
        
        if question.type == QuestionType.MULTIPLE_CHOICE:
            # Exact match for MCQ
            is_correct = user_answer_clean.lower() == correct_answer_clean.lower()
            if is_correct:
                feedback = "Correct! Well done."
                grade = "A"
            else:
                feedback = f"Incorrect. The correct answer is: {correct_answer_clean}"
                grade = "F"
        
        elif question.type == QuestionType.TRUE_FALSE:
            # Exact match for T/F
            is_correct = user_answer_clean.lower() == correct_answer_clean.lower()
            if is_correct:
                feedback = "Correct!"
                grade = "A"
            else:
                feedback = f"Incorrect. The correct answer is: {correct_answer_clean}"
                grade = "F"
        
        elif question.type == QuestionType.OPEN_ENDED:
            # Semantic similarity for open-ended
            similarity_score = self._calculate_similarity(
                user_answer_clean,
                correct_answer_clean
            )
            
            # Generate detailed feedback using LLM
            feedback_prompt = f"""Compare the student's answer with the correct answer and provide constructive feedback.

Question: {question.question}

Student's Answer: {user_answer_clean}

Correct/Expected Answer: {correct_answer_clean}

Semantic Similarity Score: {similarity_score:.2f}

Provide brief, constructive feedback (2-3 sentences) on the student's answer."""

            try:
                feedback = self.ollama.generate(
                    prompt=feedback_prompt,
                    temperature=0.5
                )
            except:
                feedback = f"Your answer has a similarity score of {similarity_score:.2%} with the expected answer."
            
            # Grade based on similarity
            if similarity_score >= 0.85:
                grade = "A"
                is_correct = True
            elif similarity_score >= 0.75:
                grade = "B"
                is_correct = True
            elif similarity_score >= 0.65:
                grade = "C"
                is_correct = False
            elif similarity_score >= 0.50:
                grade = "D"
                is_correct = False
            else:
                grade = "F"
                is_correct = False
        
        return AnswerFeedback(
            question_id=question.id,
            is_correct=is_correct,
            user_answer=user_answer_clean,
            correct_answer=correct_answer_clean,
            similarity_score=similarity_score,
            feedback=feedback,
            citations=[question.citation] if question.citation else [],
            grade=grade
        )
    
    def grade_quiz(
        self,
        quiz_id: str,
        submissions: List[AnswerSubmission]
    ) -> QuizGrading:
        """
        Grade a complete quiz submission.
        
        Args:
            quiz_id: Quiz identifier
            submissions: List of answer submissions
            
        Returns:
            QuizGrading with detailed feedback
        """
        logger.info(f"Grading quiz {quiz_id}")
        
        # Retrieve quiz
        quiz = self.active_quizzes.get(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz {quiz_id} not found")
        
        # Create question lookup
        questions_dict = {q.id: q for q in quiz.questions}
        
        # Grade each submission
        feedback_list = []
        correct_count = 0
        
        for submission in submissions:
            question = questions_dict.get(submission.question_id)
            if not question:
                continue
            
            feedback = self._grade_answer(question, submission.user_answer)
            feedback_list.append(feedback)
            
            if feedback.is_correct:
                correct_count += 1
        
        # Calculate overall score
        total_questions = len(feedback_list)
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Determine overall grade
        if score_percentage >= 90:
            overall_grade = "A"
        elif score_percentage >= 80:
            overall_grade = "B"
        elif score_percentage >= 70:
            overall_grade = "C"
        elif score_percentage >= 60:
            overall_grade = "D"
        else:
            overall_grade = "F"
        
        return QuizGrading(
            quiz_id=quiz_id,
            total_questions=total_questions,
            correct_answers=correct_count,
            score_percentage=score_percentage,
            grade=overall_grade,
            feedback=feedback_list
        )

# Singleton instance
quiz_agent = QuizAgent()
