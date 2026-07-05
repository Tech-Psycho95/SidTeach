@echo off
REM Start script for Personal Tutor Agent on Windows

echo 🎓 Starting Personal Tutor Agent with Cognee...

REM Check if virtual environment exists, create if not
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  Warning: .env file not found. Creating from template...
    copy .env.example .env
    echo 📝 Please edit .env with your Cognee API credentials before continuing.
    echo 🔑 Required: COGNEE_API_KEY and optionally OPENAI_API_KEY
)

REM Start the application
echo 🚀 Starting FastAPI server...
echo 🌐 Web UI will be available at: http://localhost:8000
echo 📖 API docs available at: http://localhost:8000/docs
echo.
python main.py

pause