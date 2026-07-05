#!/usr/bin/env python3
"""
Command-line interface for Personal Tutor Agent

Provides CLI access to all tutor functionality for users who prefer terminal interaction.
"""

import asyncio
import json
import sys
from typing import List, Optional

import click
import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv()

BASE_URL = "http://localhost:8000"

async def make_request(method: str, endpoint: str, data: Optional[dict] = None):
    """Make HTTP request to the API"""
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(f"{BASE_URL}{endpoint}")
            else:
                response = await client.request(
                    method.upper(), 
                    f"{BASE_URL}{endpoint}",
                    json=data
                )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.ConnectError:
            click.echo("❌ Error: Cannot connect to server. Make sure it's running on localhost:8000")
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            click.echo(f"❌ Error: {e.response.status_code} - {e.response.text}")
            sys.exit(1)

@click.group()
def cli():
    """Personal Tutor Agent CLI - Learn with Cognee integration"""
    pass

@cli.command()
@click.argument('content')
@click.option('--title', '-t', default='CLI Material', help='Title for the study material')
@click.option('--tags', '-g', multiple=True, help='Tags for the material')
def ingest(content: str, title: str, tags: tuple):
    """Ingest study material into Cognee
    
    Examples:
        python cli.py ingest "Photosynthesis converts sunlight to energy" --title "Biology"
        python cli.py ingest "E=mc²" --title "Physics" --tags physics equations
    """
    async def _ingest():
        data = {
            "content": content,
            "title": title,
            "tags": list(tags)
        }
        
        click.echo(f"📚 Ingesting material: '{title}'...")
        result = await make_request("POST", "/ingest", data)
        
        if result.get('success'):
            click.echo(f"✅ Successfully ingested '{result['metadata']['title']}'")
            click.echo(f"📝 Preview: {result['content_preview']}")
        else:
            click.echo("❌ Failed to ingest material")
    
    asyncio.run(_ingest())

@cli.command()
@click.option('--show-answers', '-a', is_flag=True, help='Show correct answers (for testing)')
def generate_quiz(show_answers: bool):
    """Generate a quiz from ingested materials
    
    Examples:
        python cli.py generate-quiz
        python cli.py generate-quiz --show-answers
    """
    async def _generate():
        click.echo("🧠 Generating quiz from your materials...")
        result = await make_request("POST", "/quiz/generate")
        
        if result.get('success'):
            click.echo(f"✅ Generated {result['total_questions']} questions!")
            click.echo(f"Quiz ID: {result['quiz_id']}\n")
            
            for i, question in enumerate(result['questions'], 1):
                click.echo(f"Question {i}: {question['question']}")
                for j, option in enumerate(question['options']):
                    click.echo(f"  {chr(65+j)}. {option}")
                    
                if show_answers:
                    # This would need modification in the API to return answers
                    click.echo("  (Answer hidden in CLI mode - use web interface)")
                click.echo()
                
            click.echo("Use 'python cli.py answer <question_id> <answer>' to submit answers")
        else:
            click.echo("❌ Failed to generate quiz")
    
    asyncio.run(_generate())

@cli.command()
@click.argument('question_id')
@click.argument('answer')
@click.option('--user-id', '-u', default='cli_user', help='User ID for tracking')
def answer(question_id: str, answer: str, user_id: str):
    """Submit an answer to a quiz question
    
    Examples:
        python cli.py answer q_1 "chlorophyll"
        python cli.py answer q_2 A
    """
    async def _answer():
        data = {
            "question_id": question_id,
            "answer": answer,
            "user_id": user_id
        }
        
        click.echo(f"📝 Submitting answer for {question_id}...")
        result = await make_request("POST", "/quiz/answer", data)
        
        if result.get('success'):
            if result['is_correct']:
                click.echo(f"✅ Correct! {result['explanation']}")
            else:
                click.echo(f"❌ Incorrect. {result['explanation']}")
        else:
            click.echo("❌ Failed to submit answer")
    
    asyncio.run(_answer())

