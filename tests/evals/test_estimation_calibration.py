from pathlib import Path

import pytest

from foreman_ai_hq.estimation_calibration import (
    CalibrationCase,
    CalibrationCatalogError,
    build_calibration_selection,
    check_estimate_band,
    load_calibration_sources,
    load_catalog,
    load_default_catalog,
    load_local_catalog,
    render_calibration_summary,
    select_relevant_cases,
)


def _case(case_id: str, description: str, **overrides):
    data = {
        "id": case_id,
        "task_description": description,
        "expected_tokens_min": 1_000,
        "expected_tokens_max": 2_000,
        "complexity": "modest",
        "task_kind": "implementation",
        "recommended_model": "claude-sonnet-4-6",
        "project_profile": {"name": "DEMO_REPO_2099", "language": "python"},
        "rationale": "Synthetic DEMO_2099 calibration rationale.",
    }
    data.update(overrides)
    return CalibrationCase(**data)


def _write_catalog(path: Path, cases: str):
    path.write_text(f"cases:\n{cases}")


def test_strict_catalog_loads_valid_case_with_optional_actual_tokens(tmp_path):
    path = tmp_path / "calibration.yaml"
    _write_catalog(
        path,
        """
  - id: DEMO-CAL-2099-999-010
    task_description: Add DEMO_2099 route tests.
    project_profile:
      name: DEMO_REPO_2099
      language: python
    task_kind: implementation
    complexity: modest
    recommended_model: claude-sonnet-4-6
    expected_tokens_min: 5000
    expected_tokens_max: 12000
    actual_tokens: 9100
    rationale: Route plus tests in a synthetic repo.
""",
    )

    result = load_catalog(path, strict=True, source="test")

    assert len(result.cases) == 1
    case = result.cases[0]
    assert case.id == "DEMO-CAL-2099-999-010"
    assert case.expected_range == (5_000, 12_000)
    assert case.actual_tokens == 9_100
    assert case.contains_estimate(8_000)
    assert not result.warnings


@pytest.mark.parametrize(
    "case_yaml, expected_message",
    [
        (
            """
  - task_description: Missing ID.
    project_profile: {}
    task_kind: implementation
    complexity: modest
    recommended_model: claude-sonnet-4-6
    expected_tokens_min: 5000
    expected_tokens_max: 12000
    rationale: Missing required ID.
""",
            "missing non-empty id",
        ),
        (
            """
  - id: DEMO-CAL-2099-999-011
    task_description: Invalid range.
    project_profile: {}
    task_kind: implementation
    complexity: modest
    recommended_model: claude-sonnet-4-6
    expected_tokens_min: 12000
    expected_tokens_max: 5000
    rationale: Invalid range.
""",
            "expected_tokens_min must be <= expected_tokens_max",
        ),
        (
            """
  - id: DEMO-CAL-2099-999-012
    task_description: Bad profile.
    project_profile: not-a-dict
    task_kind: implementation
    complexity: modest
    recommended_model: claude-sonnet-4-6
    expected_tokens_min: 5000
    expected_tokens_max: 12000
    rationale: Invalid profile.
""",
            "project_profile must be an object",
        ),
    ],
)
def test_strict_catalog_reports_schema_errors(tmp_path, case_yaml, expected_message):
    path = tmp_path / "calibration.yaml"
    _write_catalog(path, case_yaml)

    with pytest.raises(CalibrationCatalogError, match=expected_message):
        load_catalog(path, strict=True)


def test_strict_catalog_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "calibration.yaml"
    _write_catalog(
        path,
        """
  - id: DEMO-CAL-2099-999-013
    task_description: First case.
    project_profile: {}
    task_kind: implementation
    complexity: simple
    recommended_model: claude-haiku-4-5
    expected_tokens_min: 1000
    expected_tokens_max: 2000
    rationale: First.
  - id: DEMO-CAL-2099-999-013
    task_description: Duplicate case.
    project_profile: {}
    task_kind: implementation
    complexity: simple
    recommended_model: claude-haiku-4-5
    expected_tokens_min: 1000
    expected_tokens_max: 2000
    rationale: Duplicate.
""",
    )

    with pytest.raises(CalibrationCatalogError, match="duplicate calibration case id"):
        load_catalog(path, strict=True)


