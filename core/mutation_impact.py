from __future__ import annotations

from typing import Any

from core.liabilities import find_sequence_liabilities
from utils.sequence_utils import (
    get_subsequence,
    local_aromatic_fraction,
    local_charged_fraction,
    local_flexibility_proxy,
    local_hydrophobic_fraction,
    local_mean_hydrophobicity,
    local_net_charge,
    mutate_sequence,
)


def compute_local_metrics(seq: str, start: int, end: int) -> dict[str, Any]:
    local_seq = get_subsequence(seq, start, end)
    return {
        "sequence": local_seq,
        "mean_hydrophobicity": round(local_mean_hydrophobicity(local_seq), 3),
        "hydrophobic_fraction": round(local_hydrophobic_fraction(local_seq), 3),
        "aromatic_fraction": round(local_aromatic_fraction(local_seq), 3),
        "local_net_charge": local_net_charge(local_seq),
        "charged_fraction": round(local_charged_fraction(local_seq), 3),
        "flexibility_proxy": round(local_flexibility_proxy(local_seq), 3),
    }


def compare_local_metrics(before: dict[str, Any], after: dict[str, Any]) -> dict[str, float]:
    deltas: dict[str, float] = {}
    for k in before:
        if k == "sequence":
            continue
        deltas[k] = round(float(after[k]) - float(before[k]), 3)
    return deltas


def collect_region_local_liabilities(seq: str, start: int, end: int) -> list[dict]:
    all_liabs = find_sequence_liabilities(seq)
    return [x for x in all_liabs if start <= x["position"] <= end]


def diff_liabilities(before: list[dict], after: list[dict]) -> tuple[list[dict], list[dict]]:
    def key(x: dict) -> tuple[Any, ...]:
        return (x["position"], x["liability_type"], x["motif_or_residue"])

    before_set = {key(x): x for x in before}
    after_set = {key(x): x for x in after}

    gained = [after_set[k] for k in after_set.keys() - before_set.keys()]
    lost = [before_set[k] for k in before_set.keys() - after_set.keys()]
    return gained, lost


def compute_benefit_score(
    region_analysis: dict[str, Any],
    deltas: dict[str, float],
    gained: list[dict],
    lost: list[dict],
    before_metrics: dict[str, Any],
    after_metrics: dict[str, Any],
) -> float:
    score = 0.0
    issue = region_analysis["dominant_issue"]

    if "aggregation" in issue or "self_association" in issue:
        score += max(0.0, -deltas["mean_hydrophobicity"]) * 2.0
        score += max(0.0, -deltas["aromatic_fraction"]) * 2.0
        score += abs(deltas["local_net_charge"]) * 0.15

    if "charge_imbalance" in issue:
        bq = abs(int(before_metrics["local_net_charge"]))
        aq = abs(int(after_metrics["local_net_charge"]))
        score += max(0, bq - aq) * 0.4

    if issue == "site_specific_mitigation":
        score += len(lost) * 2.0
        score -= len(gained) * 2.0
        score += max(0.0, -deltas["mean_hydrophobicity"]) * 0.5
    else:
        score += len(lost) * 1.0
        score -= len(gained) * 1.5
    return round(score, 3)


def compute_disruption_risk(wt: str, mut: str, deltas: dict[str, float]) -> float:
    risk = 0.0

    if wt in {"G", "P", "C"}:
        risk += 1.5
    if abs(deltas["mean_hydrophobicity"]) > 0.8:
        risk += 1.0
    if abs(deltas["local_net_charge"]) >= 2:
        risk += 1.0
    if wt in {"F", "W", "Y"} and mut not in {"F", "W", "Y"}:
        risk += 0.5

    return round(risk, 3)


def assign_recommendation_tier(benefit_score: float, disruption_risk: float) -> str:
    if benefit_score >= 1.5 and disruption_risk <= 1.0:
        return "strong"
    if benefit_score >= 0.7 and disruption_risk <= 1.5:
        return "moderate"
    return "cautious"


def assign_confidence(
    region_analysis: dict[str, Any],
    gained: list[dict],
    deltas: dict[str, float],
) -> str:
    if region_analysis["confidence"] == "high" and not gained and abs(deltas["mean_hydrophobicity"]) >= 0.3:
        return "high"
    if abs(deltas["mean_hydrophobicity"]) >= 0.2:
        return "medium"
    return "low"


def build_mutation_rationale(
    region_analysis: dict[str, Any],
    mutation: str,
    deltas: dict[str, float],
    gained: list[dict],
    lost: list[dict],
) -> str:
    parts = [
        f"{mutation} targets region {region_analysis['start']}-{region_analysis['end']} "
        f"({region_analysis['dominant_issue']})"
    ]

    if deltas["mean_hydrophobicity"] < 0:
        parts.append(f"reduces local hydrophobicity by {abs(deltas['mean_hydrophobicity']):.2f}")
    if deltas["aromatic_fraction"] < 0:
        parts.append(f"reduces aromatic density by {abs(deltas['aromatic_fraction']):.2f}")
    if deltas["local_net_charge"] != 0:
        parts.append(f"changes local net charge by {deltas['local_net_charge']:+.0f}")
    if lost:
        parts.append(f"removes {len(lost)} local liability(s)")
    if gained:
        parts.append(f"introduces {len(gained)} new local liability(s)")

    return "; ".join(parts) + "."


def evaluate_mutation_for_region(
    seq: str,
    region_analysis: dict[str, Any],
    position: int,
    new_residue: str,
) -> dict[str, Any]:
    start, end = region_analysis["start"], region_analysis["end"]
    wt_residue = seq[position - 1]
    mutation = f"{wt_residue}{position}{new_residue}"

    mutated_seq = mutate_sequence(seq, position, new_residue)

    before_metrics = compute_local_metrics(seq, start, end)
    after_metrics = compute_local_metrics(mutated_seq, start, end)

    deltas = compare_local_metrics(before_metrics, after_metrics)

    before_liabs = collect_region_local_liabilities(seq, start, end)
    after_liabs = collect_region_local_liabilities(mutated_seq, start, end)
    gained, lost = diff_liabilities(before_liabs, after_liabs)

    benefit_score = compute_benefit_score(
        region_analysis, deltas, gained, lost, before_metrics, after_metrics
    )
    disruption_risk = compute_disruption_risk(wt_residue, new_residue, deltas)
    recommendation_tier = assign_recommendation_tier(benefit_score, disruption_risk)
    confidence = assign_confidence(region_analysis, gained, deltas)
    rationale = build_mutation_rationale(region_analysis, mutation, deltas, gained, lost)

    return {
        "mutation": mutation,
        "position": position,
        "wt_residue": wt_residue,
        "mut_residue": new_residue,
        "region_start": start,
        "region_end": end,
        "before_metrics": before_metrics,
        "after_metrics": after_metrics,
        "deltas": deltas,
        "liabilities_gained": gained,
        "liabilities_lost": lost,
        "benefit_score": benefit_score,
        "disruption_risk": disruption_risk,
        "confidence": confidence,
        "recommendation_tier": recommendation_tier,
        "rationale": rationale,
        "category": "patch_breaking",
    }
