#!/usr/bin/env python3
"""Test script for Ollama integration with the chat app."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.schemas.chat import ChatRequest, Message
from app.services.llm_service import LLMService


async def test_ollama_chat():
    """Test Ollama chat completion."""
    print("Testing Ollama integration...")
    
    # Create a request with Ollama provider
    request = ChatRequest(
        messages=[
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Say 'Hello from Ollama!' and nothing else.")
        ],
        model="llama3.2:3b",  # Use a small model for testing
        temperature=0.7,
        provider="ollama"  # Explicitly use Ollama
    )
    
    try:
        # Create service instance (will use default provider from settings)
        service = LLMService()
        
        # Test non-streaming response
        print("\n1. Testing non-streaming response...")
        response = await service.generate_response(request)
        print(f"Response: {response.message.content}")
        print(f"Model used: {response.model}")
        if response.usage:
            print(f"Tokens: {response.usage}")
        
        # Test streaming response
        print("\n2. Testing streaming response...")
        request.stream = True
        print("Streaming: ", end="", flush=True)
        async for chunk in service.stream_response(request):
            print(chunk, end="", flush=True)
        print("\n")
        
        print("\n✅ Ollama integration test successful!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Ollama is running (ollama serve)")
        print("2. You have a model installed (ollama pull llama3.2:3b)")
        return False
    
    return True


async def test_model_switching():
    """Test switching between cloud and local models."""
    print("\n3. Testing model switching...")
    
    service = LLMService()
    
    # Test with default provider (should be OpenAI from config)
    request1 = ChatRequest(
        messages=[Message(role="user", content="Say 'Hello from cloud!'")],
        model="gpt-3.5-turbo"
    )
    
    # Test with Ollama override
    request2 = ChatRequest(
        messages=[Message(role="user", content="Say 'Hello from local!'")],
        model="llama3.2:3b",
        provider="ollama"
    )
    
    try:
        # Only test if both are available
        print("Testing cloud model...")
        # This might fail if no API key is set
        try:
            response1 = await service.generate_response(request1)
            print(f"Cloud response: {response1.message.content[:50]}...")
        except Exception as e:
            print(f"Cloud model not available: {e}")
        
        print("Testing local model...")
        response2 = await service.generate_response(request2)
        print(f"Local response: {response2.message.content[:50]}...")
        
        print("\n✅ Model switching test successful!")
        
    except Exception as e:
        print(f"\n❌ Error in model switching: {e}")
        return False
    
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("OLLAMA INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Test basic Ollama functionality
    success = await test_ollama_chat()
    
    if success:
        # Test model switching
        await test_model_switching()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())