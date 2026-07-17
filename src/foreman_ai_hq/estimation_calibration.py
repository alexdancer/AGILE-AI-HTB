from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent / "defaults" / "estimation_calibration.yaml"
LOCAL_CATALOG_PATH = Path(".foreman") / "estimation_calibration.yaml"
DEFAULT_MAX_CASES = 3
DEFAULT_MAX_SUMMARY_CHARS = 2_000
_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "for",
    "in",
    "no",
    "of",
    "or",
    "the",
    "to",
    "with",
}


class CalibrationCatalogError(ValueError):
    """Raised when a strict calibration catalog is invalid."""


@dataclass(frozen=True)
class CalibrationCase:
    id: str
    task_description: str
    expected_tokens_min: int
    expected_tokens_max: int
    complexity: str
    task_kind: str
    recommended_model: str
    project_profile: dict[str, Any]
    rationale: str
    actual_tokens: int | None = None
    source: str = "manual"

    @property
    def expected_range(self) -> tuple[int, int]:
        return self.expected_tokens_min, self.expected_tokens_max

    def contains_estimate(self, estimate_tokens: int) -> bool:
        return self.expected_tokens_min <= estimate_tokens <= self.expected_tokens_max


@dataclass(frozen=True)
class CatalogLoadResult:
    cases: list[CalibrationCase] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def extend(self, other: "CatalogLoadResult") -> "CatalogLoadResult":
        return CatalogLoadResult(cases=[*self.cases, *other.cases], warnings=[*self.warnings, *other.warnings])


@dataclass(frozen=True)
class CalibrationSelection:
    cases: list[CalibrationCase]
    warnings: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass(frozen=True)
class EstimateBandCheck:
    case_id: str
    expected_tokens_min: int
    expected_tokens_max: int
    estimate_tokens: int
    within_band: bool


def load_default_catalog(*, strict: bool = True) -> CatalogLoadResult:
    return load_catalog(DEFAULT_CATALOG_PATH, strict=strict, source="default")


def load_local_catalog(project_root: str | Path | None) -> CatalogLoadResult:
    if not project_root:
        return CatalogLoadResult()
    path = Path(project_root).expanduser() / LOCAL_CATALOG_PATH
    if not path.exists():
        return CatalogLoadResult()
    return load_catalog(path, strict=False, source="local")


def load_calibration_sources(project_root: str | Path | None = None) -> CatalogLoadResult:
    """Load default calibration cases plus optional repo-local operator cases.

    The returned case shape is deliberately source-agnostic so future SQL-derived
    completed-task cases can be appended without changing estimator integration.
    """
    result = load_default_catalog(strict=True)
    return result.extend(load_local_catalog(project_root))


def load_catalog(path: str | Path, *, strict: bool, source: str = "manual") -> CatalogLoadResult:
    catalog_path = Path(path)
    if not catalog_path.exists():
        if strict:
            raise CalibrationCatalogError(f"calibration catalog not found: {catalog_path}")
        return CatalogLoadResult()
    try:
        raw = yaml.safe_load(catalog_path.read_text())
    except yaml.YAMLError as exc:
        message = f"invalid YAML in calibration catalog {catalog_path}: {exc}"
        if strict:
            raise CalibrationCatalogError(message) from exc
        return CatalogLoadResult(warnings=[f"invalid YAML in calibration catalog {catalog_path}"])
    cases_raw = raw.get("cases") if isinstance(raw, dict) else None
    if not isinstance(cases_raw, list):
        message = f"calibration catalog {catalog_path} must contain a cases list"
        if strict:
            raise CalibrationCatalogError(message)
        return CatalogLoadResult(warnings=[_sanitize_warning(message)])

    cases: list[CalibrationCase] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(cases_raw, start=1):
        try:
            case = _parse_case(item, catalog_path=catalog_path, index=index, source=source)
            if case.id in seen_ids:
                raise CalibrationCatalogError(f"duplicate calibration case id: {case.id}")
            seen_ids.add(case.id)
            cases.append(case)
        except CalibrationCatalogError as exc:
            if strict:
                raise
            warnings.append(_sanitize_warning(str(exc)))
    return CatalogLoadResult(cases=cases, warnings=warnings)


