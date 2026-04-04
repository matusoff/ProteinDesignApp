from __future__ import annotations

from typing import Any

from config import RESULT_SCHEMA_VERSION


def make_result(
    *,
    sequence_name: str,
    sequence: str,
    goal: str,
    protected_positions: list[int],
    global_features: dict[str, Any],
    risk_regions: list[dict[str, Any]],
    liabilities: list[dict[str, Any]],
    scores: dict[str, Any],
    mutation_suggestions: list[dict[str, Any]],
    report_text: str,
    region_analyses: list[dict[str, Any]] | None = None,
    mutation_impacts: list[dict[str, Any]] | None = None,
    decision_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Canonical analysis result object.

    Kept as a plain dict (instead of a dataclass) so it's easy to:
    - export to JSON later
    - store in Gradio state
    - diff/compare runs
    """

    return {
        "version": RESULT_SCHEMA_VERSION,
        "sequence_name": sequence_name,
        "sequence": sequence,
        "goal": goal,
        "protected_positions": protected_positions,
        "global_features": global_features,
        "risk_regions": risk_regions,
        "liabilities": liabilities,
        "scores": scores,
        "mutation_suggestions": mutation_suggestions,
        "region_analyses": region_analyses or [],
        "mutation_impacts": mutation_impacts or [],
        "decision_summary": decision_summary or {},
        "report_text": report_text,
    }

