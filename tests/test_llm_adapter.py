import pytest

from agile_ai_htb.llm import LLMClient, LLMClientError, calculate_cost, extract_usage, final_stream_usage
from agile_ai_htb.settings import Settings


@pytest.mark.asyncio
async def test_llm_client_forwards_openai_compatible_request(monkeypatch):
    captured = {}

    def fake_post_json(url, headers, payload):
        captured.update({"url": url, "headers": headers, "payload": payload})
        return {"id": "chatcmpl_fake", "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}}

    monkeypatch.setenv("CONTROL_TEST_KEY", "test-key")
    settings = Settings(
        control_plane_provider="openai-compatible",
        control_plane_model="openai/gpt-4.1-mini",
        control_plane_api_key_env="CONTROL_TEST_KEY",
        control_plane_base_url="https://provider.example/v1",
    )

    response = await LLMClient(settings, http_post_json=fake_post_json).acompletion(
        {"model": "openai/gpt-4.1-mini", "messages": [{"role": "user", "content": "hi"}]}
    )

    assert captured["url"] == "https://provider.example/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["payload"]["model"] == "gpt-4.1-mini"
    assert response["usage"]["total_tokens"] == 5


@pytest.mark.asyncio
async def test_llm_client_translates_anthropic_messages(monkeypatch):
    captured = {}

    def fake_post_json(url, headers, payload):
        captured.update({"url": url, "headers": headers, "payload": payload})
        return {
            "id": "msg_fake",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "done"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 7, "output_tokens": 11},
        }

    monkeypatch.setenv("CONTROL_TEST_KEY", "sk-ant-test")
    settings = Settings(
        control_plane_provider="anthropic",
        control_plane_model="anthropic/claude-sonnet-4-20250514",
        control_plane_api_key_env="CONTROL_TEST_KEY",
    )

    response = await LLMClient(settings, http_post_json=fake_post_json).acompletion(
        {
            "model": "anthropic/claude-sonnet-4-20250514",
            "messages": [
                {"role": "system", "content": "be concise"},
                {"role": "user", "content": "hi"},
            ],
            "max_tokens": 12,
            "temperature": 0,
        }
    )

    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    assert captured["headers"]["x-api-key"] == "sk-ant-test"
    assert captured["payload"] == {
        "model": "claude-sonnet-4-20250514",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 12,
        "system": "be concise",
        "temperature": 0,
    }
    assert response["choices"][0]["message"]["content"] == "done"
    assert response["usage"] == {"prompt_tokens": 7, "completion_tokens": 11, "total_tokens": 18}


@pytest.mark.asyncio
async def test_llm_client_rejects_missing_credentials(monkeypatch):
    monkeypatch.delenv("MISSING_CONTROL_KEY", raising=False)
    monkeypatch.delenv("MISSING_LEGACY_KEY", raising=False)
    settings = Settings(control_plane_api_key_env="MISSING_CONTROL_KEY", provider_api_key_env="MISSING_LEGACY_KEY")

    with pytest.raises(LLMClientError, match="missing control-plane API key env"):
        await LLMClient(settings).acompletion({"model": "gpt-4o-mini", "messages": []})


@pytest.mark.asyncio
async def test_llm_client_rejects_unsupported_provider(monkeypatch):
    monkeypatch.setenv("CONTROL_TEST_KEY", "test-key")
    settings = Settings(control_plane_provider="unsupported", control_plane_api_key_env="CONTROL_TEST_KEY")

    with pytest.raises(LLMClientError, match="unsupported control-plane provider"):
        await LLMClient(settings).acompletion({"model": "x", "messages": []})


@pytest.mark.asyncio
async def test_llm_client_rejects_anthropic_streaming_clearly(monkeypatch):
    monkeypatch.setenv("CONTROL_TEST_KEY", "sk-ant-test")
    settings = Settings(control_plane_provider="anthropic", control_plane_api_key_env="CONTROL_TEST_KEY")

    with pytest.raises(LLMClientError, match="anthropic streaming is not supported"):
        await LLMClient(settings).acompletion({"model": "claude-sonnet-4-20250514", "messages": [], "stream": True})


def test_extract_usage_supports_openai_anthropic_dict_and_object_responses():
    class Usage:
        prompt_tokens = 7
        completion_tokens = 11
        total_tokens = 18

    class Response:
        usage = Usage()

    assert extract_usage({"usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}}) == {
        "prompt_tokens": 2,
        "completion_tokens": 3,
        "total_tokens": 5,
    }
    assert extract_usage({"usage": {"input_tokens": 13, "output_tokens": 17}}) == {
        "prompt_tokens": 13,
        "completion_tokens": 17,
        "total_tokens": 30,
    }
    assert extract_usage(Response()) == {"prompt_tokens": 7, "completion_tokens": 11, "total_tokens": 18}


def test_calculate_cost_returns_none_when_pricing_unavailable():
    assert calculate_cost("unknown-model", 10, 20) is None


def test_calculate_cost_uses_optional_local_pricing_when_available():
    assert calculate_cost("gpt-4o-mini", 10, 20) == pytest.approx(0.0000135)


@pytest.mark.asyncio
async def test_llm_client_translates_gpt5_max_tokens_to_max_completion_tokens(monkeypatch):
    captured = {}

    def fake_post_json(url, headers, payload):
        captured.update({"payload": payload})
        return {"id": "chatcmpl_fake", "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}}

    monkeypatch.setenv("CONTROL_TEST_KEY", "test-key")
    settings = Settings(
        control_plane_provider="openai",
        control_plane_model="gpt-5.4-mini",
        control_plane_api_key_env="CONTROL_TEST_KEY",
    )

    await LLMClient(settings, http_post_json=fake_post_json).acompletion(
        {
            "model": "gpt-5.4-mini",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 12,
        }
    )

    assert "max_tokens" not in captured["payload"]
    assert captured["payload"]["max_completion_tokens"] == 12


@pytest.mark.asyncio
async def test_final_stream_usage_uses_only_last_usage_chunk():
    async def chunks():
        yield {"choices": [{"delta": {"content": "a"}}], "usage": {"prompt_tokens": 100, "completion_tokens": 100, "total_tokens": 200}}
        yield {"choices": [{"delta": {"content": "b"}}]}
        yield {"choices": [], "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}}

    assert await final_stream_usage(chunks()) == {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}