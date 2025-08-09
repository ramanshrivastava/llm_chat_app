# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLM Chat App is a FastAPI-based web application that provides a chat interface for Azure OpenAI models (GPT-4, GPT-3.5-turbo). The application features a responsive UI with dark mode, code block rendering, and token usage tracking.

## Essential Commands

### Development Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### Running the Application
```bash
# Start the application (default: http://localhost:8000)
python main.py

# Run with hot reload for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=term-missing

# Run specific test types
pytest -m unit
pytest -m integration

# Run a single test file
pytest tests/unit/test_chat.py

# Run a specific test
pytest tests/unit/test_chat.py::test_chat_endpoint
```

### Code Quality
```bash
# Linting
flake8 .

# Type checking
mypy .

# Code formatting and linting with ruff
ruff check .
ruff format .
```

### Docker
```bash
# Build image
docker build -t llm-chat-app .

# Run container
docker run -p 8000:8000 --env-file .env llm-chat-app
```

## Architecture Overview

### Project Structure
- `app/` - Main application code
  - `api/` - FastAPI route handlers (endpoints)
  - `core/` - Core configuration using Pydantic settings
  - `schemas/` - Pydantic models for request/response validation
  - `services/` - Business logic layer (Azure OpenAI integration)
  - `static/` - Frontend assets (CSS, JavaScript)
  - `templates/` - Jinja2 HTML templates
- `tests/` - Test suite organized by unit and integration tests
- `main.py` - Entry point that starts Uvicorn server
- `pyproject.toml` - Project configuration and dependencies

### Key Design Patterns
1. **Configuration Management**: Uses Pydantic Settings with `.env` file support for managing environment variables
2. **API Structure**: RESTful endpoints with proper request/response schemas
3. **Service Layer**: Separated business logic in `services/llm_service.py` for Azure OpenAI interactions
4. **Error Handling**: Comprehensive try-catch blocks with proper HTTP status codes
5. **Frontend Integration**: Server-side rendering with Jinja2 templates + vanilla JavaScript for interactivity

### Environment Configuration
Required environment variables in `.env`:
```
LLM_API_KEY=your_azure_openai_api_key
LLM_API_ENDPOINT=https://your-endpoint.openai.azure.com
LLM_MODEL=gpt-4
SECRET_KEY=your_secret_key
```

### API Endpoints
- `GET /` - Main chat interface
- `GET /health` - Health check
- `POST /api/chat` - Generate chat responses (streaming supported)
- `POST /api/chat/system` - Generate responses with system messages

### CI/CD Pipeline
GitHub Actions workflow (`.github/workflows/ci-cd.yml`):
1. Runs tests and linting on push/PR
2. Builds and pushes Docker image to GitHub Container Registry
3. Configured for deployment to Azure Kubernetes Service (AKS)

### Development Workflow
1. Always run tests before committing changes
2. Use `pytest --cov` to ensure adequate test coverage
3. Run `ruff check` and `ruff format` for code quality
4. The application uses FastAPI's automatic API documentation at `/docs`
5. Frontend changes are in `app/static/` and `app/templates/`
6. Azure OpenAI integration is handled through the `openai` Python SDK in `app/services/llm_service.py`