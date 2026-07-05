# SidTeach - A Personal Tutor Agent with Cogne

A minimal but complete Personal Tutor Agent that uses Cognee as the primary data retrieval and memory layer.

## Features

- Upload/paste study materials (text or markdown)
- Generate quizzes from uploaded materials
- Answer quiz questions with performance tracking
- Get progress summaries and adaptive recommendations
- All data stored and retrieved through Cognee

## Tech Stack

- **Backend**: Python + FastAPI
- **Memory Layer**: Cognee Python SDK
- **Frontend**: Simple HTML/JS with fetch API
- **Persistence**: Cognee (no external database)

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Cognee**:
   - Copy `.env.example` to `.env`
   - Add your Cognee API credentials
   - Initialize Cognee workspace

3. **Start the application**:
   ```bash
   ./start.sh
   ```
   Or manually:
   ```bash
   python main.py
   ```

4. **Access the app**:
   - Web UI: http://localhost:8000
   - API docs: http://localhost:8000/docs

## How Cognee is Used

Cognee serves as our **primary retrieval and memory layer** for:

- **Material Storage**: Study materials are chunked and stored with metadata (title, tags, timestamps)
- **Quiz Generation**: Semantic search retrieves relevant content for question generation
- **Answer Tracking**: User responses and performance metrics are stored for analysis
- **Progress Analytics**: Historical data is queried to compute accuracy and identify weak areas
- **Adaptive Learning**: Performance patterns drive personalized question recommendations

### Key Cognee Operations

```python
# Store study material
await cognee.add(content, metadata={"type": "material", "title": title})

# Retrieve for quiz generation  
results = await cognee.search(query, limit=5)

# Store quiz answers
await cognee.add(answer_data, metadata={"type": "answer", "user_id": user_id})

# Query performance data
performance = await cognee.search("user performance accuracy", limit=20)
```

## API Endpoints

- `POST /ingest` - Upload study materials
- `POST /quiz/generate` - Generate quiz from materials  
- `POST /quiz/answer` - Submit quiz answers
- `GET /progress` - Get performance summary and recommendations

## Demo Script

Run this sequence to see the full workflow:

1. **Ingest material**:
   ```bash
   curl -X POST "http://localhost:8000/ingest" \
     -H "Content-Type: application/json" \
     -d '{"content": "Photosynthesis is the process by which plants convert sunlight into energy...", "title": "Plant Biology"}'
   ```

2. **Generate quiz**:
   ```bash
   curl -X POST "http://localhost:8000/quiz/generate"
   ```

3. **Answer questions**:
   ```bash
   curl -X POST "http://localhost:8000/quiz/answer" \
     -H "Content-Type: application/json" \
     -d '{"question_id": "q1", "answer": "A"}'
   ```

4. **Check progress**:
   ```bash
   curl "http://localhost:8000/progress"
   ```

## CLI Usage

```bash
# Ingest material
python cli.py ingest "Your study material here" --title "Topic Name"

# Generate quiz
python cli.py generate-quiz

# Answer question  
python cli.py answer q1 A

# Check progress
python cli.py progress
```

## Testing

```bash
python -m pytest tests/ -v
```

## Environment Variables

See `.env.example` for required configuration.
