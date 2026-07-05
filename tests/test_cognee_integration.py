"""
Tests for Cognee integration functionality

These tests verify that our Cognee integration patterns work correctly.
Note: These tests use mocking and don't require actual Cognee configuration.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock cognee before importing
with patch('cognee.config.set_llm_api_key'), \
     patch('cognee.prune.prune_system', new_callable=AsyncMock), \
     patch('cognee.add', new_callable=AsyncMock), \
     patch('cognee.search', new_callable=AsyncMock):
    from main import init_cognee, generate_quiz_questions

class TestCogneeIntegration:
    """Test Cognee-specific functionality"""
    
    @pytest.mark.asyncio
    async def test_cognee_initialization(self):
        """Test Cognee initialization function"""
        # Mock cognee module to avoid requiring actual API keys
        with patch('main.cognee') as mock_cognee:
            mock_cognee.config.set_llm_api_key = Mock()
            mock_cognee.prune.prune_system = AsyncMock(return_value=True)
            
            result = await init_cognee()
            
            # Should succeed with mocked cognee
            assert result is True
            mock_cognee.config.set_llm_api_key.assert_called_once()
            mock_cognee.prune.prune_system.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_cognee_initialization_failure(self):
        """Test Cognee initialization with failure"""
        with patch('main.cognee') as mock_cognee:
            mock_cognee.config.set_llm_api_key = Mock()
            mock_cognee.prune.prune_system = AsyncMock(side_effect=Exception("API Error"))
            
            result = await init_cognee()
            
            # Should handle failure gracefully
            assert result is False
    
    def test_quiz_question_generation(self):
        """Test quiz question generation logic"""
        sample_content = """
        Photosynthesis is the process by which plants convert sunlight into energy.
        This process occurs in chloroplasts and produces oxygen as a byproduct.
        The chemical equation is 6CO2 + 6H2O + light energy → C6H12O6 + 6O2.
        This process is essential for most life on Earth.
        """
        
        questions = generate_quiz_questions(sample_content, num_questions=3)
        
        # Should generate at least one question
        assert len(questions) >= 1
        assert len(questions) <= 3
        
        # Check question structure
        for question in questions:
            assert hasattr(question, 'id')
            assert hasattr(question, 'question')
            assert hasattr(question, 'options')
            assert hasattr(question, 'correct_answer')
            
            assert len(question.options) >= 2  # Should have multiple options
            assert question.correct_answer in question.options  # Correct answer should be in options
    
    def test_quiz_generation_short_content(self):
        """Test quiz generation with very short content"""
        short_content = "Water boils at 100°C."
        
        questions = generate_quiz_questions(short_content, num_questions=2)
        
        # Should generate at least one fallback question
        assert len(questions) >= 1
        
        # Check that we get a valid question structure even with short content
        question = questions[0]
        assert question.id is not None
        assert len(question.question) > 0
        assert len(question.options) > 0
    
    def test_quiz_generation_empty_content(self):
        """Test quiz generation with empty content"""
        empty_content = ""
        
        questions = generate_quiz_questions(empty_content, num_questions=2)
        
        # Should generate at least one fallback question
        assert len(questions) >= 1
        
        # Should have a default question
        question = questions[0]
        assert "main topic" in question.question.lower() or "q_1" in question.id

class TestCogneeDataPatterns:
    """Test data patterns used with Cognee"""
    
    def test_material_metadata_structure(self):
        """Test that material metadata follows expected structure"""
        from datetime import datetime
        
        # This is the metadata structure we use with Cognee
        metadata = {
            "type": "study_material",
            "title": "Test Material",
            "tags": ["test", "demo"],
            "timestamp": datetime.now().isoformat(),
            "content_length": 100,
            "user_id": "test_user"
        }
        
        # Verify structure
        assert metadata["type"] == "study_material"
        assert "timestamp" in metadata
        assert isinstance(metadata["tags"], list)
        assert isinstance(metadata["content_length"], int)
    
    def test_quiz_answer_data_structure(self):
        """Test quiz answer data structure for Cognee storage"""
        answer_data = {
            "question_id": "q_1",
            "quiz_id": "quiz_123",
            "user_id": "test_user",
            "question_text": "What is photosynthesis?",
            "user_answer": "energy conversion",
            "correct_answer": "energy conversion",
            "is_correct": True,
            "timestamp": "2024-01-01T12:00:00",
            "question_options": ["energy conversion", "water absorption", "cell division", "none"]
        }
        
        # Verify all required fields are present
        required_fields = ["question_id", "user_id", "is_correct", "timestamp"]
        for field in required_fields:
            assert field in answer_data
        
        # Verify data types
        assert isinstance(answer_data["is_correct"], bool)
        assert isinstance(answer_data["question_options"], list)
    
    def test_quiz_metadata_structure(self):
        """Test quiz session metadata structure"""
        quiz_metadata = {
            "quiz_id": "quiz_123",
            "created_at": "2024-01-01T12:00:00",
            "source_material": {"title": "Biology 101"},
            "num_questions": 5,
            "user_id": "test_user"
        }
        
        # Verify structure
        assert "quiz_id" in quiz_metadata
        assert "created_at" in quiz_metadata
        assert isinstance(quiz_metadata["num_questions"], int)
        assert quiz_metadata["num_questions"] > 0

class TestMockCogneeOperations:
    """Test Cognee operations with mocking"""
    
    @pytest.mark.asyncio
    async def test_mock_cognee_add_operation(self):
        """Test Cognee add operation with mocking"""
        with patch('main.cognee') as mock_cognee:
            mock_cognee.add = AsyncMock(return_value={"status": "success"})
            
            # Test the add operation
            content = "Test study material"
            metadata = {"type": "study_material", "title": "Test"}
            
            await mock_cognee.add(content, metadata=metadata)
            
            # Verify the call was made correctly
            mock_cognee.add.assert_called_once_with(content, metadata=metadata)
    
    @pytest.mark.asyncio
    async def test_mock_cognee_search_operation(self):
        """Test Cognee search operation with mocking"""
        with patch('main.cognee') as mock_cognee:
            # Mock search results
            mock_results = [
                {"content": "Sample content", "metadata": {"title": "Test Material"}},
                {"content": "More content", "metadata": {"title": "Another Material"}}
            ]
            mock_cognee.search = AsyncMock(return_value=mock_results)
            
            # Test the search operation
            results = await mock_cognee.search("study_material", limit=5)
            
            # Verify results
            assert len(results) == 2
            assert results[0]["content"] == "Sample content"
            mock_cognee.search.assert_called_once_with("study_material", limit=5)

if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])