def test_lenient_local_catalog_ignores_malformed_cases_and_keeps_valid(tmp_path):
    root = tmp_path / "repo"
    catalog_dir = root / ".foreman"
    catalog_dir.mkdir(parents=True)
    catalog = catalog_dir / "estimation_calibration.yaml"
    _write_catalog(
        catalog,
        """
  - id: DEMO-CAL-2099-999-014
    task_description: Valid DEMO_2099 local case.
    project_profile:
      name: DEMO_REPO_2099
    task_kind: implementation
    complexity: modest
    recommended_model: claude-sonnet-4-6
    expected_tokens_min: 5000
    expected_tokens_max: 12000
    rationale: Valid local case.
  - id: DEMO-CAL-2099-999-015
    task_description: Bad secret-like local case.
    project_profile: bad-profile
    task_kind: implementation
    complexity: modest
    recommended_model: claude-sonnet-4-6
    expected_tokens_min: 5000
    expected_tokens_max: 12000
    rationale: Bearer abcdefghijklmnop
""",
    )

    result = load_local_catalog(root)

    assert [case.id for case in result.cases] == ["DEMO-CAL-2099-999-014"]
    assert len(result.warnings) == 1
    assert "project_profile must be an object" in result.warnings[0]
    assert "Bearer abcdefghijklmnop" not in result.warnings[0]


def test_lenient_local_catalog_malformed_yaml_warning_does_not_leak_source_text(tmp_path):
    root = tmp_path / "repo"
    catalog_dir = root / ".foreman"
    catalog_dir.mkdir(parents=True)
    catalog = catalog_dir / "estimation_calibration.yaml"
    catalog.write_text(
        "cases:\n"
        "  - id: DEMO-CAL-2099-999-SECRET\n"
        "    rationale: api_key=demo-secret\n"
        "    bad: [unterminated\n",
        encoding="utf-8",
    )

    result = load_local_catalog(root)

    assert not result.cases
    assert len(result.warnings) == 1
    assert "invalid YAML in calibration catalog" in result.warnings[0]
    assert "api_key" not in result.warnings[0]
    assert "demo-secret" not in result.warnings[0]
    assert "unterminated" not in result.warnings[0]


def test_default_and_local_sources_are_combined(tmp_path):
    root = tmp_path / "repo"
    catalog_dir = root / ".foreman"
    catalog_dir.mkdir(parents=True)
    _write_catalog(
        catalog_dir / "estimation_calibration.yaml",
        """
  - id: DEMO-CAL-2099-999-016
    task_description: Valid DEMO_2099 local case.
    project_profile:
      name: DEMO_REPO_2099
    task_kind: implementation
    complexity: simple
    recommended_model: claude-haiku-4-5
    expected_tokens_min: 1000
    expected_tokens_max: 3000
    rationale: Local case.
""",
    )

    result = load_calibration_sources(root)

    assert any(case.id == "DEMO-CAL-2099-999-001" for case in result.cases)
    assert any(case.id == "DEMO-CAL-2099-999-016" for case in result.cases)


def test_checked_in_default_catalog_is_valid_and_demo_safe():
    result = load_default_catalog(strict=True)

    assert result.cases
    assert not result.warnings
    for case in result.cases:
        text = f"{case.id} {case.task_description} {case.rationale} {case.project_profile}"
        assert "DEMO" in text
        assert "2099" in text
        assert ".invalid" not in text or "DEMO" in text


def test_selection_uses_structured_filters_lexical_overlap_and_stable_tie_breaking():
    cases = [
        _case("DEMO-CAL-2099-999-B", "Update unrelated billing docs", expected_tokens_min=3_000, expected_tokens_max=5_000),
        _case("DEMO-CAL-2099-999-A", "Add board archive filter route tests", expected_tokens_min=1_500, expected_tokens_max=2_500),
        _case("DEMO-CAL-2099-999-C", "Add board archive filter route tests", expected_tokens_min=1_000, expected_tokens_max=2_000),
        _case(
            "DEMO-CAL-2099-999-D",
            "Add board archive filter route tests",
            complexity="complex",
            recommended_model="claude-opus-4-8",
        ),
    ]

    selected = select_relevant_cases(
        cases,
        task_description="Add board archive filter tests",
        project_profile={"name": "DEMO_REPO_2099", "language": "python"},
        complexity="modest",
        recommended_model="claude-sonnet-4-6",
        limit=2,
    )

    assert [case.id for case in selected] == ["DEMO-CAL-2099-999-A", "DEMO-CAL-2099-999-C"]


