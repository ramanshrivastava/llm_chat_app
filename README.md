# LLM Chat App

A modern chat application powered by multiple providers (Azure OpenAI, OpenAI, Anthropic, and Google's Gemini), allowing users to interact with various LLM models through a clean and intuitive interface.

## Features

- Chat with Azure OpenAI, OpenAI, Anthropic, or Gemini models using a unified API
- Adjustable parameters (temperature, max tokens)
- Code block rendering
- Dark mode support
- Responsive design for mobile and desktop
- Token usage tracking
- OpenAI-style streaming responses via SSE

## Tech Stack

- **Backend**: FastAPI, Python 3.12.2
- **Frontend**: HTML, CSS, JavaScript
- **LLM Integration**: OpenAI-compatible providers (Azure OpenAI, OpenAI, Anthropic, Gemini)
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

3. Create a `.env` file in the root directory with your LLM provider settings.
   Example for Azure OpenAI:
   ```
   LLM_API_KEY=your_api_key_here
   LLM_PROVIDER=azure
   LLM_API_ENDPOINT=https://your-resource.openai.azure.com
   LLM_DEPLOYMENT=your-deployment-name
   LLM_API_VERSION=2024-02-15-preview
   LLM_MODEL=gpt-4
   SECRET_KEY=your_secret_key_here
   ```
   For OpenAI or Anthropic, set `LLM_PROVIDER` to `openai` or `anthropic` and
   adjust the endpoint and model accordingly.

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
- `POST /api/chat/stream`: Stream a response using SSE

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
contains common resources while `overlays/dev` and `overlays/production`
provide environment-specific configuration. The production overlay scales the
deployment and sets the image tag, whereas the dev overlay uses a lightweight
configuration for testing.

Deploy the application with:

```bash
kubectl apply -k k8s/overlays/production
```

For testing or preview environments you can use the dev overlay:

```bash
kubectl apply -k k8s/overlays/dev
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

## Continuous Deployment with GitHub Actions

The included GitHub Actions workflow builds the Docker image and deploys the
Kustomize overlay to AKS. Define the following repository secrets:

- `AZURE_CREDENTIALS` &ndash; output of `az ad sp create-for-rbac`
- `AKS_RESOURCE_GROUP` &ndash; resource group of the cluster
- `AKS_CLUSTER_NAME` &ndash; name of the AKS cluster

On pushes to `main` the workflow logs in to Azure, sets the cluster context and
applies the production overlay.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI, Azure OpenAI, Anthropic and Google for providing the LLM capabilities
- FastAPI for the efficient API framework
- The open-source community for various libraries and tools used in this project


