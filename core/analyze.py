from __future__ import annotations

from typing import Any

from core.features import summarize_global_features
from core.liabilities import find_sequence_liabilities
from core.mutations import generate_mutation_suggestions
from core.parser import extract_sequence, validate_sequence
from core.protected_regions import parse_protected_regions
from core.report import generate_text_report
from core.scanner import identify_risk_regions
from core.scoring import build_score_summary
from core.results import make_result


def analyze_sequence(
    *,
    sequence_text: str,
    sequence_name: str,
    goal: str,
    protected_text: str,
) -> tuple[dict[str, Any] | None, str | None]:
    seq = extract_sequence(sequence_text)
    is_valid, errors = validate_sequence(seq)
    if not is_valid:
        error_md = "### Input error\n\n" + "\n".join([f"- {e}" for e in errors])
        return None, error_md

    protected_positions = sorted(parse_protected_regions(protected_text))

    global_features = summarize_global_features(seq)
    risk_regions = identify_risk_regions(seq)
    liabilities = find_sequence_liabilities(seq)
    scores = build_score_summary(global_features, risk_regions, liabilities)
    mutation_impacts, mutation_suggestions, region_analyses, decision_summary = generate_mutation_suggestions(
        seq, risk_regions, liabilities, set(protected_positions)
    )

    result = make_result(
        sequence_name=sequence_name or "input sequence",
        sequence=seq,
        goal=goal,
        protected_positions=protected_positions,
        global_features=global_features,
        risk_regions=risk_regions,
        liabilities=liabilities,
        scores=scores,
        mutation_suggestions=mutation_suggestions,
        mutation_impacts=mutation_impacts,
        region_analyses=region_analyses,
        decision_summary=decision_summary,
        report_text="",
    )
    result["report_text"] = generate_text_report(result)

    return result, None

