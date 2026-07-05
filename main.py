"""
Personal Tutor Agent with Cognee Integration

This FastAPI application demonstrates using Cognee as the primary data retrieval 
and memory layer for a personalized learning system.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import cognee
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Personal Tutor Agent", version="1.0.0")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class IngestRequest(BaseModel):
    content: str
    title: str = "Study Material"
    tags: List[str] = []

class QuizAnswerRequest(BaseModel):
    question_id: str
    answer: str
    user_id: str = "default_user"

class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_answer: str

# Global variables for demo (in production, use proper session management)
current_quiz: List[QuizQuestion] = []
quiz_metadata = {}

async def init_cognee():
    """Initialize Cognee with configuration"""
    try:
        # Configure Cognee
        cognee.config.set_llm_api_key(os.getenv("OPENAI_API_KEY"))
        
        # Initialize the system
        await cognee.prune.prune_system()
        print("✓ Cognee initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize Cognee: {e}")
        return False

def generate_quiz_questions(content: str, num_questions: int = 5) -> List[QuizQuestion]:
    """
    Generate quiz questions from content using simple parsing.
    In production, use Cognee + LLM for better question generation.
    """
    # Simple demo question generation - replace with LLM integration
    sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]
    questions = []
    
    for i, sentence in enumerate(sentences[:num_questions]):
        # Create a simple fill-in-the-blank or multiple choice
        words = sentence.split()
        if len(words) > 5:
            # Pick a key word to make into a question
            key_word_idx = len(words) // 2
            key_word = words[key_word_idx]
            
            question_text = sentence.replace(key_word, "_____")
            options = [key_word, f"not_{key_word}", f"fake_{key_word}", "none_of_above"]
            
            questions.append(QuizQuestion(
                id=f"q_{i+1}",
                question=f"Fill in the blank: {question_text}",
                options=options,
                correct_answer=key_word
            ))
    
    # Add at least one question if none generated
    if not questions:
        questions.append(QuizQuestion(
            id="q_1",
            question="What is the main topic of the provided material?",
            options=["Science", "History", "Literature", "Mathematics"],
            correct_answer="Science"
        ))
    
    return questions

@app.on_event("startup")
async def startup_event():
    """Initialize Cognee on startup"""
    success = await init_cognee()
    if not success:
        print("Warning: Cognee initialization failed, some features may not work")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main UI"""
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/ingest")
async def ingest_material(request: IngestRequest):
    """
    Ingest study materials into Cognee for later retrieval.
    
    This endpoint demonstrates Cognee's 'remember' functionality by storing
    content with rich metadata for semantic search and retrieval.
    """
    try:
        # Prepare metadata for Cognee storage
        metadata = {
            "type": "study_material",
            "title": request.title,
            "tags": request.tags,
            "timestamp": datetime.now().isoformat(),
            "content_length": len(request.content),
            "user_id": "default_user"  # In production, get from auth
        }
        
        # Store in Cognee with metadata
        # Cognee will automatically chunk and index the content
        await cognee.add(request.content, metadata=metadata)
        
        print(f"✓ Stored material '{request.title}' in Cognee")
        
        return {
            "success": True,
            "message": f"Successfully ingested '{request.title}'",
            "content_preview": request.content[:100] + "..." if len(request.content) > 100 else request.content,
            "metadata": metadata
        }
        
    except Exception as e:
        print(f"✗ Error ingesting material: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest material: {str(e)}")

