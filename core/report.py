from typing import Any

import pandas as pd


def build_global_features_table(global_features: dict) -> pd.DataFrame:
    rows = [
        {"Property": k, "Value": v}
        for k, v in global_features.items()
    ]
    return pd.DataFrame(rows)


def build_risk_regions_table(risk_regions: list[dict]) -> pd.DataFrame:
    if not risk_regions:
        return pd.DataFrame(columns=["Start", "End", "Sequence", "Risk Type", "Severity", "Score", "Reason"])

    rows = []
    for r in risk_regions:
        rows.append({
            "Start": r["start"],
            "End": r["end"],
            "Sequence": r["sequence"],
            "Risk Type": r["risk_type"],
            "Severity": r["severity"],
            "Score": r["score"],
            "Reason": r["reason"],
        })
    return pd.DataFrame(rows)


def build_liabilities_table_from_result(result: dict[str, Any]) -> pd.DataFrame:
    """Use structure-mapped liabilities when `structure_context` is present and ok."""
    sc = result.get("structure_context") or {}
    liabilities = result.get("liabilities") or []
    if sc.get("ok") and sc.get("liabilities_mapped"):
        rows = []
        for x in sc["liabilities_mapped"]:
            rows.append(
                {
                    "Position": x.get("position"),
                    "Motif/Residue": x.get("motif_or_residue"),
                    "Liability Type": x.get("liability_type"),
                    "Severity": x.get("severity"),
                    "Comment": x.get("comment"),
                    "Exposure (3D)": x.get("structure_exposure"),
                    "Adj. severity": x.get("severity_structure_adjusted"),
                    "Structure note": x.get("structure_note", ""),
                }
            )
        return pd.DataFrame(rows)
    return build_liabilities_table(liabilities)


def build_liabilities_table(liabilities: list[dict]) -> pd.DataFrame:
    if not liabilities:
        return pd.DataFrame(columns=["Position", "Motif/Residue", "Liability Type", "Severity", "Comment"])

    rows = []
    for x in liabilities:
        rows.append({
            "Position": x["position"],
            "Motif/Residue": x["motif_or_residue"],
            "Liability Type": x["liability_type"],
            "Severity": x["severity"],
            "Comment": x["comment"],
        })
    return pd.DataFrame(rows)


def build_region_analysis_table(region_analyses: list[dict[str, Any]]) -> pd.DataFrame:
    if not region_analyses:
        return pd.DataFrame(
            columns=[
                "Region",
                "Risk type",
                "Dominant issue",
                "Severity",
                "Confidence",
                "Mean hydrophobicity",
                "Aromatic fraction",
                "Local net charge",
                "Reason summary",
                "Design strategy",
            ]
        )

    rows = []
    for r in region_analyses:
        ev = r.get("evidence") or {}
        rows.append(
            {
                "Region": f"{r['start']}–{r['end']}",
                "Risk type": r.get("risk_type"),
                "Dominant issue": r.get("dominant_issue"),
                "Severity": r.get("severity"),
                "Confidence": r.get("confidence"),
                "Mean hydrophobicity": ev.get("mean_hydrophobicity"),
                "Aromatic fraction": ev.get("aromatic_fraction"),
                "Local net charge": ev.get("local_net_charge"),
                "Reason summary": r.get("reason_summary"),
                "Design strategy": r.get("design_strategy"),
            }
        )
    return pd.DataFrame(rows)


def build_mutation_impact_table(impacts: list[dict[str, Any]]) -> pd.DataFrame:
    if not impacts:
        return pd.DataFrame(
            columns=[
                "Rank",
                "Mutation",
                "Option type",
                "Category",
                "Region",
                "Benefit score",
                "Disruption risk",
                "Δ mean hydrophobicity",
                "Δ aromatic fraction",
                "Δ local net charge",
                "Liabilities gained",
                "Liabilities lost",
                "Confidence",
                "Rationale",
            ]
        )

    has_struct = any(x.get("structure_exposure") for x in impacts)
    rows = []
    for i, x in enumerate(impacts, start=1):
        d = x.get("deltas") or {}
        row = {
            "Rank": x.get("rank", i),
            "Mutation": x.get("mutation"),
            "Option type": x.get("option_type", ""),
            "Category": x.get("category", ""),
            "Region": f"{x.get('region_start')}–{x.get('region_end')}",
            "Benefit score": x.get("benefit_score"),
            "Disruption risk": x.get("disruption_risk"),
            "Δ mean hydrophobicity": d.get("mean_hydrophobicity"),
            "Δ aromatic fraction": d.get("aromatic_fraction"),
            "Δ local net charge": d.get("local_net_charge"),
            "Liabilities gained": len(x.get("liabilities_gained") or []),
            "Liabilities lost": len(x.get("liabilities_lost") or []),
            "Confidence": x.get("confidence"),
            "Rationale": x.get("rationale"),
        }
        if has_struct:
            row["Exposure (3D)"] = x.get("structure_exposure", "")
            row["Structure note"] = x.get("structure_note", "")
        rows.append(row)
    return pd.DataFrame(rows)


