import pytest

from token_tracker_harness import llm
from token_tracker_harness.llm import LLMClient, calculate_cost, extract_usage, final_stream_usage


@pytest.mark.asyncio
async def test_llm_client_forwards_request_to_litellm(monkeypatch):
    captured = {}

    async def fake_acompletion(**kwargs):
        captured.update(kwargs)
        return {"id": "chatcmpl_fake", "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}}

    monkeypatch.setattr(llm.litellm, "acompletion", fake_acompletion)

    response = await LLMClient().acompletion({"model": "fake-model", "messages": [{"role": "user", "content": "hi"}]})

    assert captured["model"] == "fake-model"
    assert response["usage"]["total_tokens"] == 5


def test_extract_usage_supports_dict_and_object_responses():
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
    assert extract_usage(Response()) == {"prompt_tokens": 7, "completion_tokens": 11, "total_tokens": 18}


def test_calculate_cost_returns_none_when_litellm_pricing_unavailable(monkeypatch):
    def fake_completion_cost(**kwargs):
        raise KeyError("unknown model")

    monkeypatch.setattr(llm.litellm, "completion_cost", fake_completion_cost)

    assert calculate_cost("unknown-model", 10, 20) is None


def test_calculate_cost_wraps_litellm_completion_cost(monkeypatch):
    def fake_completion_cost(**kwargs):
        assert kwargs == {"model": "fake-model", "prompt_tokens": 10, "completion_tokens": 20}
        return 0.123

    monkeypatch.setattr(llm.litellm, "completion_cost", fake_completion_cost)

    assert calculate_cost("fake-model", 10, 20) == 0.123


@pytest.mark.asyncio
async def test_final_stream_usage_uses_only_last_usage_chunk():
    async def chunks():
        yield {"choices": [{"delta": {"content": "a"}}], "usage": {"prompt_tokens": 100, "completion_tokens": 100, "total_tokens": 200}}
        yield {"choices": [{"delta": {"content": "b"}}]}
        yield {"choices": [], "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}}

    assert await final_stream_usage(chunks()) == {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}
