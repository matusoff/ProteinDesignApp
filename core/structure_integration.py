"""
Merge sequence-level results with structure-derived features (MVP heuristics).
"""

from __future__ import annotations

from typing import Any


def integrate_sequence_and_structure(
    risk_regions: list[dict[str, Any]],
    liabilities: list[dict[str, Any]],
    residue_table: list[dict[str, Any]],
    structural_hotspots: list[dict[str, Any]],
    mapped_liabilities: list[dict[str, Any]],
    sequence_warnings: list[str],
) -> dict[str, Any]:
    """
    Produce a summary blob for UI/export; optional mutation list adjustments.
    """
    exposed_liabs = [x for x in mapped_liabilities if x.get("structure_exposure") == "exposed"]
    boosted_regions: list[str] = []
    for r in risk_regions:
        rt = str(r.get("risk_type", ""))
        if rt != "hydrophobic_cluster":
            continue
        s, e = int(r["start"]), int(r["end"])
        overlap = any(
            s <= int(p) <= e
            for hs in structural_hotspots
            for p in hs.get("seq_positions", [])
        )
        if overlap:
            boosted_regions.append(f"{s}–{e}")

    return {
        "sequence_structure_warnings": list(sequence_warnings),
        "structural_hotspot_count": len(structural_hotspots),
        "exposed_liability_count": len(exposed_liabs),
        "region_ids_with_3d_hydrophobic_support": boosted_regions,
        "summary_line": _summary_line(structural_hotspots, exposed_liabs, sequence_warnings),
    }


def _summary_line(
    hotspots: list[dict[str, Any]],
    exposed_liabs: list[dict[str, Any]],
    warnings: list[str],
) -> str:
    parts = [
        f"{len(hotspots)} surface hydrophobic patch(es) (3D)",
        f"{len(exposed_liabs)} liability site(s) on exposed structure",
    ]
    if warnings:
        parts.append("numbering/coverage warnings — see details")
    return "; ".join(parts) + "."


def adjust_mutations_for_structure(
    mutation_suggestions: list[dict[str, Any]],
    residue_table: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add structure_exposure / note; small benefit bump for exposed hydrophobic positions."""
    by_pos = {int(r["seq_index"]): r for r in residue_table}
    out: list[dict[str, Any]] = []
    hydro = set("AVILMFYW")
    for m in mutation_suggestions:
        x = dict(m)
        pos = int(x.get("position", 0))
        row = by_pos.get(pos)
        if row:
            exp = row.get("exposure_class", "unknown")
            x["structure_exposure"] = exp
            wt = str(x.get("mutation", "X0X"))[0] if x.get("mutation") else ""
            if exp == "exposed" and wt in hydro:
                x["benefit_score"] = float(x.get("benefit_score", 0)) + 0.35
                x["structure_note"] = "Exposed hydrophobic — patch mitigation likely surface-relevant."
            elif exp == "buried":
                x["structure_note"] = "Buried site — consider higher structural risk for substitutions."
        else:
            x["structure_exposure"] = "unmapped"
        out.append(x)
    out.sort(key=lambda z: (-float(z.get("benefit_score", 0)), z.get("disruption_risk", 0), z.get("position", 0)))
    for i, z in enumerate(out, start=1):
        z["rank"] = i
    return out