def build_mutation_table(suggestions: list[dict]) -> pd.DataFrame:
    if not suggestions:
        return pd.DataFrame(
            columns=[
                "Rank",
                "Mutation",
                "Category",
                "Option type",
                "Benefit score",
                "Confidence",
                "Rationale",
            ]
        )

    rows = []
    has_struct = any(s.get("structure_exposure") for s in suggestions)
    for s in suggestions:
        row = {
            "Rank": s.get("rank"),
            "Mutation": s["mutation"],
            "Category": s.get("category", ""),
            "Option type": s.get("option_type", ""),
            "Benefit score": s.get("benefit_score", ""),
            "Confidence": s.get("confidence", ""),
            "Rationale": s.get("rationale", s.get("expected_effect", "")),
        }
        if has_struct:
            row["Exposure (3D)"] = s.get("structure_exposure", "")
            row["Structure note"] = s.get("structure_note", "")
        rows.append(row)
    return pd.DataFrame(rows)


def generate_executive_brief_md(result: dict[str, Any]) -> str:
    """Short narrative for the UI (complements the executive HTML card)."""
    ds = result.get("decision_summary") or {}
    liabs = result.get("liabilities") or []
    n_liab = len(liabs)
    n_risk = len(result.get("risk_regions") or [])
    interp = ds.get("interpretation", "").strip()
    prim = ds.get("primary_recommendation", "").strip()
    drivers = ds.get("top_drivers") or []
    bullets: list[str] = []
    if interp:
        bullets.append(f"- **Readout:** {interp}")
    if prim:
        bullets.append(f"- **Strategy:** {prim}")
    if drivers:
        d0 = drivers[0]
        bullets.append(
            f"- **Top driver:** region **{d0.get('start')}–{d0.get('end')}** "
            f"({d0.get('dominant_issue')})."
        )
    bullets.append(f"- **Flags:** {n_risk} risk span(s), {n_liab} liability hit(s).")
    body = "\n".join(bullets) if bullets else "_Run analysis to populate insights._"
    return "### Insights\n\n" + body


def generate_short_summary(result: dict[str, Any]) -> str:
    score_summary = result["scores"]
    seq_name = result.get("sequence_name") or "input sequence"
    ds = result.get("decision_summary") or {}
    top_drivers = ds.get("top_drivers") or []

    driver_lines = []
    for d in top_drivers[:3]:
        driver_lines.append(
            f"{d.get('rank')}. Region **{d.get('start')}–{d.get('end')}** → "
            f"`{d.get('dominant_issue')}` ({d.get('severity')} severity, {d.get('confidence')} confidence)"
        )
    drivers_md = "\n".join(driver_lines) if driver_lines else "_No ranked drivers._"

    safer = ds.get("safer_option")
    stronger = ds.get("stronger_option")
    dom = ds.get("dominant_region")
    interp = ds.get("interpretation", "")
    prim = ds.get("primary_recommendation", "")

    dom_md = ""
    if dom:
        ev = dom.get("evidence") or {}
        dom_md = (
            f"**Dominant hotspot:** {dom['start']}–{dom['end']}  \n"
            f"- Mean hydrophobicity: **{ev.get('mean_hydrophobicity')}**  \n"
            f"- Aromatic fraction: **{ev.get('aromatic_fraction')}**  \n"
            f"- Local net charge: **{ev.get('local_net_charge')}**  \n"
            f"- Readout: {dom.get('reason_summary', '')}  \n"
            f"- Strategy: {dom.get('design_strategy', '')}  \n"
        )

    options_md = ""
    if safer or stronger:
        options_md = (
            f"- **Safer option:** `{safer or '—'}`  \n"
            f"- **Stronger option:** `{stronger or '—'}`  \n"
        )

    return (
        f"### Summary for {seq_name}\n\n"
        f"{dom_md}\n"
        f"**Top 3 developability drivers:**  \n{drivers_md}\n\n"
        f"- **Overall risk:** {score_summary['overall']['label']}  \n"
        f"- **Aggregation concern:** {score_summary['aggregation']['label']}  \n"
        f"- **Solubility concern:** {score_summary['solubility']['label']}  \n"
        f"- **Chemical liability concern:** {score_summary['chemical']['label']}  \n\n"
        f"**Decision:** {interp}  \n"
        f"**Primary recommendation:** {prim}  \n\n"
        f"{options_md}\n"
    )


