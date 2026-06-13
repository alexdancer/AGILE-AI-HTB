from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import litellm


class LLMClient:
    async def acompletion(self, request: dict[str, Any]) -> Any:
        return await litellm.acompletion(**request)


def extract_usage(response: Any) -> dict[str, int]:
    usage = _get(response, "usage", {}) or {}
    prompt_tokens = int(_get(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(_get(usage, "completion_tokens", 0) or 0)
    total_tokens = int(_get(usage, "total_tokens", prompt_tokens + completion_tokens) or 0)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    try:
        return float(
            litellm.completion_cost(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        )
    except Exception:
        return None


async def final_stream_usage(chunks: AsyncIterator[Any]) -> dict[str, int]:
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    async for chunk in chunks:
        chunk_usage = extract_usage(chunk)
        if any(chunk_usage.values()):
            usage = chunk_usage
    return usage


def response_to_dict(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return response
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "dict"):
        return response.dict()
    raise TypeError(f"unsupported LLM response type: {type(response)!r}")


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)
