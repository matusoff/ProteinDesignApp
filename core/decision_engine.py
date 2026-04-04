from __future__ import annotations

from typing import Any


def rank_region_analyses(region_analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    severity_rank = {"high": 2, "medium": 1, "low": 0}
    confidence_rank = {"high": 2, "medium": 1, "low": 0}

    def score_tuple(x: dict[str, Any]) -> tuple[float, float, float, float, float]:
        ev = x.get("evidence") or {}
        length = float(x.get("end", 0) - x.get("start", 0) + 1)
        hydro_density = float(ev.get("mean_hydrophobicity", 0.0)) * float(ev.get("hydrophobic_fraction", 0.0))
        return (
            float(severity_rank.get(str(x.get("severity")), 0)),
            float(confidence_rank.get(str(x.get("confidence")), 0)),
            length,
            float(ev.get("mean_hydrophobicity", 0.0)),
            hydro_density,
        )

    return sorted(region_analyses, key=score_tuple, reverse=True)


def build_decision_summary(
    region_analyses: list[dict[str, Any]],
    mutation_impacts: list[dict[str, Any]],
) -> dict[str, Any]:
    ranked_regions = rank_region_analyses(region_analyses)
    dominant = ranked_regions[0] if ranked_regions else None

    if not dominant:
        return {
            "dominant_region": None,
            "top_drivers": [],
            "primary_recommendation": "No dominant region identified.",
            "safer_option": None,
            "stronger_option": None,
            "interpretation": "No major decision-driving hotspot detected.",
        }

    top_drivers: list[dict[str, Any]] = []
    for i, r in enumerate(ranked_regions[:3], start=1):
        ev = r.get("evidence") or {}
        top_drivers.append(
            {
                "rank": i,
                "start": r["start"],
                "end": r["end"],
                "dominant_issue": r["dominant_issue"],
                "severity": r["severity"],
                "confidence": r["confidence"],
                "mean_hydrophobicity": ev.get("mean_hydrophobicity"),
                "risk_type": (r.get("source_flags") or [{}])[0].get("risk_type"),
            }
        )

    def _overlaps(a0: int, a1: int, b0: int, b1: int) -> bool:
        return not (a1 < b0 or b1 < a0)

    region_mutations = [
        x
        for x in mutation_impacts
        if _overlaps(
            int(x.get("region_start", 0)),
            int(x.get("region_end", 0)),
            int(dominant["start"]),
            int(dominant["end"]),
        )
    ]

    if not region_mutations and mutation_impacts:
        region_mutations = list(mutation_impacts)

    safer = next((x for x in region_mutations if x.get("option_type") == "safer"), None)
    stronger = next((x for x in region_mutations if x.get("option_type") == "stronger"), None)

    if safer is None and region_mutations:
        safer = sorted(region_mutations, key=lambda x: (x["disruption_risk"], -x["benefit_score"]))[0]
    if stronger is None and region_mutations:
        stronger = sorted(region_mutations, key=lambda x: (-x["benefit_score"], x["disruption_risk"]))[0]

    if safer and stronger and safer.get("mutation") == stronger.get("mutation"):
        if len(region_mutations) > 1:
            stronger = sorted(
                [x for x in region_mutations if x.get("mutation") != safer.get("mutation")],
                key=lambda x: (-x["benefit_score"], x["disruption_risk"]),
            )[0]
        else:
            stronger = None

    interpretation = (
        f"Dominant concern is region {dominant['start']}-{dominant['end']} "
        f"({dominant['dominant_issue']}) driven by {dominant['reason_summary']}."
    )

    return {
        "dominant_region": dominant,
        "top_drivers": top_drivers,
        "primary_recommendation": dominant.get("design_strategy", ""),
        "safer_option": safer["mutation"] if safer else None,
        "stronger_option": stronger["mutation"] if stronger else None,
        "interpretation": interpretation,
    }
