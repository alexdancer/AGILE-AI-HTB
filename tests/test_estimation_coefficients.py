from foreman_ai_hq.estimation_coefficients import (
    compute_token_estimate,
    estimate_disagreement,
    estimate_from_drivers,
    resolve_coefficients,
)


def test_default_coefficients_resolve_from_missing_adapter_and_model():
    coefficients = resolve_coefficients("unknown-adapter", "unknown/model")

    assert coefficients["a"] == 900
    assert coefficients.provenance["g"] == "seed"
    assert coefficients.provenance["p"] == "fitted(3)"


def test_adapter_default_falls_back_from_missing_model():
    coefficients = resolve_coefficients("opencode", "unknown/model")

    assert coefficients["a"] == 900
    assert coefficients.provenance["p"] == "fitted(3)"


def test_exact_adapter_model_block_resolves():
    coefficients = resolve_coefficients("opencode", "opencode/gpt-5.1")

    assert coefficients["a"] == 500
    assert coefficients["b"] == 200
    assert coefficients.provenance["p"] == "fitted(2)"


def test_arithmetic_on_fixed_driver_set():
    drivers = {
        "files_to_read": 2,
        "files_to_modify": 1,
        "expected_turns": 3,
        "needs_test_run": True,
    }
    token_estimate = compute_token_estimate(drivers, resolve_coefficients(None, None))

    assert token_estimate == 12345


def test_estimate_grows_quadratically_in_expected_turns():
    base = {"files_to_read": 2, "files_to_modify": 1, "needs_test_run": False}
    low = compute_token_estimate({**base, "expected_turns": 2}, resolve_coefficients(None, None))
    high = compute_token_estimate({**base, "expected_turns": 4}, resolve_coefficients(None, None))

    assert high > 2 * low


def test_test_run_overhead_adds_constant_k():
    base = {"files_to_read": 1, "files_to_modify": 0, "expected_turns": 1}
    without = compute_token_estimate({**base, "needs_test_run": False}, resolve_coefficients(None, None))
    with_test = compute_token_estimate({**base, "needs_test_run": True}, resolve_coefficients(None, None))

    assert with_test - without == 3000


def test_disagreement_computation():
    d = estimate_disagreement(10_000, 12_000)

    assert d == 0.2


def test_estimate_from_drivers_returns_provenance():
    drivers = {
        "files_to_read": 2,
        "files_to_modify": 1,
        "expected_turns": 3,
        "needs_test_run": True,
    }
    token_estimate, coefficients = estimate_from_drivers(drivers, "opencode", "opencode/gpt-5.1")

    assert token_estimate == 7745
    assert coefficients.provenance["a"] == "seed"
    assert coefficients.provenance["p"] == "fitted(2)"