@cli.command()
@click.option('--user-id', '-u', default='cli_user', help='User ID for progress tracking')
def progress(user_id: str):
    """Show progress summary and recommendations
    
    Examples:
        python cli.py progress
        python cli.py progress --user-id john_doe
    """
    async def _progress():
        click.echo("📊 Analyzing your progress...")
        result = await make_request("GET", f"/progress?user_id={user_id}")
        
        if result.get('success'):
            stats = result['stats']
            
            click.echo("\n" + "="*50)
            click.echo("📈 PROGRESS SUMMARY")
            click.echo("="*50)
            click.echo(f"Overall Accuracy: {stats['accuracy']}%")
            click.echo(f"Questions Answered: {stats['correct_answers']}/{stats['total_questions']}")
            click.echo(f"Quizzes Taken: {stats['quizzes_taken']}")
            
            if stats['recent_topics']:
                click.echo(f"Recent Topics: {', '.join(stats['recent_topics'])}")
            
            click.echo("\n🎯 PERSONALIZED RECOMMENDATIONS:")
            click.echo("-" * 30)
            for i, rec in enumerate(result['recommendations'], 1):
                click.echo(f"{i}. {rec}")
                
            click.echo()
        else:
            click.echo("❌ Failed to get progress")
    
    asyncio.run(_progress())

@cli.command()
def status():
    """Check if the server is running"""
    async def _status():
        try:
            result = await make_request("GET", "/health")
            click.echo(f"✅ Server is running: {result['status']}")
        except:
            click.echo("❌ Server is not responding")
    
    asyncio.run(_status())

@cli.command()
def demo():
    """Run a complete demo of the tutor system"""
    async def _demo():
        click.echo("🎓 Starting Personal Tutor Agent Demo")
        click.echo("="*50)
        
        # Step 1: Ingest material
        click.echo("\n📚 Step 1: Ingesting sample study material...")
        sample_content = """
        Mitosis is the process of cell division that results in two genetically identical daughter cells. 
        It consists of several phases: prophase (chromosomes condense), metaphase (chromosomes align), 
        anaphase (chromosomes separate), and telophase (nuclei reform). This process is essential for 
        growth and tissue repair in multicellular organisms.
        """
        
        ingest_data = {
            "content": sample_content.strip(),
            "title": "Cell Biology - Mitosis",
            "tags": ["biology", "cell-division", "demo"]
        }
        
        result = await make_request("POST", "/ingest", ingest_data)
        if result.get('success'):
            click.echo("✅ Material ingested successfully!")
        
        # Step 2: Generate quiz
        click.echo("\n🧠 Step 2: Generating quiz...")
        result = await make_request("POST", "/quiz/generate")
        if result.get('success'):
            click.echo(f"✅ Generated {result['total_questions']} questions!")
            
            # Show first question as example
            if result['questions']:
                q = result['questions'][0]
                click.echo(f"\nSample Question: {q['question']}")
                for i, option in enumerate(q['options']):
                    click.echo(f"  {chr(65+i)}. {option}")
        
        # Step 3: Submit a sample answer
        click.echo("\n📝 Step 3: Submitting sample answer...")
        if result.get('success') and result['questions']:
            q = result['questions'][0]
            sample_answer = q['options'][0]  # Pick first option
            
            answer_data = {
                "question_id": q['id'],
                "answer": sample_answer,
                "user_id": "demo_user"
            }
            
            result = await make_request("POST", "/quiz/answer", answer_data)
            if result.get('success'):
                status = "✅ Correct!" if result['is_correct'] else "❌ Incorrect"
                click.echo(f"{status} {result['explanation']}")
        
        # Step 4: Check progress
        click.echo("\n📊 Step 4: Checking progress...")
        result = await make_request("GET", "/progress?user_id=demo_user")
        if result.get('success'):
            stats = result['stats']
            click.echo(f"Demo Progress: {stats['accuracy']}% accuracy")
        
        click.echo("\n🎉 Demo completed! All data stored in Cognee.")
        click.echo("Visit http://localhost:8000 for the web interface.")
    
    asyncio.run(_demo())

if __name__ == '__main__':
    cli()