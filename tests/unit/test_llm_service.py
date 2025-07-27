import types
from unittest.mock import patch

import pytest

from app.services.llm_service import LLMService
from app.schemas.chat import ChatRequest, Message


@pytest.mark.asyncio
async def test_generate_response_openai(monkeypatch):
    # Set up provider to openai
    monkeypatch.setattr('app.core.config.settings', type('S', (), {
        'LLM_PROVIDER': 'openai',
        'LLM_MODEL': 'gpt-4',
        'LLM_API_KEY': 'x',
        'LLM_API_ENDPOINT': 'https://example.com',
    })())

    sync_client = types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(
                create=lambda **kwargs: types.SimpleNamespace(
                    choices=[
                        types.SimpleNamespace(
                            message=types.SimpleNamespace(content="ok")
                        )
                    ],
                    usage=types.SimpleNamespace(
                        prompt_tokens=1, completion_tokens=1, total_tokens=2
                    ),
                )
            )
        )
    )

    with patch('openai.OpenAI', return_value=sync_client):
        svc = LLMService()
        req = ChatRequest(messages=[Message(role='user', content='hi')])
        resp = await svc.generate_response(req)

    assert resp.message.content == 'ok'
    assert resp.model == 'gpt-4'


