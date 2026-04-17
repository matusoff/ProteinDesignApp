"""
Aggregate Cα-based exposure proxies for liability sites vs the whole chain.

These are geometric heuristics (neighbor counts, distance from Cα centroid), not SASA.
"""

from __future__ import annotations

from typing import Any


def compute_liability_patch_stats(
    residue_table: list[dict[str, Any]],
    mapped_liabilities: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Summarize how liability hits sit in the structure using the same proxies as per-residue rows.

    Returns a dict safe to JSON-serialize (numbers + strings only).
    """
    disclaimer = (
        "Cα-only heuristics: neighbor count within 10 Å and distance from the chain Cα centroid "
        "(radial shell percentile). Not SASA, not a binding-interface predictor."
    )

    if not residue_table:
        return {
            "ok": False,
            "disclaimer": disclaimer,
            "interpretation": "No residue table — patch stats unavailable.",
        }

    def _mean(vals: list[float]) -> float | None:
        return float(sum(vals) / len(vals)) if vals else None

    chain_n = len(residue_table)
    chain_nb = [float(r.get("neighbor_count_10A", 0)) for r in residue_table]
    chain_rad = [float(r.get("radial_shell_percentile", 50.0)) for r in residue_table]

    mapped = [m for m in mapped_liabilities if m.get("structure_exposure") != "unmapped"]
    unmapped_n = len(mapped_liabilities) - len(mapped)

    exp_counts: dict[str, int] = {"exposed": 0, "intermediate": 0, "buried": 0}
    li_nb: list[float] = []
    li_rad: list[float] = []
    for m in mapped:
        cls = str(m.get("structure_exposure") or "intermediate")
        if cls in exp_counts:
            exp_counts[cls] += 1
        if m.get("neighbor_count_10A") is not None:
            li_nb.append(float(m["neighbor_count_10A"]))
        if m.get("radial_shell_percentile") is not None:
            li_rad.append(float(m["radial_shell_percentile"]))

    mnb = _mean(li_nb)
    mrad = _mean(li_rad)
    cnb = _mean(chain_nb)
    crad = _mean(chain_rad)

    interpretation = ""
    if not mapped:
        interpretation = (
            f"No liabilities mapped to coordinates ({unmapped_n} unmapped)."
            if unmapped_n
            else "No sequence liabilities — patch stats refer to the empty liability list."
        )
    else:
        parts = [
            f"{len(mapped)} liability site(s) mapped on chain ({chain_n} residues).",
            f"Exposure mix: {exp_counts['exposed']} exposed / {exp_counts['intermediate']} intermediate / "
            f"{exp_counts['buried']} buried (tertiles of 10 Å neighbor counts on this chain).",
        ]
        if mnb is not None and cnb is not None:
            delta = mnb - cnb
            parts.append(
                f"Mean neighbors @10 Å: {mnb:.1f} at liabilities vs {cnb:.1f} chain-wide "
                f"({'fewer' if delta < -0.5 else 'more' if delta > 0.5 else 'similar'} local packing at hits)."
            )
        if mrad is not None and crad is not None:
            parts.append(
                f"Mean radial shell percentile: {mrad:.1f}% vs {crad:.1f}% chain-wide "
                "(higher → farther from Cα centroid; crude ‘outer shell’ proxy for globular folds)."
            )
        if unmapped_n:
            parts.append(f"{unmapped_n} liability row(s) not mapped to structure indices.")
        interpretation = " ".join(parts)

    return {
        "ok": True,
        "disclaimer": disclaimer,
        "chain_residue_count": chain_n,
        "liability_mapped_count": len(mapped),
        "liability_unmapped_count": unmapped_n,
        "exposure_counts": exp_counts,
        "chain_mean_neighbors_10A": cnb,
        "liability_mean_neighbors_10A": mnb,
        "chain_mean_radial_shell_pct": crad,
        "liability_mean_radial_shell_pct": mrad,
        "interpretation": interpretation,
    }
