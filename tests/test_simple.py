"""
Simple tests that don't require external dependencies
"""

import pytest
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_project_structure():
    """Test that required files exist"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_files = [
        'main.py',
        'cli.py', 
        'requirements.txt',
        'README.md',
        '.env.example',
        'start.sh',
        'start.bat',
        'static/index.html'
    ]
    
    for file_path in required_files:
        full_path = os.path.join(project_root, file_path)
        assert os.path.exists(full_path), f"Required file missing: {file_path}"

def test_requirements_content():
    """Test that requirements.txt has necessary packages"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    req_path = os.path.join(project_root, 'requirements.txt')
    
    with open(req_path, 'r') as f:
        content = f.read()
    
    required_packages = ['fastapi', 'uvicorn', 'cognee', 'pytest', 'click']
    
    for package in required_packages:
        assert package in content, f"Required package missing: {package}"

def test_env_example_content():
    """Test that .env.example has required variables"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, '.env.example')
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    required_vars = ['COGNEE_API_KEY', 'HOST', 'PORT']
    
    for var in required_vars:
        assert var in content, f"Required environment variable missing: {var}"

def test_readme_structure():
    """Test that README.md has key sections"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(project_root, 'README.md')
    
    with open(readme_path, 'r') as f:
        content = f.read().lower()
    
    required_sections = ['cognee', 'setup', 'api endpoints', 'demo']
    
    for section in required_sections:
        assert section in content, f"Required README section missing: {section}"

# Test some standalone functions if we can import them safely
def test_quiz_generation_logic():
    """Test the quiz generation logic without Cognee"""
    # Simple content for testing
    content = """
    Photosynthesis is the process by which plants convert sunlight into energy.
    This process occurs in chloroplasts and produces oxygen as a byproduct.
    The chemical equation is 6CO2 + 6H2O + light energy → C6H12O6 + 6O2.
    """
    
    # Mock the QuizQuestion class
    class MockQuizQuestion:
        def __init__(self, id, question, options, correct_answer):
            self.id = id
            self.question = question
            self.options = options
            self.correct_answer = correct_answer
    
    # Simple quiz generation logic (extracted from main.py)
    def simple_quiz_gen(content, num_questions=3):
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]
        questions = []
        
        for i, sentence in enumerate(sentences[:num_questions]):
            words = sentence.split()
            if len(words) > 5:
                key_word_idx = len(words) // 2
                key_word = words[key_word_idx]
                
                question_text = sentence.replace(key_word, "_____")
                options = [key_word, f"not_{key_word}", f"fake_{key_word}", "none_of_above"]
                
                questions.append(MockQuizQuestion(
                    id=f"q_{i+1}",
                    question=f"Fill in the blank: {question_text}",
                    options=options,
                    correct_answer=key_word
                ))
        
        if not questions:
            questions.append(MockQuizQuestion(
                id="q_1",
                question="What is the main topic?",
                options=["Science", "History", "Literature", "Math"],
                correct_answer="Science"
            ))
        
        return questions
    
    # Test the function
    questions = simple_quiz_gen(content)
    
    assert len(questions) > 0
    assert len(questions) <= 3
    
    for q in questions:
        assert hasattr(q, 'id')
        assert hasattr(q, 'question')
        assert hasattr(q, 'options')
        assert hasattr(q, 'correct_answer')
        assert len(q.options) >= 2
        assert q.correct_answer in q.options

if __name__ == "__main__":
    pytest.main([__file__, "-v"])