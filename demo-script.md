# Personal Tutor Agent Demo Script

This script demonstrates the complete functionality of the Personal Tutor Agent with Cognee integration. Follow these steps to record a 60-90 second demo.

## Prerequisites

1. ✅ Cognee API key configured in `.env`
2. ✅ Application running on `http://localhost:8000`
3. ✅ Fresh session (optional: restart server for clean state)

## Demo Steps (60-90 seconds)

### Step 1: Start Application (5 seconds)
```bash
./start.sh  # or start.bat on Windows
```
**Show**: Terminal output confirming server start

### Step 2: Open Web Interface (5 seconds)
- Navigate to `http://localhost:8000`
**Show**: Clean interface with three main sections

### Step 3: Ingest Study Material (15 seconds)
**Action**: 
- Paste this content in the material box:
```
Mitosis is the process of cell division that results in two identical daughter cells. It has four main phases: prophase (chromosomes condense), metaphase (chromosomes align at center), anaphase (chromosomes separate), and telophase (nuclear membranes reform). This process is essential for growth and tissue repair.
```
- Title: "Cell Biology - Mitosis"
- Click "📥 Upload Material"

**Show**: Success message confirming storage in Cognee

### Step 4: Generate Quiz (10 seconds)
**Action**: 
- Click "🎯 Create Quiz"
- Wait for generation

**Show**: Multiple choice questions generated from the material

### Step 5: Answer Questions (20 seconds)
**Action**:
- Answer 2-3 questions (mix correct/incorrect for demo)
- Click "Submit Answer" for each

**Show**: 
- Immediate feedback (correct/incorrect)
- Explanations for answers
- Storage confirmation

### Step 6: View Progress (10 seconds)
**Action**:
- Click "📈 View Progress"

**Show**: 
- Accuracy statistics
- Performance metrics
- Personalized recommendations based on answers

### Step 7: Demonstrate Persistence (10 seconds)
**Action**:
- Restart the server (`Ctrl+C`, then `python main.py`)
- Return to web interface
- Click "📈 View Progress" again

**Show**: Data persisted through Cognee (same statistics)

### Step 8: CLI Demo (Optional - 10 seconds)
**Action**:
```bash
python cli.py progress
python cli.py demo
```

**Show**: CLI access to same functionality

## Key Points to Highlight

1. **Cognee Integration**: 
   - "All data stored and retrieved through Cognee"
   - "No external database needed"

2. **Semantic Memory**:
   - "Cognee automatically chunks and indexes content"
   - "Intelligent retrieval for quiz generation"

3. **Adaptive Learning**:
   - "Performance tracking drives personalized recommendations"
   - "Historical analysis identifies weak areas"

4. **Persistence**:
   - "Data survives application restarts"
   - "Cross-session learning continuity"

5. **Multiple Interfaces**:
   - "Web UI for interactive use"
   - "CLI for automation and scripting"

## Troubleshooting

- **Cognee not configured**: Use mock data or show error handling
- **Quiz generation fails**: Pre-load sample material via CLI
- **Empty progress**: Use `python cli.py demo` to populate data

## Reset for Multiple Takes

```bash
# Quick reset (if needed)
python -c "import asyncio; import cognee; asyncio.run(cognee.prune.prune_system())"
```

## Demo Variations

### Quick Demo (30 seconds):
- Steps 2, 3, 4, 6 only
- Pre-populate with CLI demo data

### Technical Demo (90 seconds):
- Include Step 8 (CLI)
- Show API documentation at `/docs`
- Mention Cognee search and semantic capabilities

### Integration Demo:
- Show `main.py` code snippets
- Highlight Cognee API calls
- Demonstrate search and storage patterns