def test_selection_rejects_conflicting_project_profile():
    cases = [
        _case("DEMO-CAL-2099-999-A", "Add board archive filter route tests"),
        _case(
            "DEMO-CAL-2099-999-B",
            "Add board archive filter route tests",
            project_profile={"name": "OTHER_DEMO_REPO_2099"},
        ),
    ]

    selected = select_relevant_cases(
        cases,
        task_description="Add board archive filter tests",
        project_profile={"name": "DEMO_REPO_2099"},
    )

    assert [case.id for case in selected] == ["DEMO-CAL-2099-999-A"]


def test_selection_rejects_profile_when_specific_key_conflicts_even_if_generic_key_matches():
    cases = [
        _case("DEMO-CAL-2099-999-A", "Add board archive filter route tests"),
        _case(
            "DEMO-CAL-2099-999-B",
            "Add board archive filter route tests",
            project_profile={"name": "OTHER_DEMO_REPO_2099", "test_command": "pytest"},
        ),
    ]

    selected = select_relevant_cases(
        cases,
        task_description="Add board archive filter tests",
        project_profile={"name": "DEMO_REPO_2099", "test_command": "pytest"},
    )

    assert [case.id for case in selected] == ["DEMO-CAL-2099-999-A"]


def test_summary_contains_ranges_actuals_and_is_capped():
    cases = [
        _case(
            "DEMO-CAL-2099-999-A",
            "Add board archive filter route tests",
            expected_tokens_min=5_000,
            expected_tokens_max=12_000,
            actual_tokens=9_100,
            rationale="This rationale is intentionally long enough to require truncation in a small summary cap.",
        )
    ]

    summary = render_calibration_summary(cases, max_chars=170)

    assert "DEMO-CAL-2099-999-A" in summary
    assert "expected=5000-12000" in summary
    assert "actual=9100" in summary
    assert len(summary) <= 170
    assert "multiply or clamp" in render_calibration_summary(cases)


def test_build_calibration_selection_preserves_sql_ready_candidate_shape(tmp_path):
    selection = build_calibration_selection(
        task_description="Implement DEMO_WORKER_2099 token evidence parsing",
        project_root=tmp_path,
        project_profile={"name": "DEMO_REPO_2099_TOKEN_TRACKER"},
        limit=1,
    )

    assert selection.cases
    assert selection.summary
    assert hasattr(selection.cases[0], "actual_tokens")


def test_catalog_backed_estimate_band_eval_records_case_and_estimate():
    case = _case(
        "DEMO-CAL-2099-999-EVAL",
        "Add DEMO_2099 estimator catalog eval coverage",
        expected_tokens_min=8_000,
        expected_tokens_max=16_000,
    )

    check = check_estimate_band(case, 12_000)

    assert check.case_id == "DEMO-CAL-2099-999-EVAL"
    assert check.expected_tokens_min == 8_000
    assert check.expected_tokens_max == 16_000
    assert check.estimate_tokens == 12_000
    assert check.within_band is True


def test_catalog_backed_estimate_band_eval_failure_is_actionable():
    case = _case(
        "DEMO-CAL-2099-999-EVAL",
        "Add DEMO_2099 estimator catalog eval coverage",
        expected_tokens_min=8_000,
        expected_tokens_max=16_000,
    )

    with pytest.raises(AssertionError) as exc:
        check_estimate_band(case, 20_000)

    message = str(exc.value)
    assert "DEMO-CAL-2099-999-EVAL" in message
    assert "8000-16000" in message
    assert "20000" in message
    assert "Add DEMO_2099 estimator catalog eval coverage" in message