@app.post("/quiz/generate")
async def generate_quiz():
    """
    Generate a quiz from previously ingested materials using Cognee's search.
    
    This demonstrates Cognee's 'recall' functionality by searching for
    relevant study materials to create quiz questions.
    """
    try:
        global current_quiz, quiz_metadata
        
        # Search for recent study materials in Cognee
        search_results = await cognee.search(
            "study_material content knowledge",
            limit=5
        )
        
        if not search_results:
            raise HTTPException(
                status_code=404, 
                detail="No study materials found. Please ingest some content first."
            )
        
        # Get the most recent material for quiz generation
        latest_material = search_results[0]
        content = latest_material.get('content', '')
        
        # Generate quiz questions
        current_quiz = generate_quiz_questions(content)
        
        # Store quiz metadata in Cognee for tracking
        quiz_metadata = {
            "quiz_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "source_material": latest_material.get('metadata', {}),
            "num_questions": len(current_quiz),
            "user_id": "default_user"
        }
        
        await cognee.add(
            json.dumps(quiz_metadata),
            metadata={
                "type": "quiz_session",
                "quiz_id": quiz_metadata["quiz_id"],
                "timestamp": quiz_metadata["created_at"]
            }
        )
        
        # Return questions without correct answers
        quiz_for_user = [
            {
                "id": q.id,
                "question": q.question,
                "options": q.options
            }
            for q in current_quiz
        ]
        
        print(f"✓ Generated quiz with {len(current_quiz)} questions")
        
        return {
            "success": True,
            "quiz_id": quiz_metadata["quiz_id"],
            "questions": quiz_for_user,
            "total_questions": len(current_quiz)
        }
        
    except Exception as e:
        print(f"✗ Error generating quiz: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

@app.post("/quiz/answer")
async def submit_quiz_answer(request: QuizAnswerRequest):
    """
    Submit and score a quiz answer, storing results in Cognee.
    
    This demonstrates storing user interaction data in Cognee for
    later analysis and adaptive learning recommendations.
    """
    try:
        global current_quiz, quiz_metadata
        
        # Find the question
        question = None
        for q in current_quiz:
            if q.id == request.question_id:
                question = q
                break
                
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Check if answer is correct
        is_correct = request.answer.strip().lower() == question.correct_answer.strip().lower()
        
        # Prepare answer data for Cognee storage
        answer_data = {
            "question_id": request.question_id,
            "quiz_id": quiz_metadata.get("quiz_id"),
            "user_id": request.user_id,
            "question_text": question.question,
            "user_answer": request.answer,
            "correct_answer": question.correct_answer,
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat(),
            "question_options": question.options
        }
        
        # Store answer in Cognee for performance tracking
        await cognee.add(
            json.dumps(answer_data),
            metadata={
                "type": "quiz_answer",
                "user_id": request.user_id,
                "quiz_id": quiz_metadata.get("quiz_id"),
                "is_correct": is_correct,
                "timestamp": answer_data["timestamp"]
            }
        )
        
        print(f"✓ Stored answer for question {request.question_id}: {'correct' if is_correct else 'incorrect'}")
        
        return {
            "success": True,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": f"The correct answer is '{question.correct_answer}'"
        }
        
    except Exception as e:
        print(f"✗ Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")

@app.get("/progress")
async def get_progress_summary(user_id: str = "default_user"):
    """
    Get user progress summary and adaptive recommendations from Cognee.
    
    This demonstrates querying historical data from Cognee to compute
    performance metrics and provide personalized learning suggestions.
    """
    try:
        # Search for user's quiz answers in Cognee
        answer_results = await cognee.search(
            f"quiz_answer user_id:{user_id}",
            limit=50
        )
        
        # Search for quiz sessions
        quiz_results = await cognee.search(
            f"quiz_session user_id:{user_id}",
            limit=20
        )
        
        if not answer_results and not quiz_results:
            return {
                "success": True,
                "message": "No quiz activity found",
                "stats": {
                    "total_questions": 0,
                    "correct_answers": 0,
                    "accuracy": 0,
                    "quizzes_taken": 0
                },
                "recommendations": ["Start by ingesting some study material and taking a quiz!"]
            }
        
        # Parse answer data
        total_questions = len(answer_results)
        correct_answers = 0
        recent_topics = set()
        
        for result in answer_results:
            try:
                data = json.loads(result.get('content', '{}'))
                if data.get('is_correct'):
                    correct_answers += 1
                    
                # Extract topic from question for recommendations
                question = data.get('question_text', '')
                if 'plant' in question.lower() or 'photosynthesis' in question.lower():
                    recent_topics.add('biology')
                elif 'math' in question.lower() or 'equation' in question.lower():
                    recent_topics.add('mathematics')
                else:
                    recent_topics.add('general')
                    
            except json.JSONDecodeError:
                continue
        
        # Calculate accuracy
        accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Generate adaptive recommendations based on performance
        recommendations = []
        if accuracy < 60:
            recommendations.append("Consider reviewing the study material before taking another quiz")
            recommendations.append("Focus on understanding key concepts rather than memorization")
        elif accuracy < 80:
            recommendations.append("Good progress! Try more challenging questions on the same topics")
            recommendations.append("Review incorrect answers to identify knowledge gaps")
        else:
            recommendations.append("Excellent performance! Ready for advanced topics")
            recommendations.append("Consider expanding to new subject areas")
        
        # Add topic-specific recommendations
        if 'biology' in recent_topics and accuracy > 70:
            recommendations.append("Strong in biology - consider ecology or genetics next")
        
        stats = {
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "accuracy": round(accuracy, 1),
            "quizzes_taken": len(quiz_results),
            "recent_topics": list(recent_topics)
        }
        
        print(f"✓ Generated progress summary: {accuracy:.1f}% accuracy over {total_questions} questions")
        
        return {
            "success": True,
            "stats": stats,
            "recommendations": recommendations,
            "message": f"You've answered {correct_answers}/{total_questions} questions correctly ({accuracy:.1f}%)"
        }
        
    except Exception as e:
        print(f"✗ Error getting progress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Personal Tutor Agent"}

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )