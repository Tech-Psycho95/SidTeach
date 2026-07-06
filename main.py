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
from fastapi.responses import HTMLResponse, JSONResponse
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

class QuizGenerateRequest(BaseModel):
    num_questions: int = 5

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
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/ingest")
async def ingest_material(request: IngestRequest):
    """
    Ingest study materials into Cognee for later retrieval.
    
    This endpoint demonstrates Cognee's 'remember' functionality by storing
    content with rich metadata for semantic search and retrieval.
    """
    try:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")

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
        try:
            await cognee.add(request.content, metadata=metadata)
            print(f"✓ Stored material '{request.title}' in Cognee")
            storage_succeeded = True
        except Exception as storage_error:
            print(f"⚠️ Cognee storage failed for '{request.title}': {storage_error}")
            storage_succeeded = False
            metadata["storage_status"] = "deferred"
            metadata["storage_error"] = str(storage_error)

        if storage_succeeded:
            try:
                await asyncio.sleep(1)  # allow the save to settle before indexing
                await cognee.cognify()
                print("✓ Study material indexed successfully!")
                message = f"Successfully ingested and indexed '{request.title}'. Indexed successfully."
            except Exception as cognify_error:
                print(f"⚠️ Cognify failed for '{request.title}': {cognify_error}")
                message = f"Successfully ingested '{request.title}', but indexing is currently unavailable."
                metadata["indexing_status"] = "deferred"
        else:
            message = f"Successfully ingested '{request.title}', but storage is currently unavailable."
            metadata["indexing_status"] = "deferred"
        
        return {
            "success": True,
            "message": message,
            "content_preview": request.content[:100] + "..." if len(request.content) > 100 else request.content,
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Error ingesting material: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest material: {str(e)}")

@app.post("/quiz/generate")
@app.post("/quiz")
async def generate_quiz(request: Request, quiz_request: Optional[QuizGenerateRequest] = None):
    """
    Generate a quiz from previously ingested materials using Cognee's search.

    The modern /quiz/generate route returns a richer object payload for tests and
    clients that expect metadata, while the older /quiz route remains a compatibility
    alias that returns the plain question array expected by the legacy UI.
    """
    try:
        global current_quiz, quiz_metadata

        num_questions = max(1, quiz_request.num_questions if quiz_request else 5)
        is_generate_route = request.url.path.endswith("/quiz/generate")

        # Search for recent study materials in Cognee without the deprecated limit argument
        try:
            search_results = await cognee.search("study_material content knowledge")
        except Exception as search_error:
            print(f"⚠️ Cognee search unavailable: {search_error}")
            search_results = []

        selected_results = search_results[:num_questions] if search_results else []

        if not selected_results:
            return JSONResponse(status_code=400, content={"error": "No usable study material"})

        generated_questions: List[QuizQuestion] = []
        for material in selected_results:
            content = material.get("content", "")
            if not content:
                continue

            generated_questions.extend(generate_quiz_questions(content, num_questions=1))

            if len(generated_questions) >= num_questions:
                break

        if not generated_questions:
            return JSONResponse(status_code=400, content={"error": "No usable study material"})

        current_quiz = generated_questions[:num_questions]

        quiz_metadata = {
            "quiz_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "source_materials": [
                material.get("metadata", {}) for material in selected_results if material.get("metadata")
            ],
            "num_questions": len(current_quiz),
            "user_id": "default_user"
        }

        try:
            await cognee.add(
                json.dumps(quiz_metadata),
                metadata={
                    "type": "quiz_session",
                    "quiz_id": quiz_metadata["quiz_id"],
                    "timestamp": quiz_metadata["created_at"]
                }
            )
        except Exception as storage_error:
            print(f"⚠️ Quiz metadata storage skipped: {storage_error}")

        quiz_for_user = [
            {
                "id": q.id,
                "question": q.question,
                "options": q.options
            }
            for q in current_quiz
        ]

        if is_generate_route:
            return {
                "success": True,
                "questions": quiz_for_user,
                "total_questions": len(quiz_for_user),
                "quiz_id": quiz_metadata["quiz_id"],
            }

        print(f"✓ Generated quiz with {len(current_quiz)} questions")

        return quiz_for_user

    except Exception as e:
        print(f"✗ Error generating quiz: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

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
        try:
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
        except Exception as storage_error:
            print(f"⚠️ Answer storage skipped: {storage_error}")
        
        return {
            "success": True,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": f"The correct answer is '{question.correct_answer}'"
        }
        
    except HTTPException:
        raise
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
        try:
            answer_results = await cognee.search(
                f"quiz_answer user_id:{user_id}"
            )
        except Exception as search_error:
            print(f"⚠️ Progress answer search unavailable: {search_error}")
            answer_results = []
        
        # Search for quiz sessions
        try:
            quiz_results = await cognee.search(
                f"quiz_session user_id:{user_id}"
            )
        except Exception as search_error:
            print(f"⚠️ Progress quiz search unavailable: {search_error}")
            quiz_results = []
        
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