from __future__ import annotations

from typing import Any

from config import HYDRO_WINDOW
from core.mutation_impact import compare_local_metrics, compute_local_metrics
from utils.constants import KD_SCALE


def _local_mean_kd_hydrophobicity(seq: str, position_1based: int, window: int = HYDRO_WINDOW) -> float:
    """
    Local hydrophobicity around a residue position using KD scale.

    Uses a centered window (clipped at ends). This is only for relative comparisons.
    """

    if not seq:
        return 0.0

    pos0 = position_1based - 1
    half = window // 2
    start = max(0, pos0 - half)
    end = min(len(seq), pos0 + half + 1)
    segment = seq[start:end]
    if not segment:
        return 0.0
    return sum(KD_SCALE[a] for a in segment) / len(segment)


def _mutation_label(wt: str, mut: str, position_1based: int) -> str:
    # wt could be '-' for insertion cases
    if wt == "-" and mut == "-":
        return f"{position_1based}"
    if wt == "-":
        return f"ins{mut}{position_1based}"
    if mut == "-":
        return f"del{wt}{position_1based}"
    return f"{wt}{position_1based}{mut}"


def changed_residues(
    wt_seq: str,
    mut_seq: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Returns (changes, meta).

    For v0.2 we do position-by-position comparison.
    If lengths differ, we report trailing insertions/deletions.
    """

    changes: list[dict[str, Any]] = []
    min_len = min(len(wt_seq), len(mut_seq))
    for i in range(min_len):
        if wt_seq[i] != mut_seq[i]:
            pos = i + 1
            changes.append(
                {
                    "position": pos,
                    "wt_residue": wt_seq[i],
                    "mut_residue": mut_seq[i],
                    "mutation": _mutation_label(wt_seq[i], mut_seq[i], pos),
                    "category": "substitution",
                }
            )

    meta: dict[str, Any] = {"wt_len": len(wt_seq), "mut_len": len(mut_seq)}

    if len(wt_seq) != len(mut_seq):
        if len(mut_seq) < len(wt_seq):
            for i in range(min_len, len(wt_seq)):
                pos = i + 1
                changes.append(
                    {
                        "position": pos,
                        "wt_residue": wt_seq[i],
                        "mut_residue": "-",
                        "mutation": _mutation_label(wt_seq[i], "-", pos),
                        "category": "deletion",
                    }
                )
            meta["length_event"] = "deletion"
        else:
            for i in range(min_len, len(mut_seq)):
                pos = i + 1
                changes.append(
                    {
                        "position": pos,
                        "wt_residue": "-",
                        "mut_residue": mut_seq[i],
                        "mutation": _mutation_label("-", mut_seq[i], pos),
                        "category": "insertion",
                    }
                )
            meta["length_event"] = "insertion"
    else:
        meta["length_event"] = "same"

    return changes, meta


def _risk_delta_summary(wt_score: float, mut_score: float) -> tuple[float, str, str]:
    delta = mut_score - wt_score

    # score is constructed as "higher = worse" in the current scoring scheme
    if delta <= -0.5:
        label = "favorable"
    elif delta >= 0.5:
        label = "risky"
    else:
        label = "mixed"

    explanation = (
        "Overall risk decreased (mutant looks favorable)."
        if label == "favorable"
        else "Overall risk increased (mutant looks risky)."
        if label == "risky"
        else "Overall risk is similar (mutant looks mixed)."
    )
    return delta, label, explanation


def _per_region_metric_deltas(
    wt_seq: str,
    mut_seq: str,
    wt_region_analyses: list[dict[str, Any]],
    dominant_region: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    primary_improved = False

    for ra in wt_region_analyses:
        start, end = int(ra["start"]), int(ra["end"])
        if start < 1 or end > len(wt_seq) or end > len(mut_seq):
            continue

        before = compute_local_metrics(wt_seq, start, end)
        after = compute_local_metrics(mut_seq, start, end)
        deltas = compare_local_metrics(before, after)

        issue = str(ra.get("dominant_issue") or "")
        improvement = ""
        if ("aggregation" in issue or "self_association" in issue) and deltas["mean_hydrophobicity"] < -0.15:
            improvement = "significant_improvement"
            if (
                dominant_region
                and ra["start"] == dominant_region["start"]
                and ra["end"] == dominant_region["end"]
            ):
                primary_improved = True
        elif deltas["mean_hydrophobicity"] < -0.08:
            improvement = "moderate_improvement"
        elif deltas["mean_hydrophobicity"] > 0.08:
            improvement = "worsened"
        else:
            improvement = "similar"

        rows.append(
            {
                "region": f"{start}–{end}",
                "dominant_issue": issue,
                "wt_mean_hydro": before["mean_hydrophobicity"],
                "mut_mean_hydro": after["mean_hydrophobicity"],
                "delta_mean_hydro": deltas["mean_hydrophobicity"],
                "delta_local_net_charge": deltas["local_net_charge"],
                "interpretation": improvement,
            }
        )

    return rows, primary_improved


def compare_results(wt: dict[str, Any], mut: dict[str, Any]) -> dict[str, Any]:
    wt_seq = wt.get("sequence") or ""
    mut_seq = mut.get("sequence") or ""

    changes, meta = changed_residues(wt_seq, mut_seq)

    wt_overall = float(wt.get("scores", {}).get("overall", {}).get("score", 0.0))
    mut_overall = float(mut.get("scores", {}).get("overall", {}).get("score", 0.0))
    delta_overall, label, explanation = _risk_delta_summary(wt_overall, mut_overall)

    risk_breakdown = {
        "aggregation": {
            "wt": wt.get("scores", {}).get("aggregation", {}).get("score", 0.0),
            "mut": mut.get("scores", {}).get("aggregation", {}).get("score", 0.0),
        },
        "solubility": {
            "wt": wt.get("scores", {}).get("solubility", {}).get("score", 0.0),
            "mut": mut.get("scores", {}).get("solubility", {}).get("score", 0.0),
        },
        "chemical": {
            "wt": wt.get("scores", {}).get("chemical", {}).get("score", 0.0),
            "mut": mut.get("scores", {}).get("chemical", {}).get("score", 0.0),
        },
    }

    # Add hydrophobicity deltas near each substitution
    hydro_changes: list[dict[str, Any]] = []
    for c in changes:
        if c["category"] != "substitution":
            continue
        pos = int(c["position"])
        wt_local = _local_mean_kd_hydrophobicity(wt_seq, pos)
        mut_local = _local_mean_kd_hydrophobicity(mut_seq, pos)
        updated = {
            **c,
            "wt_local_hydro": round(wt_local, 3),
            "mut_local_hydro": round(mut_local, 3),
            "hydrophobicity_delta": round(mut_local - wt_local, 3),
        }
        hydro_changes.append(updated)
        # Update the original change entry for simpler table rendering.
        c.update(updated)

    # Liabilities gained/lost
    def _liab_key(x: dict[str, Any]) -> tuple[Any, ...]:
        return (x.get("liability_type"), x.get("position"), x.get("motif_or_residue"))

    wt_liab = wt.get("liabilities") or []
    mut_liab = mut.get("liabilities") or []
    wt_keys = {_liab_key(x) for x in wt_liab}
    mut_keys = {_liab_key(x) for x in mut_liab}

    gained_keys = mut_keys - wt_keys
    lost_keys = wt_keys - mut_keys

    gained = [x for x in mut_liab if _liab_key(x) in gained_keys]
    lost = [x for x in wt_liab if _liab_key(x) in lost_keys]

    # Keep output deterministic-ish
    gained = sorted(gained, key=lambda x: (x.get("liability_type", ""), x.get("position", 0)))
    lost = sorted(lost, key=lambda x: (x.get("liability_type", ""), x.get("position", 0)))

    # Compose compact markdown summary
    top_changes = changes[:6]
    top_changes_txt = (
        ", ".join([c["mutation"] for c in top_changes])
        if top_changes
        else "No residue differences detected."
    )

    def _short_list(items: list[dict[str, Any]]) -> str:
        if not items:
            return "none"
        s = [f"{x.get('liability_type')}@{x.get('position')}" for x in items[:5]]
        return ", ".join(s)

    gained_txt = _short_list(gained)
    lost_txt = _short_list(lost)

    wt_region_analyses = wt.get("region_analyses") or []
    dominant_region = (wt.get("decision_summary") or {}).get("dominant_region")
    per_region, primary_improved = _per_region_metric_deltas(
        wt_seq, mut_seq, wt_region_analyses, dominant_region
    )

    per_region_md = ""
    if per_region:
        lines = []
        for pr in per_region[:8]:
            lines.append(
                f"- **{pr['region']}** ({pr['dominant_issue']}): "
                f"mean hydro {pr['wt_mean_hydro']:.3f} → {pr['mut_mean_hydro']:.3f} "
                f"(Δ {pr['delta_mean_hydro']:+.3f}) — _{pr['interpretation']}_"
            )
        per_region_md = "\n".join(lines)

    narrative = explanation
    if label == "mixed" and primary_improved:
        narrative = (
            "Overall composite score is similar, but the **primary developability driver region** "
            "shows improved local biophysics (lower local hydrophobicity / better patch disruption). "
            "This can still be a favorable engineering direction."
        )

    compare_md = (
        f"## WT vs Mutant summary\n\n"
        f"**Overall label:** {label}  \n"
        f"**Overall risk:** {wt_overall:.2f} → {mut_overall:.2f} (delta {delta_overall:+.2f})  \n\n"
        f"### Per-region local biophysics (same coordinates on WT vs Mutant)\n"
        f"{per_region_md or '_No overlapping regions to compare._'}\n\n"
        f"**Changed residues:** {top_changes_txt}\n\n"
        f"**Liabilities:** gained({len(gained)})={gained_txt}; lost({len(lost)})={lost_txt}\n\n"
        f"**Interpretation:** {narrative}\n"
    )

    return {
        "version": wt.get("version") or mut.get("version") or "0.2.0",
        "wt": wt,
        "mutant": mut,
        "changed_residues": changes,
        "changed_residues_meta": meta,
        "risk_delta": {
            "wt_overall": wt_overall,
            "mut_overall": mut_overall,
            "delta_overall": delta_overall,
            "label": label,
            "explanation": explanation,
            "breakdown": risk_breakdown,
        },
        "hydrophobicity_changes_near_mutations": hydro_changes,
        "liability_diff": {
            "gained": gained,
            "lost": lost,
        },
        "compare_markdown": compare_md,
        "per_region_deltas": per_region,
        "primary_region_improved": primary_improved,
    }

