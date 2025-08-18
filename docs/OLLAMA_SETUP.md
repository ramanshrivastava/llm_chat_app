# Using Ollama with LLM Chat App

This guide explains how to use local models through Ollama with the LLM Chat App, including GPT-OSS models.

## Prerequisites

1. **Install Ollama**
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Start Ollama Service**
   ```bash
   ollama serve
   ```

3. **Download Models**
   ```bash
   # GPT-OSS 20B (OpenAI's open model)
   ollama pull gpt-oss:20b
   
   # Other recommended models
   ollama pull llama3.1:70b        # Meta's latest, very capable
   ollama pull mixtral:8x7b        # Good for reasoning
   ollama pull deepseek-coder:6.7b # Excellent for code
   ollama pull llama3.2:3b         # Fast, lightweight
   ```

## Configuration

### Option 1: Use Ollama as Default Provider

1. Copy the example environment file:
   ```bash
   cp .env.ollama.example .env
   ```

2. The key settings are:
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   LLM_MODEL=gpt-oss:20b
   ```

### Option 2: Hybrid Setup (Cloud + Local)

Keep your existing Azure/OpenAI configuration and select Ollama models from the UI:

1. Keep your current `.env` with Azure/OpenAI settings
2. Add Ollama configuration:
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   ```
3. Select Ollama models from the dropdown in the UI (marked with 🏠)

## Usage

### From the Web Interface

1. Start the application:
   ```bash
   python main.py
   ```

2. Open http://localhost:8000

3. In the Model dropdown, select any model marked with 🏠:
   - **GPT-OSS 20B 🏠** - OpenAI's open model
   - **Llama 3.1 70B 🏠** - Meta's latest
   - **Mixtral 8x7B 🏠** - MoE architecture
   - **DeepSeek Coder 🏠** - For programming
   - **Llama 3.2 3B (Fast) 🏠** - Quick responses

### From Python Code

```python
from app.schemas.chat import ChatRequest, Message
from app.services.llm_service import LLMService

# Create a request specifying Ollama
request = ChatRequest(
    messages=[
        Message(role="user", content="Hello, GPT-OSS!")
    ],
    model="gpt-oss:20b",
    provider="ollama"  # Explicitly use Ollama
)

# Generate response
service = LLMService()
response = await service.generate_response(request)
print(response.message.content)
```

## Testing

Run the test script to verify your setup:

```bash
python test_ollama.py
```

## Performance Tips

### For M4 Pro (48GB RAM)

**Recommended Models by Use Case:**
- **General Chat**: `gpt-oss:20b` or `llama3.1:70b-q4`
- **Fast Responses**: `llama3.2:3b` or `phi3:mini`
- **Code Generation**: `deepseek-coder:6.7b` or `codellama:13b`
- **Long Context**: `yarn-mistral:7b-128k`

**Memory Usage:**
- GPT-OSS 20B: ~12-15GB RAM
- Llama 3.1 70B (4-bit): ~35-40GB RAM
- Mixtral 8x7B: ~25-30GB RAM
- Small models (3-7B): 4-8GB RAM

### Optimization

1. **Keep Models Loaded**: Ollama keeps models in memory for 5 minutes by default
   ```bash
   # Keep a model loaded longer
   ollama run gpt-oss:20b --keepalive 30m
   ```

2. **Use Appropriate Quantization**: 
   - Q4 models offer best balance of quality/speed
   - Q8 for maximum quality (uses more RAM)
   - Q2-Q3 for speed (lower quality)

3. **Monitor Performance**:
   ```bash
   # Check loaded models
   ollama ps
   
   # See model details
   ollama show gpt-oss:20b
   ```

## Troubleshooting

### "Connection refused" error
- Ensure Ollama is running: `ollama serve`
- Check if port 11434 is available: `lsof -i :11434`

### "Model not found" error
- Download the model first: `ollama pull model-name`
- Check available models: `ollama list`

### Slow responses
- Check RAM usage: `top` or Activity Monitor
- Use a smaller/quantized model
- Close other applications to free RAM

### Application doesn't show Ollama models
- Restart the application after installing `ollama` package:
  ```bash
  pip install -e ".[dev]"  # Reinstall dependencies
  python main.py
  ```

## Benefits of Local Models

✅ **Privacy**: Your data never leaves your machine
✅ **No API Costs**: Free after initial download
✅ **Offline Access**: Works without internet
✅ **Low Latency**: No network roundtrip
✅ **Customization**: Fine-tune models for your needs

## Next Steps

1. Try different models to find what works best for your use case
2. Experiment with temperature and max_tokens settings
3. Consider fine-tuning models for specialized tasks
4. Set up model switching for different types of queries