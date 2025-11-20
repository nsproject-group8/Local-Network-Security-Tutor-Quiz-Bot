from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    OPEN_ENDED = "open_ended"

class QuizMode(str, Enum):
    RANDOM = "random"
    TOPIC_SPECIFIC = "topic_specific"

class Citation(BaseModel):
    source: str
    content: str
    page: Optional[int] = None
    url: Optional[str] = None
    confidence: float = 0.0

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    question: str
    answer: str
    citations: List[Citation]
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.now)

class QuizGenerationRequest(BaseModel):
    mode: QuizMode
    topic: Optional[str] = None
    num_questions: int = 5
    question_types: List[QuestionType] = [
        QuestionType.MULTIPLE_CHOICE,
        QuestionType.TRUE_FALSE,
        QuestionType.OPEN_ENDED
    ]

class QuizQuestion(BaseModel):
    id: str
    type: QuestionType
    question: str
    options: Optional[List[str]] = None  # For MCQ and T/F
    correct_answer: str
    topic: str
    difficulty: str = "medium"
    citation: Optional[Citation] = None

class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[QuizQuestion]
    generated_at: datetime = Field(default_factory=datetime.now)

class AnswerSubmission(BaseModel):
    quiz_id: str
    question_id: str
    user_answer: str

class AnswerFeedback(BaseModel):
    question_id: str
    is_correct: bool
    user_answer: str
    correct_answer: str
    similarity_score: Optional[float] = None
    feedback: str
    citations: List[Citation]
    grade: str  # A, B, C, D, F

class QuizGrading(BaseModel):
    quiz_id: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    grade: str
    feedback: List[AnswerFeedback]
    submitted_at: datetime = Field(default_factory=datetime.now)

class DocumentUpload(BaseModel):
    filename: str
    content_type: str
    size: int
    uploaded_at: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseModel):
    status: str
    ollama_available: bool
    chroma_initialized: bool
    documents_indexed: int