def select_relevant_cases(
    cases: Iterable[CalibrationCase],
    *,
    task_description: str,
    project_profile: dict[str, Any] | None = None,
    task_kind: str | None = None,
    complexity: str | None = None,
    recommended_model: str | None = None,
    limit: int = DEFAULT_MAX_CASES,
) -> list[CalibrationCase]:
    if limit <= 0:
        return []
    task_tokens = _tokens(task_description)
    ranked: list[tuple[tuple[int, int, str, int], CalibrationCase]] = []
    for case in cases:
        if not _matches_requested_fields(
            case,
            project_profile=project_profile,
            task_kind=task_kind,
            complexity=complexity,
            recommended_model=recommended_model,
        ):
            continue
        lexical_overlap = len(task_tokens & _tokens(case.task_description))
        structured_score = _structured_score(
            case,
            project_profile=project_profile,
            task_kind=task_kind,
            complexity=complexity,
            recommended_model=recommended_model,
        )
        if lexical_overlap == 0 and not any((task_kind, complexity, recommended_model)):
            continue
        if lexical_overlap == 0 and structured_score < 2:
            continue
        ranked.append(((-structured_score, -lexical_overlap, case.id, case.expected_tokens_min), case))
    ranked.sort(key=lambda item: item[0])
    return [case for _, case in ranked[:limit]]


def render_calibration_summary(
    cases: Iterable[CalibrationCase],
    *,
    max_chars: int = DEFAULT_MAX_SUMMARY_CHARS,
) -> str:
    selected = list(cases)
    if not selected or max_chars <= 0:
        return ""
    lines = ["Calibration examples (Worker tokens; read-only, no multiply or clamp):"]
    for case in selected:
        actual = f", actual={case.actual_tokens}" if case.actual_tokens is not None else ""
        profile = _profile_label(case.project_profile)
        lines.append(
            f"- {case.id}: expected={case.expected_tokens_min}-{case.expected_tokens_max}{actual}, "
            f"{case.task_kind}/{case.complexity}, "
            f"profile={profile}. Rationale: {_one_line(case.rationale)}"
        )
    summary = "\n".join(lines).strip()
    if len(summary) <= max_chars:
        return summary
    return summary[: max(0, max_chars - 1)].rstrip() + "…"


def check_estimate_band(case: CalibrationCase, estimate_tokens: int) -> EstimateBandCheck:
    if isinstance(estimate_tokens, bool) or not isinstance(estimate_tokens, int):
        raise AssertionError(f"case {case.id}: estimate_tokens must be an integer, got {estimate_tokens!r}")
    check = EstimateBandCheck(
        case_id=case.id,
        expected_tokens_min=case.expected_tokens_min,
        expected_tokens_max=case.expected_tokens_max,
        estimate_tokens=estimate_tokens,
        within_band=case.contains_estimate(estimate_tokens),
    )
    if not check.within_band:
        raise AssertionError(
            f"case {case.id}: estimate {estimate_tokens} outside expected Worker-token band "
            f"{case.expected_tokens_min}-{case.expected_tokens_max}; task={case.task_description[:120]!r}"
        )
    return check


def build_calibration_selection(
    *,
    task_description: str,
    project_root: str | Path | None = None,
    project_profile: dict[str, Any] | None = None,
    task_kind: str | None = None,
    complexity: str | None = None,
    recommended_model: str | None = None,
    limit: int = DEFAULT_MAX_CASES,
    max_summary_chars: int = DEFAULT_MAX_SUMMARY_CHARS,
) -> CalibrationSelection:
    loaded = load_calibration_sources(project_root)
    selected = select_relevant_cases(
        loaded.cases,
        task_description=task_description,
        project_profile=project_profile,
        task_kind=task_kind,
        complexity=complexity,
        recommended_model=recommended_model,
        limit=limit,
    )
    return CalibrationSelection(
        cases=selected,
        warnings=loaded.warnings,
        summary=render_calibration_summary(selected, max_chars=max_summary_chars),
    )


