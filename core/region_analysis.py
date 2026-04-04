from __future__ import annotations

from typing import Any

from utils.sequence_utils import (
    local_aromatic_fraction,
    local_charged_fraction,
    local_flexibility_proxy,
    local_hydrophobic_fraction,
    local_low_complexity,
    local_mean_hydrophobicity,
    local_net_charge,
)


def collect_region_liabilities(start: int, end: int, liabilities: list[dict]) -> list[dict]:
    return [x for x in liabilities if start <= x["position"] <= end]


def build_region_evidence(region: dict, liabilities: list[dict]) -> dict[str, Any]:
    seq = region.get("sequence") or ""
    if not seq:
        return {
            "mean_hydrophobicity": 0.0,
            "hydrophobic_fraction": 0.0,
            "aromatic_fraction": 0.0,
            "local_net_charge": 0,
            "charged_fraction": 0.0,
            "low_complexity": False,
            "flexibility_proxy": 0.0,
            "liability_count": 0,
        }

    local_liabs = collect_region_liabilities(region["start"], region["end"], liabilities)

    return {
        "mean_hydrophobicity": round(local_mean_hydrophobicity(seq), 3),
        "hydrophobic_fraction": round(local_hydrophobic_fraction(seq), 3),
        "aromatic_fraction": round(local_aromatic_fraction(seq), 3),
        "local_net_charge": local_net_charge(seq),
        "charged_fraction": round(local_charged_fraction(seq), 3),
        "low_complexity": local_low_complexity(seq),
        "flexibility_proxy": round(local_flexibility_proxy(seq), 3),
        "liability_count": len(local_liabs),
    }


def infer_dominant_issue(region: dict, evidence: dict[str, Any]) -> str:
    if region["risk_type"] == "hydrophobic_cluster":
        if evidence["aromatic_fraction"] >= 0.20 and abs(evidence["local_net_charge"]) <= 1:
            return "self_association_hotspot"
        return "solubility_or_aggregation_hotspot"

    if region["risk_type"] == "aromatic_cluster":
        return "aromatic_packing_or_self_association_hotspot"

    if region["risk_type"] == "charge_patch":
        return "local_charge_imbalance"

    if region["risk_type"] == "low_complexity":
        return "local_flexibility_or_disorder_risk"

    return "regional_sequence_concern"


def infer_confidence(region: dict, evidence: dict[str, Any]) -> str:
    signals = 0
    if evidence["mean_hydrophobicity"] >= 2.0:
        signals += 1
    if evidence["aromatic_fraction"] >= 0.20:
        signals += 1
    if abs(evidence["local_net_charge"]) <= 1:
        signals += 1
    if evidence["liability_count"] > 0:
        signals += 1

    if signals >= 3:
        return "high"
    if signals == 2:
        return "medium"
    return "low"


def build_reason_summary(region: dict, evidence: dict[str, Any]) -> str:
    parts: list[str] = []

    if evidence["mean_hydrophobicity"] >= 1.5:
        parts.append(f"elevated mean hydrophobicity ({evidence['mean_hydrophobicity']})")
    if evidence["aromatic_fraction"] >= 0.20:
        parts.append(f"aromatic enrichment ({evidence['aromatic_fraction']:.2f})")
    if abs(evidence["local_net_charge"]) <= 1:
        parts.append("weak local charge compensation")
    if evidence["liability_count"] > 0:
        parts.append(f"{evidence['liability_count']} local liabilities")

    if not parts:
        return "Region flagged by heuristic scanner."
    return ", ".join(parts)


def propose_design_strategy(dominant_issue: str) -> str:
    mapping = {
        "self_association_hotspot": (
            "Break the local hydrophobic/aromatic patch with conservative polarity or charge introduction."
        ),
        "solubility_or_aggregation_hotspot": (
            "Reduce local hydrophobic exposure with low-disruption substitutions."
        ),
        "aromatic_packing_or_self_association_hotspot": (
            "Reduce aromatic clustering while preserving local packing where possible."
        ),
        "local_charge_imbalance": (
            "Rebalance local charge without creating new hydrophobic hotspots."
        ),
        "local_flexibility_or_disorder_risk": (
            "Review whether this segment should remain flexible or be stabilized."
        ),
    }
    return mapping.get(dominant_issue, "Review region-specific mutation options carefully.")


def analyze_regions(risk_regions: list[dict], liabilities: list[dict]) -> list[dict[str, Any]]:
    analyses: list[dict[str, Any]] = []
    for region in risk_regions:
        evidence = build_region_evidence(region, liabilities)
        dominant_issue = infer_dominant_issue(region, evidence)
        confidence = infer_confidence(region, evidence)
        reason_summary = build_reason_summary(region, evidence)
        strategy = propose_design_strategy(dominant_issue)

        analyses.append(
            {
                "start": region["start"],
                "end": region["end"],
                "sequence": region.get("sequence") or "",
                "risk_type": region.get("risk_type"),
                "dominant_issue": dominant_issue,
                "severity": region.get("severity"),
                "confidence": confidence,
                "evidence": evidence,
                "reason_summary": reason_summary,
                "design_strategy": strategy,
                "source_flags": [region],
            }
        )

    return analyses
