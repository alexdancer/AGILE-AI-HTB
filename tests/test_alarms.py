from token_tracker_harness.alarms import (
    alarm_for_checkpoint_failure,
    detect_budget_alarms,
    detect_loop,
    detect_session_timeout,
    detect_tool_category_bias,
)


def test_budget_zone_alarms_fire_once_per_session_zone_transition():
    previous = [{"type": "BUDGET_YELLOW", "session_id": "sess-1"}]

    yellow = detect_budget_alarms(
        session_id="sess-1",
        zone="yellow",
        daily_used_tokens=650_000,
        daily_cap_tokens=1_000_000,
        session_used_tokens=10_000,
        session_cap_tokens=200_000,
        previous_alarms=previous,
    )
    red = detect_budget_alarms(
        session_id="sess-1",
        zone="red",
        daily_used_tokens=900_000,
        daily_cap_tokens=1_000_000,
        session_used_tokens=10_000,
        session_cap_tokens=200_000,
        previous_alarms=previous,
    )

    assert yellow == []
    assert len(red) == 1
    assert red[0].type == "BUDGET_RED"
    assert red[0].severity == "MEDIUM"
    assert red[0].session_id == "sess-1"
    assert red[0].context["zone"] == "red"
    assert red[0].recommended_action
    assert red[0].timestamp


def test_budget_alarm_deduplication_is_per_session_only_and_context_has_remaining_budget():
    alarms = detect_budget_alarms(
        session_id="sess-new",
        zone="yellow",
        daily_used_tokens=650_000,
        daily_cap_tokens=1_000_000,
        session_used_tokens=10_000,
        session_cap_tokens=200_000,
        previous_alarms=[{"type": "BUDGET_YELLOW", "session_id": "sess-old"}],
    )

    assert [alarm.type for alarm in alarms] == ["BUDGET_YELLOW"]
    assert alarms[0].context["daily_remaining_tokens"] == 350_000
    assert alarms[0].context["daily_usage_ratio"] == 0.65


def test_daily_and_session_cap_alarms_fire_when_caps_crossed():
    alarms = detect_budget_alarms(
        session_id="sess-2",
        zone="red",
        daily_used_tokens=1_100_000,
        daily_cap_tokens=1_000_000,
        session_used_tokens=250_000,
        session_cap_tokens=200_000,
        previous_alarms=[],
    )

    by_type = {alarm.type: alarm for alarm in alarms}
    assert by_type["DAILY_CAP_EXCEEDED"].severity == "HIGH"
    assert by_type["DAILY_CAP_EXCEEDED"].context["daily_used_tokens"] == 1_100_000
    assert by_type["SESSION_CAP_EXCEEDED"].severity == "MEDIUM"
    assert by_type["SESSION_CAP_EXCEEDED"].context["session_used_tokens"] == 250_000


def test_loop_detection_requires_consecutive_same_tool_and_input_hash():
    no_loop = [
        {"tool_name": "read_file", "input_hash": "a"},
        {"tool_name": "read_file", "input_hash": "a"},
        {"tool_name": "terminal", "input_hash": "b"},
        {"tool_name": "read_file", "input_hash": "a"},
    ]
    loop = no_loop + [
        {"tool_name": "read_file", "input_hash": "a"},
        {"tool_name": "read_file", "input_hash": "a"},
        {"tool_name": "read_file", "input_hash": "a"},
        {"tool_name": "read_file", "input_hash": "a"},
    ]

    assert detect_loop(no_loop, threshold=5, session_id="sess-3") is None
    alarm = detect_loop(loop, threshold=5, session_id="sess-3")

    assert alarm.type == "LOOP_DETECTED"
    assert alarm.severity == "MEDIUM"
    assert alarm.context["tool_name"] == "read_file"
    assert alarm.context["input_hash"] == "a"
    assert alarm.context["repetition_count"] == 5


def test_loop_detection_supports_plan_signature_without_session_id():
    alarm = detect_loop(
        [
            {"tool_name": "read_file", "input_hash": "a"},
            {"tool_name": "read_file", "input_hash": "a"},
        ],
        threshold=2,
    )

    assert alarm.type == "LOOP_DETECTED"
    assert alarm.session_id == ""


def test_timeout_tool_bias_and_checkpoint_failure_alarms_have_expected_shape():
    timeout = detect_session_timeout("sess-4", elapsed_seconds=1900, timeout_seconds=1800)
    bias = detect_tool_category_bias("sess-4", category="web", category_token_share=0.75, limit=0.50)
    checkpoint = alarm_for_checkpoint_failure("sess-4", checkpoint_name="budget_health", reason="over budget")

    assert timeout.type == "SESSION_TIMEOUT"
    assert timeout.severity == "MEDIUM"
    assert timeout.context["elapsed_seconds"] == 1900
    assert bias.type == "TOOL_CATEGORY_BIAS"
    assert bias.severity == "LOW"
    assert bias.context["category"] == "web"
    assert checkpoint.type == "CHECKPOINT_FAIL"
    assert checkpoint.severity == "MEDIUM"
    assert checkpoint.context == {"checkpoint_name": "budget_health", "reason": "over budget"}


def test_timeout_and_bias_return_none_below_thresholds():
    assert detect_session_timeout("sess-5", elapsed_seconds=100, timeout_seconds=1800) is None
    assert detect_tool_category_bias("sess-5", category="file_io", category_token_share=0.25, limit=0.50) is None
