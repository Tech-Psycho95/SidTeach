#!/bin/bash
# Start script for Personal Tutor Agent

echo "🎓 Starting Personal Tutor Agent with Cognee..."

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env with your Cognee API credentials before continuing."
    echo "🔑 Required: COGNEE_API_KEY and optionally OPENAI_API_KEY"
fi

# Start the application
echo "🚀 Starting FastAPI server..."
echo "🌐 Web UI will be available at: http://localhost:8000"
echo "📖 API docs available at: http://localhost:8000/docs"
echo ""
python main.py