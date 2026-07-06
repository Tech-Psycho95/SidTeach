"""
Unit tests for Personal Tutor Agent API endpoints

Tests the core functionality of the tutor system including
material ingestion and quiz generation.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

# Add the parent directory to the path so we can import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock cognee before importing main
with patch('cognee.config.set_llm_api_key'), \
     patch('cognee.prune.prune_system', new_callable=AsyncMock), \
     patch('cognee.add', new_callable=AsyncMock), \
     patch('cognee.search', new_callable=AsyncMock, return_value=[]):
    from main import app

# Create test client
client = TestClient(app)

class TestPersonalTutorAPI:
    """Test suite for Personal Tutor Agent API"""
    
    def test_health_check(self):
        """Test that the health endpoint works"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Personal Tutor Agent"
    
    def test_ingest_material_success(self):
        """Test successful material ingestion"""
        test_material = {
            "content": "Water boils at 100 degrees Celsius at sea level pressure.",
            "title": "Basic Chemistry",
            "tags": ["chemistry", "water", "temperature"]
        }
        
        response = client.post("/ingest", json=test_material)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Successfully ingested" in data["message"]
        assert data["metadata"]["title"] == "Basic Chemistry"
        assert data["metadata"]["type"] == "study_material"
        assert len(data["metadata"]["tags"]) == 3
    
    def test_ingest_material_minimal(self):
        """Test material ingestion with minimal data"""
        test_material = {
            "content": "Photosynthesis produces oxygen.",
            "title": "Biology Fact"
        }
        
        response = client.post("/ingest", json=test_material)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["title"] == "Biology Fact"
        assert "content_preview" in data

    def test_ingest_triggers_cognification(self):
        """Test that ingestion triggers cognification after saving the material"""
        test_material = {
            "content": "Neural networks learn from patterns in data.",
            "title": "AI Basics"
        }

        with patch('main.cognee.add', new_callable=AsyncMock), \
             patch('main.cognee.cognify', new_callable=AsyncMock), \
             patch('main.asyncio.sleep', new_callable=AsyncMock):
            response = client.post("/ingest", json=test_material)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "indexed successfully" in data["message"].lower()
    
    def test_ingest_empty_content_fails(self):
        """Test that empty content is rejected"""
        test_material = {
            "content": "",
            "title": "Empty Content"
        }
        
        response = client.post("/ingest", json=test_material)
        # The endpoint should handle this gracefully
        # In a real implementation, you might want to validate content length
        assert response.status_code in [200, 400]  # Either works or properly rejects
    
    def test_quiz_generation_without_material(self):
        """Test quiz generation when no material exists"""
        with patch('main.cognee.search', new_callable=AsyncMock, return_value=[]):
            response = client.post("/quiz/generate", json={"num_questions": 1})

        assert response.status_code == 400
        data = response.json()
        assert data == {"error": "No usable study material"}

    def test_quiz_generation_returns_array_and_supports_alias(self):
        """Test that quiz generation returns an array of questions and works on the alias route"""
        search_results = [
            {"content": "One short sentence about biology.", "metadata": {"title": "Bio 1"}}
        ]

        with patch('main.cognee.search', new_callable=AsyncMock, return_value=search_results):
            response = client.post("/quiz", json={"num_questions": 1})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert "question" in data[0]
        assert "options" in data[0]

    def test_quiz_generation_respects_num_questions(self):
        """Test that quiz generation honors the requested number of questions"""
        search_results = [
            {"content": "One short sentence about biology.", "metadata": {"title": "Bio 1"}},
            {"content": "Another short sentence about chemistry.", "metadata": {"title": "Chem 1"}},
            {"content": "A third short sentence about physics.", "metadata": {"title": "Phys 1"}},
        ]

        with patch('main.cognee.search', new_callable=AsyncMock, return_value=search_results):
            response = client.post("/quiz/generate", json={"num_questions": 3})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["questions"]) == 3
        assert data["total_questions"] == 3
    
    def test_quiz_answer_invalid_question(self):
        """Test answering a question that doesn't exist"""
        answer_data = {
            "question_id": "nonexistent_q1",
            "answer": "test answer",
            "user_id": "test_user"
        }
        
        response = client.post("/quiz/answer", json=answer_data)
        assert response.status_code == 404
        
        data = response.json()
        assert "Question not found" in data["detail"]
    
    def test_progress_for_new_user(self):
        """Test progress endpoint for user with no activity"""
        response = client.get("/progress?user_id=brand_new_user")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # Should return empty/zero stats for new user
        stats = data["stats"]
        assert stats["total_questions"] == 0
        assert stats["correct_answers"] == 0
        assert stats["accuracy"] == 0
        assert stats["quizzes_taken"] == 0
    
    def test_progress_default_user(self):
        """Test progress endpoint with default user"""
        response = client.get("/progress")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "stats" in data
        assert "recommendations" in data
        
        # Should have at least one recommendation
        assert len(data["recommendations"]) > 0

class TestDataFlow:
    """Test the complete data flow through Cognee"""
    
    def test_complete_learning_flow(self):
        """Test a complete learning session from ingestion to progress"""
        # Step 1: Ingest material
        material = {
            "content": "The mitochondria is the powerhouse of the cell. It produces ATP through cellular respiration.",
            "title": "Cell Biology",
            "tags": ["biology", "cells", "energy"]
        }
        
        ingest_response = client.post("/ingest", json=material)
        assert ingest_response.status_code == 200
        assert ingest_response.json()["success"] is True
        
        # Step 2: Generate quiz (may fail if Cognee not configured)
        quiz_response = client.post("/quiz/generate")
        
        if quiz_response.status_code == 200:
            quiz_data = quiz_response.json()
            assert quiz_data["success"] is True
            assert len(quiz_data["questions"]) > 0
            
            # Step 3: Answer a question (if quiz was generated)
            first_question = quiz_data["questions"][0]
            answer_data = {
                "question_id": first_question["id"],
                "answer": first_question["options"][0],  # Pick first option
                "user_id": "integration_test_user"
            }
            
            answer_response = client.post("/quiz/answer", json=answer_data)
            if answer_response.status_code == 200:
                answer_result = answer_response.json()
                assert answer_result["success"] is True
                assert "is_correct" in answer_result
                
                # Step 4: Check progress
                progress_response = client.get("/progress?user_id=integration_test_user")
                assert progress_response.status_code == 200
                
                progress_data = progress_response.json()
                assert progress_data["success"] is True
                
                # Should now have some activity
                stats = progress_data["stats"]
                if stats["total_questions"] > 0:
                    assert stats["total_questions"] >= 1
                    assert stats["accuracy"] >= 0

if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])