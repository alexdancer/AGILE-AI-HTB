from foreman_ai_hq.board_workspace import board_counts
from foreman_ai_hq.evidence_reporting import safe_evidence, token_totals
from foreman_ai_hq.worker_setup_view import active_adapter_for_request, worker_setup_next_action


def test_extracted_portal_helpers_keep_board_worker_and_evidence_contracts():
    assert board_counts([
        {"status": "Ready"},
        {"status": "Review"},
        {"status": "weird"},
    ]) == {"Estimated": 1, "Running": 0, "Review": 1, "Done": 0, "Blocked": 1}

    adapters = [
        {"id": "first", "configured": False},
        {"id": "default", "is_default": True, "configured": True},
    ]
    selected = active_adapter_for_request(adapters, None)
    requested = active_adapter_for_request(adapters, "first")
    assert selected is not None and selected["id"] == "default"
    assert requested is not None and requested["id"] == "first"

    action = worker_setup_next_action({"id": "w1", "configured": True, "discovered_models": [], "supported_models": []}, True)
    assert action["label"] == "Discover models"

    safe = safe_evidence({"api_key": "sk-test", "prompt_tokens": 10, "message": "Bearer abc123"})
    assert safe == {"prompt_tokens": 10, "message": "***REDACTED***"}

    assert token_totals({"token_log": [{"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}]}) == {
        "prompt_tokens": 2,
        "completion_tokens": 3,
        "total_tokens": 5,
    }
