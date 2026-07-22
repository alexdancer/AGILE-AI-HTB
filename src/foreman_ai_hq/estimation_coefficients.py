from __future__ import annotations

import functools
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import importlib.resources


_FACTORS = ("a", "b", "g", "p", "k")
_DEFAULT_ADAPTER_KEY = "default"


@dataclass(frozen=True)
class CoefficientSet:
    values: dict[str, float]
    provenance: dict[str, str]

    def __getitem__(self, key: str) -> float:
        return self.values[key]


def _coefficients_path() -> Path:
    # ponytail: use package resources so the file survives installs.
    return Path(str(importlib.resources.files("foreman_ai_hq") / "data" / "estimation_coefficients.json"))


@functools.lru_cache(maxsize=1)
def _raw_coefficients() -> dict[str, Any]:
    path = _coefficients_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CoefficientLoadError(f"failed to load estimation coefficients: {exc}") from exc
    if not isinstance(data, dict) or _DEFAULT_ADAPTER_KEY not in data:
        raise CoefficientLoadError("estimation coefficients must contain a 'default' block")
    _validate_block(data[_DEFAULT_ADAPTER_KEY], _DEFAULT_ADAPTER_KEY)
    for adapter_id, block in data.items():
        if adapter_id == _DEFAULT_ADAPTER_KEY:
            continue
        if not isinstance(block, dict):
            raise CoefficientLoadError(f"adapter block '{adapter_id}' must be an object")
        for key, inner in block.items():
            _validate_block(inner, f"{adapter_id}.{key}")
    return data


class CoefficientLoadError(Exception):
    """Raised when the checked-in coefficient file is missing or malformed."""


def _validate_block(block: Any, name: str) -> None:
    if not isinstance(block, dict):
        raise CoefficientLoadError(f"coefficient block '{name}' must be an object")
    for factor in _FACTORS:
        if factor not in block:
            raise CoefficientLoadError(f"coefficient block '{name}' missing factor '{factor}'")
        entry = block[factor]
        if not isinstance(entry, dict):
            raise CoefficientLoadError(f"coefficient block '{name}' factor '{factor}' must be an object")
        if "value" not in entry or not isinstance(entry["value"], (int, float)):
            raise CoefficientLoadError(f"coefficient block '{name}' factor '{factor}' must have numeric 'value'")
        if "provenance" not in entry or not isinstance(entry["provenance"], str):
            raise CoefficientLoadError(f"coefficient block '{name}' factor '{factor}' must have string 'provenance'")
        if not re.fullmatch(r"seed|fitted\(\d+\)", entry["provenance"]):
            raise CoefficientLoadError(
                f"coefficient block '{name}' factor '{factor}' provenance must be 'seed' or 'fitted(n)'"
            )


def resolve_coefficients(adapter_id: str | None, model_id: str | None) -> CoefficientSet:
    """Resolve (adapter, model) → coefficient set, falling back to adapter default then global default."""
    data = _raw_coefficients()
    block = _find_block(data, adapter_id, model_id)
    values = {factor: float(block[factor]["value"]) for factor in _FACTORS}
    provenance = {factor: block[factor]["provenance"] for factor in _FACTORS}
    return CoefficientSet(values=values, provenance=provenance)


def _find_block(
    data: dict[str, Any],
    adapter_id: str | None,
    model_id: str | None,
) -> dict[str, Any]:
    adapter_key = adapter_id if adapter_id and adapter_id in data else None
    if adapter_key:
        adapter_block = data[adapter_key]
        if model_id and model_id in adapter_block:
            return adapter_block[model_id]
        if _DEFAULT_ADAPTER_KEY in adapter_block:
            return adapter_block[_DEFAULT_ADAPTER_KEY]
    return data[_DEFAULT_ADAPTER_KEY]


def compute_token_estimate(drivers: dict[str, Any], coefficients: CoefficientSet) -> int:
    """Evaluate Ê = T·(a·r + b·m) + (g/2)·T(T−1) + p·T + k·τ."""
    r = _driver_int(drivers, "files_to_read")
    m = _driver_int(drivers, "files_to_modify")
    t = _driver_int(drivers, "expected_turns")
    tau = 1 if drivers.get("needs_test_run") else 0
    a = coefficients["a"]
    b = coefficients["b"]
    g = coefficients["g"]
    p = coefficients["p"]
    k = coefficients["k"]
    c0 = a * r + b * m
    estimate = t * c0 + (g / 2.0) * t * (t - 1) + p * t + k * tau
    return max(1, int(round(estimate)))


def _driver_int(drivers: dict[str, Any], key: str) -> int:
    value = drivers.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"driver '{key}' must be an integer")
    return max(0, value)


def estimate_disagreement(token_estimate: int, shadow_token_estimate: int) -> float:
    if token_estimate <= 0:
        raise ValueError("token_estimate must be positive")
    return abs(token_estimate - shadow_token_estimate) / token_estimate


def estimate_from_drivers(
    drivers: dict[str, Any],
    adapter_id: str | None,
    model_id: str | None,
) -> tuple[int, CoefficientSet]:
    """Resolve coefficients and compute the token estimate."""
    coefficients = resolve_coefficients(adapter_id, model_id)
    token_estimate = compute_token_estimate(drivers, coefficients)
    return token_estimate, coefficients


def _demo_self_check() -> None:
    """Pin a known driver set to a known arithmetic result to catch regressions."""
    drivers = {
        "files_to_read": 2,
        "files_to_modify": 1,
        "expected_turns": 3,
        "needs_test_run": True,
    }
    token_estimate, coefficients = estimate_from_drivers(drivers, None, None)
    assert token_estimate == 12345, f"expected 12345, got {token_estimate}"
    assert coefficients.provenance["p"] == "fitted(3)", "expected fitted provenance for p"
    assert coefficients.provenance["g"] == "seed", "expected seed provenance for g"
    disagreement = estimate_disagreement(token_estimate, 11000)
    assert abs(disagreement - 1345 / 12345) < 1e-9, f"disagreement mismatch: {disagreement}"


if __name__ == "__main__":
    _demo_self_check()
    print("estimation_coefficients self-check passed")
