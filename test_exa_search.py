#!/usr/bin/env python3
"""
Test script for Exa web search integration with Ollama models.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

async def test_exa_search():
    """Test the Exa search service directly."""
    print("\n" + "="*50)
    print("Testing Exa Search Service")
    print("="*50)
    
    from app.services.search_service import search_service
    
    # Check configuration
    print(f"\n1. Configuration Check:")
    print(f"   - Search Enabled: {search_service.enabled}")
    print(f"   - API Key Set: {bool(search_service.api_key)}")
    
    if not search_service.enabled:
        print("\n⚠️  Search service is not enabled!")
        print("   Please set EXA_API_KEY and EXA_SEARCH_ENABLED=true in your .env file")
        return False
    
    # Test basic search
    print(f"\n2. Testing Basic Search:")
    query = "latest developments in AI safety 2025"
    print(f"   Query: '{query}'")
    
    try:
        results = await search_service.search(query, num_results=3)
        print(f"   Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.title[:60]}...")
            print(f"      URL: {result.url}")
            if result.snippet:
                print(f"      Snippet: {result.snippet[:100]}...")
        print("   ✅ Basic search successful!")
    except Exception as e:
        print(f"   ❌ Search failed: {str(e)}")
        return False
    
    # Test category search
    print(f"\n3. Testing Category Search (news):")
    try:
        results = await search_service.search(
            "OpenAI GPT", 
            num_results=2,
            category="news"
        )
        print(f"   Found {len(results)} news results")
        print("   ✅ Category search successful!")
    except Exception as e:
        print(f"   ❌ Category search failed: {str(e)}")
    
    # Test formatting for LLM
    print(f"\n4. Testing LLM Formatting:")
    if results:
        formatted = search_service.format_for_llm(results, max_results=2)
        print("   Formatted output:")
        print("   " + formatted.replace("\n", "\n   ")[:300] + "...")
        print("   ✅ Formatting successful!")
    
    return True

async def test_ollama_with_search():
    """Test Ollama integration with web search."""
    print("\n" + "="*50)
    print("Testing Ollama Integration with Web Search")
    print("="*50)
    
    from app.schemas.chat import ChatRequest, Message
    from app.services.llm_service import LLMService
    from app.core.config import settings
    
    # Check if Ollama is available
    try:
        import ollama
        client = ollama.Client()
        models = client.list()
        print(f"\n1. Ollama Check:")
        print(f"   - Ollama is running")
        print(f"   - Available models: {len(models.get('models', []))}")
        
        # Find a compatible model
        compatible_model = None
        for model in models.get('models', []):
            name = model.get('name', '')
            if 'gpt-oss' in name.lower() or 'llama' in name.lower():
                compatible_model = name
                break
        
        if not compatible_model:
            print("   ⚠️  No compatible models found (need GPT-OSS or Llama)")
            print("   Run: ollama pull gpt-oss:20b")
            return False
            
        print(f"   - Using model: {compatible_model}")
        
    except Exception as e:
        print(f"\n⚠️  Ollama is not running or not installed")
        print(f"   Error: {str(e)}")
        print("   Please start Ollama and pull a compatible model")
        return False
    
    # Test with search enabled
    print(f"\n2. Testing Chat with Web Search:")
    
    # Create a test request that should trigger search
    request = ChatRequest(
        messages=[
            Message(role="user", content="What are the latest features in GPT-OSS models announced by OpenAI?")
        ],
        model=compatible_model.split(':')[0],  # Remove tag
        provider="ollama",
        temperature=0.7,
        enable_search=True,
        stream=False
    )
    
    # Create service instance
    service = LLMService(provider="ollama", model=compatible_model)
    
    print(f"   Sending query to {compatible_model}...")
    print(f"   Web search: Enabled")
    
    try:
        response = await service.generate_response(request)
        print(f"\n   Response received:")
        print(f"   {response.message.content[:500]}...")
        
        if response.usage:
            print(f"\n   Token usage:")
            print(f"   - Prompt: {response.usage.get('prompt_tokens', 'N/A')}")
            print(f"   - Completion: {response.usage.get('completion_tokens', 'N/A')}")
        
        print("\n   ✅ Ollama with web search successful!")
        
    except Exception as e:
        print(f"\n   ❌ Request failed: {str(e)}")
        return False
    
    return True

async def main():
    """Run all tests."""
    print("\n🚀 Starting Exa Search Integration Tests\n")
    
    # Test Exa search service
    exa_success = await test_exa_search()
    
    # Only test Ollama if Exa is working
    if exa_success:
        ollama_success = await test_ollama_with_search()
    else:
        ollama_success = False
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    print(f"✅ Exa Search Service: {'PASSED' if exa_success else 'FAILED'}")
    print(f"{'✅' if ollama_success else '❌'} Ollama Integration: {'PASSED' if ollama_success else 'FAILED/SKIPPED'}")
    
    if exa_success and ollama_success:
        print("\n🎉 All tests passed! Web search is ready to use.")
        print("\nTo use in the chat app:")
        print("1. Start the app: python main.py")
        print("2. Select an Ollama model (GPT-OSS or Llama)")
        print("3. Enable web search with the checkbox")
        print("4. Ask questions that need current information")
    elif exa_success:
        print("\n⚠️  Exa search works but Ollama integration needs setup.")
        print("Please ensure Ollama is running with a compatible model.")
    else:
        print("\n❌ Tests failed. Please check your configuration.")

if __name__ == "__main__":
    asyncio.run(main())