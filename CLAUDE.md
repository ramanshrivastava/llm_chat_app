# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLM Chat App is a FastAPI-based web application that provides a unified chat interface for multiple LLM providers (OpenAI, Anthropic Claude, Google Gemini, and Ollama). Features include intelligent routing with LangGraph agents, conversation memory, web search capabilities, responsive UI with dark mode, code block rendering, and comprehensive security middleware.

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
python -m app.main

# Run with hot reload for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Debug mode with verbose logging
LOG_LEVEL=DEBUG python -m app.main
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
  - `agents/` - LangGraph agents with conversation memory
  - `core/` - Core configuration using Pydantic settings
  - `middleware/` - Security, logging, CORS, and error handling middleware
  - `models/` - Database models (SQLAlchemy)
  - `repositories/` - Data access layer
  - `schemas/` - Pydantic models for request/response validation
  - `services/` - Business logic layer (multi-provider LLM integration, search)
  - `static/` - Frontend assets (CSS, JavaScript)
  - `templates/` - Jinja2 HTML templates
  - `utils/` - Utility functions and helpers
- `tests/` - Test suite organized by unit and integration tests
- `pyproject.toml` - Project configuration and dependencies

### Key Design Patterns
1. **Multi-Provider Architecture**: Unified interface supporting OpenAI, Anthropic, Gemini, and Ollama through `services/llm_service.py`
2. **Agent-Based Processing**: LangGraph agents in `agents/langgraph_agent.py` with state management and conversation memory
3. **Configuration Management**: Uses Pydantic Settings with comprehensive `.env` file support
4. **Layered Architecture**: Clear separation between API, services, repositories, and models
5. **Middleware Stack**: Comprehensive security, logging, CORS, and error handling middleware in correct order
6. **Repository Pattern**: Data access abstraction in `repositories/` for future database integration
7. **Service Layer**: Business logic separation with provider-specific handlers and unified interfaces
8. **Tool Integration**: Web search capabilities through Exa API with Ollama function calling support

### Environment Configuration
Core required environment variables in `.env`:
```
# LLM Provider Configuration
LLM_PROVIDER=openai  # openai, anthropic, gemini, ollama
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4  # Provider-specific model name
LLM_API_ENDPOINT=https://api.openai.com/v1  # For OpenAI/Ollama

# Application Security
SECRET_KEY=your_32_character_secret_key

# Optional: Web Search Integration
EXA_API_KEY=your_exa_api_key
EXA_SEARCH_ENABLED=true

# Optional: Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Optional: Application Settings
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### API Endpoints
- `GET /` - Main chat interface (server-side rendered)
- `GET /health` - Health check with provider and environment status
- `POST /api/chat` - Generate chat responses (supports streaming)
- `POST /api/chat/stream` - Server-sent events streaming endpoint
- `POST /api/chat/system` - Generate responses with system messages
- `GET /docs` - FastAPI auto-generated documentation (development only)
- `GET /redoc` - Alternative API documentation (development only)

### CI/CD Pipeline
GitHub Actions workflow (`.github/workflows/ci-cd.yml`):
1. Runs tests and linting on push/PR
2. Builds and pushes Docker image to GitHub Container Registry
3. Configured for deployment to Azure Kubernetes Service (AKS)

### Development Workflow
1. Always run tests before committing changes: `pytest`
2. Ensure code quality with: `ruff check .` and `ruff format .`
3. Run type checking: `mypy .`
4. Use `pytest --cov` to ensure adequate test coverage
5. The application uses FastAPI's automatic API documentation at `/docs` (development mode)
6. Frontend changes are in `app/static/` and `app/templates/`
7. LLM provider integration is handled through unified service in `app/services/llm_service.py`
8. Agent logic and conversation memory in `app/agents/langgraph_agent.py`
9. Web search functionality in `app/services/search_service.py`
10. All configuration changes should be made in `app/core/config.py`

### LangGraph Agent Architecture
The application uses LangGraph for intelligent conversation handling:
- **State Management**: `AgentState` tracks conversation history, tokens, and processing status
- **Memory Integration**: `MemorySaver` provides conversation persistence across requests
- **Processing Pipeline**: Initialize → LLM Call → Finalize with error handling at each step
- **Thread Support**: Conversations are organized by thread_id for multi-user scenarios
- **Usage**: Agent instance is available globally as `langgraph_agent` in `app/agents/langgraph_agent.py`

### Multi-Provider LLM Integration
The service supports multiple providers through a unified interface:
- **OpenAI**: Full ChatGPT API support with streaming
- **Anthropic**: Claude models with message-based API
- **Google Gemini**: Generative AI models with conversation format
- **Ollama**: Local models with tool calling and web search integration
- **Provider Selection**: Set `LLM_PROVIDER` environment variable or specify in request
- **Tool Support**: Ollama supports function calling for web search (Exa integration)

### Web Search Integration
Exa-powered web search available for enhanced responses:
- **Configuration**: Set `EXA_API_KEY` and `EXA_SEARCH_ENABLED=true`
- **Tool Calling**: Automatically available for compatible Ollama models
- **Search Categories**: General, news, research papers, forums, etc.
- **Domain Filtering**: Include/exclude specific domains in search results
- **Service**: `app/services/search_service.py` handles all search operations