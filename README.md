# LLM Chat App

A modern, secure chat application powered by multiple LLM providers (OpenAI, Anthropic, and Google's Gemini), featuring a clean interface, real-time streaming, and comprehensive security measures.

## 🚀 Features

### Core Features
- **Multi-Provider Support**: OpenAI, Anthropic Claude, and Google Gemini
- **Real-time Streaming**: OpenAI-compatible Server-Sent Events (SSE)
- **Beautiful UI**: Modern, responsive design with dark mode support
- **Code Highlighting**: Syntax highlighting for code blocks with copy functionality
- **Chat Persistence**: Automatic saving and loading of chat history
- **Export Functionality**: Export chat history as text files

### Security Features
- **Input Validation**: Comprehensive validation for all user inputs
- **Rate Limiting**: Configurable rate limiting per IP
- **CORS Protection**: Restricted origins with environment-based configuration
- **Secure Headers**: Comprehensive security headers and middleware
- **Environment Validation**: Strict validation of configuration settings

### Technical Features
- **Type Safety**: Full TypeScript-style annotations and validation
- **Comprehensive Testing**: Unit and integration tests with high coverage
- **Docker Ready**: Multi-stage builds with security best practices
- **Kubernetes Native**: Production-ready K8s manifests with health checks
- **Monitoring Ready**: Prometheus metrics and health endpoints

## 🛠️ Tech Stack

- **Backend**: FastAPI 0.115+, Python 3.12+
- **Frontend**: Vanilla JavaScript (ES6+), Bootstrap 5, Custom CSS
- **LLM Integration**: OpenAI, Anthropic, Google Generative AI APIs
- **Agent Framework**: LangGraph for intelligent routing
- **Deployment**: Docker, Kubernetes, Azure (production ready)
- **Testing**: pytest, FastAPI TestClient
- **Monitoring**: Prometheus-compatible metrics

## 📋 Prerequisites

- Python 3.12+
- API key for your chosen LLM provider(s)
- Docker (optional, for containerized deployment)
- Kubernetes cluster (optional, for production deployment)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/llm_chat_app.git
cd llm_chat_app

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Environment Configuration

```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your settings
# Required: LLM_API_KEY, SECRET_KEY
# Optional: Customize other settings
```

### 3. Run the Application

```bash
# Development mode
python -m app.main

# Or with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the Application

Open your browser and navigate to `http://localhost:8000`

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM_API_KEY` | API key for your LLM provider | - | ✅ |
| `SECRET_KEY` | Security key (32+ characters) | - | ✅ |
| `LLM_PROVIDER` | Provider: openai, anthropic, gemini | openai | No |
| `LLM_MODEL` | Model name | gpt-4 | No |
| `LLM_API_ENDPOINT` | API endpoint URL | https://api.openai.com/v1 | No |
| `APP_ENV` | Environment: development, production | development | No |
| `DEBUG` | Enable debug mode | true | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `ALLOWED_ORIGINS` | CORS allowed origins | ["http://localhost:3000", "http://localhost:8000"] | No |
| `RATE_LIMIT_REQUESTS` | Requests per window | 100 | No |
| `RATE_LIMIT_WINDOW` | Rate limit window (seconds) | 60 | No |

### Provider-Specific Setup

#### OpenAI
```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-key
LLM_MODEL=gpt-4
LLM_API_ENDPOINT=https://api.openai.com/v1
```

#### Anthropic Claude
```bash
LLM_PROVIDER=anthropic
LLM_API_KEY=your-anthropic-key
LLM_MODEL=claude-3-sonnet-20240229
```

#### Google Gemini
```bash
LLM_PROVIDER=gemini
LLM_API_KEY=your-google-api-key
LLM_MODEL=gemini-pro
```

## 🧪 Testing

### Run All Tests
```bash
# Install test dependencies
pip install -e .[dev]

# Run tests with coverage
pytest

# Run specific test types
pytest -m unit
pytest -m integration

# Generate coverage report
pytest --cov=. --cov-report=html
```

### Test Structure
- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: API endpoint and integration tests

## 🔧 Development

### Code Quality
```bash
# Type checking
mypy .

# Linting and formatting
ruff check .
ruff format .

# Pre-commit hooks (recommended)
pre-commit install
```

### Local Development
```bash
# Hot reload development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Debug mode with verbose logging
LOG_LEVEL=DEBUG python -m app.main
```

## 🐳 Docker Deployment

### Build and Run
```bash
# Build the image
docker build -t llm-chat-app .

# Run with environment file
docker run -p 8000:8000 --env-file .env llm-chat-app

# Or with individual environment variables
docker run -p 8000:8000 \
  -e LLM_API_KEY=your-key \
  -e SECRET_KEY=your-secret \
  llm-chat-app
```

### Docker Compose (Development)
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_API_KEY=your-key
      - SECRET_KEY=your-secret
    volumes:
      - .:/app
```

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes cluster
- kubectl configured
- Docker image built and pushed to registry

### Deploy to Kubernetes
```bash
# Update image in deployment.yaml
# Set your secrets in service.yaml

# Apply manifests
kubectl apply -f k8s/base/

# For production
kubectl apply -k k8s/overlays/production/

# Check deployment
kubectl get pods -l app=llm-chat-app
kubectl logs -l app=llm-chat-app
```

### Production Considerations
- Update `LLM_API_KEY` and `SECRET_KEY` in the Secret
- Configure `ALLOWED_ORIGINS` for your domain
- Set up ingress controller and TLS certificates
- Configure monitoring and logging
- Set resource limits based on your requirements

## 🔍 Monitoring

### Health Checks
- `GET /health`: Application health status
- Returns: `{"status": "healthy", "environment": "...", "provider": "..."}`

### Metrics
- Prometheus-compatible metrics at `/metrics` (if enabled)
- Request logging with timing information
- Error tracking and alerting ready

### Logging
- Structured JSON logging in production
- Configurable log levels
- Separate log files per environment

## 🔐 Security

### Implemented Security Measures
- **CORS Protection**: Configurable allowed origins
- **Rate Limiting**: Per-IP request limits
- **Input Validation**: Comprehensive input sanitization
- **Security Headers**: HSTS, CSP, and other security headers
- **Environment Validation**: Strict configuration validation
- **Non-root Container**: Docker runs as non-root user
- **Read-only Filesystem**: Container filesystem restrictions

### Production Security Checklist
- [ ] Generate secure `SECRET_KEY` (32+ characters)
- [ ] Set strong API keys
- [ ] Configure `ALLOWED_ORIGINS` for your domain
- [ ] Enable HTTPS with valid certificates
- [ ] Set up monitoring and alerting
- [ ] Regular security updates
- [ ] Network policies in Kubernetes
- [ ] Secrets management (Vault, etc.)

## 🎨 Frontend Features

### User Interface
- **Responsive Design**: Works on desktop and mobile
- **Dark Mode**: Toggle between light and dark themes
- **Real-time Updates**: Streaming responses with progress indication
- **Code Highlighting**: Syntax highlighting for code blocks
- **Copy Functionality**: One-click code copying
- **Export**: Download chat history as text file

### Keyboard Shortcuts
- `Ctrl/Cmd + Enter`: Send message
- `Escape`: Stop generation
- `Shift + Enter`: New line in input

### Accessibility
- Keyboard navigation support
- Screen reader compatible
- High contrast mode support
- Reduced motion preferences

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Use type hints
- Write clear commit messages

## 📄 API Documentation

When running in development mode, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints
- `POST /api/chat`: Generate chat response
- `POST /api/chat/stream`: Stream chat response
- `POST /api/chat/system`: Chat with system message
- `GET /health`: Health check

## 🐛 Troubleshooting

### Common Issues

#### "API key validation failed"
- Ensure your API key is set correctly in `.env`
- Check that the key has sufficient permissions
- Verify the key format for your provider

#### "Rate limit exceeded"
- Wait for the rate limit window to reset
- Adjust `RATE_LIMIT_REQUESTS` if needed
- Consider implementing user authentication

#### "CORS error"
- Add your frontend domain to `ALLOWED_ORIGINS`
- Ensure the origins are properly formatted as JSON array

#### Container fails to start
- Check environment variables are set
- Verify the `SECRET_KEY` is at least 32 characters
- Check container logs: `docker logs <container_id>`

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG python -m app.main

# Check configuration
python -c "from app.core.config import settings; print(settings)"
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- [OpenAI](https://openai.com/), [Anthropic](https://anthropic.com/), and [Google](https://ai.google.dev/) for LLM APIs
- The open-source community for inspiration and tools

## 📞 Support

- 📧 Email: support@yourdomain.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/llm_chat_app/issues)
- 📖 Documentation: [Wiki](https://github.com/yourusername/llm_chat_app/wiki)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/llm_chat_app/discussions)

