# Personal Tutor Agent with Cognee - Development Commands

.PHONY: help install run test clean demo cli-demo reset

help: ## Show this help message
	@echo "Personal Tutor Agent with Cognee - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies and setup environment
	@echo "📦 Setting up Personal Tutor Agent..."
	python -m venv venv || python3 -m venv venv
	./venv/bin/pip install -r requirements.txt || venv\Scripts\pip install -r requirements.txt
	@if [ ! -f .env ]; then cp .env.example .env; echo "📝 Created .env file - please add your API keys"; fi
	@echo "✅ Setup complete!"

run: ## Start the application
	@echo "🚀 Starting Personal Tutor Agent..."
	@echo "🌐 Web UI: http://localhost:8000"
	@echo "📖 API Docs: http://localhost:8000/docs"
	python main.py

test: ## Run all tests
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v --tb=short

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	python -m pytest tests/ -v --cov=main --cov-report=html --cov-report=term

demo: ## Run complete demo sequence
	@echo "🎬 Running demo sequence..."
	python cli.py demo

cli-demo: ## Show CLI commands demo
	@echo "💻 CLI Demo Commands:"
	@echo ""
	@echo "# Ingest material:"
	@echo 'python cli.py ingest "Photosynthesis converts light to energy" --title "Biology"'
	@echo ""
	@echo "# Generate quiz:"
	@echo "python cli.py generate-quiz"
	@echo ""
	@echo "# Answer question:"
	@echo "python cli.py answer q_1 chlorophyll"
	@echo ""
	@echo "# Check progress:"
	@echo "python cli.py progress"

clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage 2>/dev/null || true
	@echo "✅ Cleanup complete"

reset: ## Reset Cognee data (use with caution)
	@echo "⚠️  Resetting Cognee data..."
	python -c "import asyncio; import cognee; asyncio.run(cognee.prune.prune_system())" || echo "Note: Cognee reset requires proper configuration"

dev: ## Start in development mode with auto-reload
	@echo "🔧 Starting in development mode..."
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

lint: ## Run code linting
	@echo "🔍 Linting code..."
	python -m flake8 main.py cli.py tests/ --max-line-length=100 --ignore=E501,W503 || echo "Install flake8 for linting: pip install flake8"

format: ## Format code with black
	@echo "✨ Formatting code..."
	python -m black main.py cli.py tests/ || echo "Install black for formatting: pip install black"

check: ## Run all checks (test, lint, format-check)
	@echo "🔍 Running all checks..."
	@$(MAKE) test
	@$(MAKE) lint
	python -m black --check main.py cli.py tests/ || echo "Code formatting issues found - run 'make format'"

docker-build: ## Build Docker image (if Dockerfile exists)
	@echo "🐳 Building Docker image..."
	docker build -t personal-tutor-agent .

docker-run: ## Run Docker container
	@echo "🐳 Running Docker container..."
	docker run -p 8000:8000 --env-file .env personal-tutor-agent

status: ## Check if application is running
	@echo "🔍 Checking application status..."
	python cli.py status

api-docs: ## Open API documentation
	@echo "📖 Opening API documentation..."
	python -c "import webbrowser; webbrowser.open('http://localhost:8000/docs')"

logs: ## Show application logs (if running in background)
	@echo "📋 Application logs:"
	@echo "Run with: python main.py 2>&1 | tee app.log"

backup-data: ## Backup Cognee data (placeholder)
	@echo "💾 Cognee data backup:"
	@echo "Note: Cognee handles its own data persistence"
	@echo "Check Cognee documentation for backup procedures"