def generate_text_report(result: dict) -> str:
    ds = result.get("decision_summary") or {}
    lines = [
        f"Sequence name: {result['sequence_name']}",
        f"Goal: {result['goal']}",
        f"Schema version: {result.get('version')}",
        "",
        "Decision summary:",
        f"  {ds.get('interpretation', '')}",
        f"  Primary recommendation: {ds.get('primary_recommendation', '')}",
        f"  Safer option: {ds.get('safer_option')}",
        f"  Stronger option: {ds.get('stronger_option')}",
        "",
        "Scores:",
        f"  Overall: {result['scores']['overall']['label']} ({result['scores']['overall']['score']})",
        f"  Aggregation: {result['scores']['aggregation']['label']} ({result['scores']['aggregation']['score']})",
        f"  Solubility: {result['scores']['solubility']['label']} ({result['scores']['solubility']['score']})",
        f"  Chemical: {result['scores']['chemical']['label']} ({result['scores']['chemical']['score']})",
        "",
        "Global features:",
    ]
    for k, v in result["global_features"].items():
        lines.append(f"  - {k}: {v}")

    lines.append("")
    lines.append("Region analyses:")
    for r in result.get("region_analyses") or []:
        lines.append(
            f"  - {r['start']}-{r['end']}: {r.get('dominant_issue')} "
            f"({r.get('severity')}, conf {r.get('confidence')}) — {r.get('reason_summary')}"
        )

    lines.append("")
    lines.append("Risk regions (raw):")
    for r in result["risk_regions"]:
        lines.append(f"  - {r['risk_type']} at {r['start']}-{r['end']} ({r['severity']})")

    lines.append("")
    lines.append("Liabilities:")
    for x in result["liabilities"]:
        lines.append(f"  - {x['liability_type']} at {x['position']} ({x['motif_or_residue']})")

    lines.append("")
    lines.append("Mutation impacts (ranked):")
    lines.append(
        "  [Scores are in-app heuristics only — not experimental developability.]"
    )
    lines.append(
        "  benefit_score: composite upside from local metric deltas in the scanned window plus "
        "liability motifs removed/added (higher = more favorable trade-off in this model)."
    )
    lines.append(
        "  disruption_risk: integer-ish penalty for edits considered structurally aggressive here — "
        "e.g. mutating G/P/C (+1.5), large |Δmean hydrophobicity| or |Δlocal net charge| (+1 each), "
        "losing F/W/Y to non-aromatic (+0.5). 0.0 means none of those rules fired, not 'proven safe'."
    )
    lines.append("")
    for s in result.get("mutation_impacts") or []:
        lines.append(
            f"  - {s.get('mutation')} [{s.get('option_type', '')}]: "
            f"benefit_score={s.get('benefit_score')} disruption_risk={s.get('disruption_risk')} — "
            f"{s.get('rationale')}"
        )

    sc = result.get("structure_context") or {}
    if sc:
        lines.append("")
        lines.append("Structure context (optional):")
        if not sc.get("ok"):
            lines.append(f"  Error: {sc.get('error', '')}")
        else:
            integ = sc.get("integration") or {}
            lines.append(f"  {integ.get('summary_line', '')}")
            for w in sc.get("warnings") or []:
                lines.append(f"  Warning: {w}")
            for h in sc.get("structural_hotspots") or []:
                lines.append(
                    f"  - Patch {h.get('id')}: positions {h.get('seq_positions')} "
                    f"(score {h.get('patch_score')})"
                )
            if sc.get("pymol_png_full"):
                lines.append("  PyMOL PNG: available (session temp file; not embedded in this report).")
            if sc.get("pymol_render_error"):
                lines.append(f"  PyMOL render note: {sc.get('pymol_render_error')}")

    return "\n".join(lines)
