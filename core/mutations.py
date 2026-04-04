from __future__ import annotations

from config import TOP_N_SUGGESTIONS
from core.decision_engine import build_decision_summary
from core.mutation_impact import evaluate_mutation_for_region
from core.region_analysis import analyze_regions

# Conservative vs aggressive patch-breaking candidates (per WT residue)
PATCH_OPTIONS: dict[str, list[str]] = {
    "F": ["Y", "S"],
    "W": ["Y", "F"],
    "Y": ["F", "S"],
    "L": ["V", "Q", "E"],
    "I": ["V", "Q", "E"],
    "V": ["T", "Q", "E"],
    "M": ["L", "Q"],
    "A": ["S", "T"],
}


def _synthetic_window_region(seq: str, position: int, half: int = 4) -> dict:
    start = max(1, position - half)
    end = min(len(seq), position + half)
    return {
        "start": start,
        "end": end,
        "sequence": seq[start - 1 : end],
        "dominant_issue": "site_specific_mitigation",
        "severity": "medium",
        "confidence": "low",
        "reason_summary": "Site-targeted substitution (liability or local mitigation).",
        "design_strategy": "Evaluate structural context; prefer conservative changes if structure-sensitive.",
        "source_flags": [{}],
    }


def generate_region_candidate_mutations(
    seq: str,
    region_analysis: dict,
    protected_positions: set[int],
) -> list[tuple[int, str]]:
    candidates: list[tuple[int, str]] = []
    start, end = region_analysis["start"], region_analysis["end"]

    for pos in range(start, end + 1):
        if pos in protected_positions:
            continue

        wt = seq[pos - 1]
        if wt not in PATCH_OPTIONS:
            continue

        for alt in PATCH_OPTIONS[wt]:
            if alt == wt:
                continue
            candidates.append((pos, alt))

    return candidates


def generate_ranked_region_suggestions(
    seq: str,
    region_analysis: dict,
    protected_positions: set[int],
) -> list[dict]:
    candidates = generate_region_candidate_mutations(seq, region_analysis, protected_positions)
    impacts: list[dict] = []

    for pos, alt in candidates:
        impacts.append(evaluate_mutation_for_region(seq, region_analysis, pos, alt))

    impacts = sorted(
        impacts,
        key=lambda x: (-x["benefit_score"], x["disruption_risk"], x["position"]),
    )
    return impacts


def select_safer_and_stronger_options(impacts: list[dict]) -> list[dict]:
    if not impacts:
        return []

    safer = sorted(impacts, key=lambda x: (x["disruption_risk"], -x["benefit_score"]))[:1]
    stronger = sorted(impacts, key=lambda x: (-x["benefit_score"], x["disruption_risk"]))[:1]

    chosen: list[dict] = []
    seen: set[str] = set()
    for item, tag in [(safer[0], "safer"), (stronger[0], "stronger")]:
        key = item["mutation"]
        if key not in seen:
            new_item = dict(item)
            new_item["option_type"] = tag
            chosen.append(new_item)
            seen.add(key)

    return chosen


def _evaluate_liability_mutation(
    seq: str,
    position: int,
    new_residue: str,
    category: str,
) -> dict:
    ra = _synthetic_window_region(seq, position)
    impact = evaluate_mutation_for_region(seq, ra, position, new_residue)
    impact["category"] = category
    impact["option_type"] = "mitigation"
    impact["rationale"] = (
        f"{impact['mutation']} ({category}): " + impact["rationale"]
    )
    return impact


def generate_mutation_suggestions(
    seq: str,
    risk_regions: list[dict],
    liabilities: list[dict],
    protected_positions: set[int],
) -> tuple[list[dict], list[dict], list[dict], dict]:
    """
    Returns (mutation_impacts_for_display, mutation_suggestions_flat, region_analyses, decision_summary).

    mutation_suggestions_flat: ranked list for export/table (includes option_type when present).
    """
    region_analyses = analyze_regions(risk_regions, liabilities)

    all_impacts: list[dict] = []
    for ra in region_analyses:
        if (ra.get("source_flags") or [{}])[0].get("risk_type") != "hydrophobic_cluster":
            continue
        impacts = generate_ranked_region_suggestions(seq, ra, protected_positions)
        chosen = select_safer_and_stronger_options(impacts)
        for c in chosen:
            c.setdefault("category", "patch_breaking")
            c["expected_effect"] = (
                "Reduce local hydrophobicity / disrupt aggregation-prone patch"
            )
        all_impacts.extend(chosen)

    # Oxidation M->L
    for item in liabilities:
        if item["liability_type"] != "oxidation_prone_residue":
            continue
        pos = item["position"]
        if pos in protected_positions:
            continue
        wt = seq[pos - 1]
        if wt == "M":
            all_impacts.append(
                _evaluate_liability_mutation(seq, pos, "L", "oxidation_mitigation")
            )

    # N-gly motif N->Q
    for item in liabilities:
        if item["liability_type"] != "N_glycosylation_motif":
            continue
        pos = item["position"]
        if pos in protected_positions:
            continue
        wt = seq[pos - 1]
        if wt == "N":
            all_impacts.append(
                _evaluate_liability_mutation(seq, pos, "Q", "motif_breaking")
            )

    # Rank all impacts by benefit, then cap
    def _dedupe_impacts(impacts: list[dict]) -> list[dict]:
        by_mut: dict[str, dict] = {}
        for x in impacts:
            m = str(x["mutation"])
            if m not in by_mut or x["benefit_score"] > by_mut[m]["benefit_score"]:
                by_mut[m] = x
        return list(by_mut.values())

    all_impacts = _dedupe_impacts(all_impacts)
    all_impacts = sorted(
        all_impacts,
        key=lambda x: (-x["benefit_score"], x["disruption_risk"], x["position"]),
    )

    for i, x in enumerate(all_impacts, start=1):
        x["rank"] = i

    flat = all_impacts[:TOP_N_SUGGESTIONS]

    decision_summary = build_decision_summary(region_analyses, all_impacts)

    return all_impacts, flat, region_analyses, decision_summary