def _parse_case(raw: Any, *, catalog_path: Path, index: int, source: str) -> CalibrationCase:
    if not isinstance(raw, dict):
        raise CalibrationCatalogError(f"{catalog_path} case #{index} must be an object")
    case_id = _required_str(raw, "id", catalog_path, index)
    task_description = _required_str(raw, "task_description", catalog_path, index)
    complexity = _required_str(raw, "complexity", catalog_path, index).lower()
    if complexity not in {"simple", "modest", "complex"}:
        raise CalibrationCatalogError(f"{catalog_path} case {case_id} complexity must be simple, modest, or complex")
    task_kind = _required_str(raw, "task_kind", catalog_path, index)
    recommended_model = _required_str(raw, "recommended_model", catalog_path, index)
    rationale = _required_str(raw, "rationale", catalog_path, index)
    project_profile = raw.get("project_profile")
    if not isinstance(project_profile, dict):
        raise CalibrationCatalogError(f"{catalog_path} case {case_id} project_profile must be an object")
    expected_min = _required_positive_int(raw, "expected_tokens_min", catalog_path, case_id)
    expected_max = _required_positive_int(raw, "expected_tokens_max", catalog_path, case_id)
    if expected_min > expected_max:
        raise CalibrationCatalogError(f"{catalog_path} case {case_id} expected_tokens_min must be <= expected_tokens_max")
    actual_tokens = raw.get("actual_tokens")
    if actual_tokens is not None:
        actual_tokens = _positive_int(actual_tokens, f"{catalog_path} case {case_id} actual_tokens")
    return CalibrationCase(
        id=case_id,
        task_description=task_description,
        expected_tokens_min=expected_min,
        expected_tokens_max=expected_max,
        complexity=complexity,
        task_kind=task_kind,
        recommended_model=recommended_model,
        project_profile=dict(project_profile),
        rationale=rationale,
        actual_tokens=actual_tokens,
        source=source,
    )


def _required_str(raw: dict[str, Any], key: str, catalog_path: Path, index: int) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        case_label = raw.get("id") if isinstance(raw.get("id"), str) else f"#{index}"
        raise CalibrationCatalogError(f"{catalog_path} case {case_label} missing non-empty {key}")
    return value.strip()


def _required_positive_int(raw: dict[str, Any], key: str, catalog_path: Path, case_id: str) -> int:
    if key not in raw:
        raise CalibrationCatalogError(f"{catalog_path} case {case_id} missing {key}")
    return _positive_int(raw[key], f"{catalog_path} case {case_id} {key}")


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise CalibrationCatalogError(f"{label} must be a positive integer")
    return value


def _matches_requested_fields(
    case: CalibrationCase,
    *,
    project_profile: dict[str, Any] | None,
    task_kind: str | None,
    complexity: str | None,
    recommended_model: str | None,
) -> bool:
    if task_kind and case.task_kind != task_kind:
        return False
    if complexity and case.complexity != complexity:
        return False
    if recommended_model and case.recommended_model != recommended_model:
        return False
    if project_profile and case.project_profile:
        shared_keys = set(project_profile).intersection(case.project_profile)
        if shared_keys and not all(str(project_profile[key]) == str(case.project_profile[key]) for key in shared_keys):
            return False
    return True


def _structured_score(
    case: CalibrationCase,
    *,
    project_profile: dict[str, Any] | None,
    task_kind: str | None,
    complexity: str | None,
    recommended_model: str | None,
) -> int:
    score = 0
    if task_kind and case.task_kind == task_kind:
        score += 3
    if complexity and case.complexity == complexity:
        score += 2
    if recommended_model and case.recommended_model == recommended_model:
        score += 2
    if project_profile:
        for key, value in project_profile.items():
            if key in case.project_profile and str(case.project_profile[key]) == str(value):
                score += 1
    return score


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", text.lower())
        if len(token) > 2 and token not in _STOPWORDS
    }


def _profile_label(profile: dict[str, Any]) -> str:
    if not profile:
        return "global"
    preferred = ["name", "language", "framework", "test_command"]
    parts = [f"{key}={profile[key]}" for key in preferred if key in profile]
    if not parts:
        parts = [f"{key}={profile[key]}" for key in sorted(profile)[:3]]
    return ", ".join(_one_line(str(part)) for part in parts)


def _one_line(value: str) -> str:
    return " ".join(str(value).split())


def _sanitize_warning(message: str) -> str:
    sanitized = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", message)
    sanitized = re.sub(r"sk_[A-Za-z0-9_-]+", "[REDACTED]", sanitized)
    sanitized = re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(
        r"(?i)\b(password|passwd|pwd|api[_-]?key|secret|token)\s*[:=]\s*[^\s,;]+",
        lambda match: f"{match.group(1)}=[REDACTED]",
        sanitized,
    )
    return sanitized
