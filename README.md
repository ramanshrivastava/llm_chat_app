# LLM Chat App

A modern chat application powered by multiple providers (OpenAI, Anthropic, and Google's Gemini), allowing users to interact with various LLM models through a clean and intuitive interface.

## Features

- Chat with OpenAI, Anthropic, or Gemini models using a unified API
- Adjustable parameters (temperature, max tokens)
- Code block rendering
- Dark mode support
- Responsive design for mobile and desktop
- Token usage tracking

## Tech Stack

- **Backend**: FastAPI, Python 3.12.2
- **Frontend**: HTML, CSS, JavaScript
- **LLM Integration**: OpenAI-compatible providers (OpenAI, Anthropic, Gemini)
- **Dependency Management**: uv
- **Containerization**: Docker
- **Deployment**: Azure Kubernetes Service (AKS)
- **CI/CD**: GitHub Actions
- **Source Control**: GitHub

## Getting Started

### Prerequisites

- Python 3.12.2
- API key for your chosen LLM provider

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/llm_chat_app.git
   cd llm_chat_app
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

3. Create a `.env` file in the root directory with your LLM provider settings:
   ```
   LLM_API_KEY=your_api_key_here
    LLM_API_ENDPOINT=https://api.openai.com/v1
    LLM_MODEL=gpt-4
    LLM_PROVIDER=openai
   SECRET_KEY=your_secret_key_here
   ```

4. Run the application:
   ```bash
   python main.py
   ```

5. Open your browser and navigate to `http://localhost:8000`

## Running Tests

Install the development dependencies before running the tests. The `dev` extras
include `pytest` and `pytest-cov`:

```bash
pip install -e .[dev]
pytest
```

## API Endpoints

- `GET /`: Home page with chat interface
- `GET /health`: Health check endpoint
- `POST /api/chat`: Generate a chat response
- `POST /api/chat/system`: Generate a response with a system message

## Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t llm-chat-app .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env llm-chat-app
   ```

## Deployment to AKS with Kustomize

Kubernetes manifests are provided in the `k8s/` directory. The `base` folder
contains common resources and `overlays/production` contains production
configuration such as replica count and image tag.

Deploy the application with:

```bash
kubectl apply -k k8s/overlays/production
```

Create a `llm-chat-app-secrets` secret in the namespace with your API keys
before applying the manifests.

## Provisioning AKS with Pulumi

The `infra/pulumi` folder holds a Pulumi program for creating the AKS cluster.
Install the requirements and run `pulumi up`:

```bash
cd infra/pulumi
pip install -r requirements.txt
pulumi up
```

The program provisions a resource group and an AKS cluster and exports the
kubeconfig for cluster access.

## GitOps with Argo CD

Once the cluster is running and Argo CD is installed, create an application that
points to the Kustomize overlay:

```bash
argocd app create llm-chat-app \
  --repo https://github.com/yourusername/llm_chat_app.git \
  --path k8s/overlays/production \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default

argocd app sync llm-chat-app
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI, Anthropic and Google for providing the LLM capabilities
- FastAPI for the efficient API framework
- The open-source community for various libraries and tools used in this project


