import tempfile
from pathlib import Path
from typing import Any

import gradio as gr
import pandas as pd

from core.analyze import analyze_sequence
from core.compare import compare_results
from core.export_bundle import write_report_txt, write_tables_zip
from core.report import (
    build_global_features_table,
    build_liabilities_table_from_result,
    build_mutation_impact_table,
    build_mutation_table,
    build_region_analysis_table,
    build_risk_regions_table,
    generate_executive_brief_md,
    generate_text_report,
)
from core.structure_analysis import analyze_structure_context
from core.structure_prediction import predict_structure
from plots.hydrophobicity_plot import (
    compute_hydrophobicity_profile,
    make_hydrophobicity_comparison_plot,
    make_hydrophobicity_plot,
)
from config import REVIEW_GOAL_DEFAULT
from data.example_sequences import DEMO_FASTAS, demo_structure_path
from utils.sequence_format import format_sequence_map
from ui.visual_components import (
    build_executive_summary_html,
    build_sequence_risk_map_html,
    build_structure_section_html,
)


def _uploaded_file_path(file_obj) -> str | None:
    if file_obj is None:
        return None
    if isinstance(file_obj, str):
        return file_obj or None
    p = getattr(file_obj, "name", None)
    return str(p) if p else None


def run_analysis(
    sequence_text: str,
    seq_name: str,
    protected_text: str,
    sequence_map_style: str,
    session_state: dict[str, Any] | None,
    structure_file: Any = None,
    structure_chain: str = "",
):
    result, error_md = analyze_sequence(
        sequence_text=sequence_text,
        sequence_name=seq_name,
        goal=REVIEW_GOAL_DEFAULT,
        protected_text=protected_text,
    )
    if error_md:
        return (
            error_md,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            session_state,
            None,
            "<div></div>",
        )

    spath = _uploaded_file_path(structure_file)
    chain = (structure_chain or "").strip() or None
    if spath:
        sc = analyze_structure_context(
            result["sequence"],
            spath,
            chain,
            result["liabilities"],
            result["risk_regions"],
            result["mutation_suggestions"],
            result["mutation_impacts"],
        )
        result["structure_context"] = sc
        if sc.get("ok"):
            result["mutation_suggestions"] = sc["mutation_suggestions_structure"]
            result["mutation_impacts"] = sc["mutation_impacts_structure"]
        result["report_text"] = generate_text_report(result)

    executive_html = build_executive_summary_html(result)
    risk_map_html = build_sequence_risk_map_html(
        result["sequence"],
        result["risk_regions"],
        result["liabilities"],
        set(result["protected_positions"]),
    )
    insights_md = generate_executive_brief_md(result)

    gf_df = build_global_features_table(result["global_features"])
    rr_df = build_risk_regions_table(result["risk_regions"])
    liab_df = build_liabilities_table_from_result(result)
    region_df = build_region_analysis_table(result.get("region_analyses") or [])
    impact_df = build_mutation_impact_table(result.get("mutation_impacts") or [])
    mut_df = build_mutation_table(result["mutation_suggestions"])

    sc = result.get("structure_context") or {}
    structure_panel_html = build_structure_section_html(result.get("structure_context"))
    img_path: str | None = None
    if sc.get("ok") and sc.get("pymol_png_full"):
        p = str(sc["pymol_png_full"])
        img_path = p if Path(p).is_file() else None

    profile = compute_hydrophobicity_profile(result["sequence"])
    fig = make_hydrophobicity_plot(
        result["sequence"],
        profile,
        result["risk_regions"],
        set(result["protected_positions"]),
    )

    session_state = session_state or {"history": []}
    session_state.setdefault("history", [])
    session_state["last_run"] = {"mode": "single", "result": result}
    session_state["history"].append({"mode": "single", "result": result})

    seq_map = format_sequence_map(result["sequence"], sequence_map_style or "blocks_20")

    analysis_state = result
    return (
        executive_html,
        risk_map_html,
        insights_md,
        gf_df,
        rr_df,
        liab_df,
        region_df,
        impact_df,
        mut_df,
        fig,
        result.get("report_text", ""),
        seq_map,
        analysis_state,
        session_state,
        img_path,
        structure_panel_html,
    )


def run_compare(
    wt_text: str,
    wt_name: str,
    mutant_text: str,
    mutant_name: str,
    protected_text: str,
    sequence_map_style: str,
    session_state: dict[str, Any] | None,
):
    wt_result, wt_error = analyze_sequence(
        sequence_text=wt_text,
        sequence_name=wt_name or "WT",
        goal=REVIEW_GOAL_DEFAULT,
        protected_text=protected_text,
    )
    if wt_error:
        return wt_error, None, None, None, None, None, None, None, None, None, session_state

    mut_result, mut_error = analyze_sequence(
        sequence_text=mutant_text,
        sequence_name=mutant_name or "Mutant",
        goal=REVIEW_GOAL_DEFAULT,
        protected_text=protected_text,
    )
    if mut_error:
        return mut_error, None, None, None, None, None, None, None, None, None, session_state

    comp = compare_results(wt_result, mut_result)

    changed = comp.get("changed_residues") or []
    changed_cols = [
        "position",
        "wt_residue",
        "mut_residue",
        "mutation",
        "category",
        "wt_local_hydro",
        "mut_local_hydro",
        "hydrophobicity_delta",
    ]
    changed_df = pd.DataFrame(changed, columns=changed_cols) if changed else pd.DataFrame(columns=changed_cols)

    risk = comp.get("risk_delta") or {}
    rows = [
        {
            "Metric": "Overall",
            "WT": risk.get("wt_overall", 0.0),
            "Mutant": risk.get("mut_overall", 0.0),
            "Delta": risk.get("delta_overall", 0.0),
        },
        {
            "Metric": "Aggregation",
            "WT": risk.get("breakdown", {}).get("aggregation", {}).get("wt", 0.0),
            "Mutant": risk.get("breakdown", {}).get("aggregation", {}).get("mut", 0.0),
            "Delta": float(risk.get("breakdown", {}).get("aggregation", {}).get("mut", 0.0))
            - float(risk.get("breakdown", {}).get("aggregation", {}).get("wt", 0.0)),
        },
        {
            "Metric": "Solubility",
            "WT": risk.get("breakdown", {}).get("solubility", {}).get("wt", 0.0),
            "Mutant": risk.get("breakdown", {}).get("solubility", {}).get("mut", 0.0),
            "Delta": float(risk.get("breakdown", {}).get("solubility", {}).get("mut", 0.0))
            - float(risk.get("breakdown", {}).get("solubility", {}).get("wt", 0.0)),
        },
        {
            "Metric": "Chemical liabilities",
            "WT": risk.get("breakdown", {}).get("chemical", {}).get("wt", 0.0),
            "Mutant": risk.get("breakdown", {}).get("chemical", {}).get("mut", 0.0),
            "Delta": float(risk.get("breakdown", {}).get("chemical", {}).get("mut", 0.0))
            - float(risk.get("breakdown", {}).get("chemical", {}).get("wt", 0.0)),
        },
    ]
    risk_df = pd.DataFrame(rows)

    gained = (comp.get("liability_diff") or {}).get("gained") or []
    lost = (comp.get("liability_diff") or {}).get("lost") or []

    gained_df = pd.DataFrame(gained) if gained else pd.DataFrame(columns=["position", "motif_or_residue", "liability_type", "severity", "comment"])
    lost_df = pd.DataFrame(lost) if lost else pd.DataFrame(columns=["position", "motif_or_residue", "liability_type", "severity", "comment"])

    wt_seq = wt_result["sequence"]
    mut_seq = mut_result["sequence"]
    wt_profile = compute_hydrophobicity_profile(wt_seq)
    mut_profile = compute_hydrophobicity_profile(mut_seq)
    changed_positions = [int(c["position"]) for c in changed if c.get("category") == "substitution"]
    fig = make_hydrophobicity_comparison_plot(wt_seq, mut_seq, wt_profile, mut_profile, changed_positions)

    compare_md = comp.get("compare_markdown", "")
    style = sequence_map_style or "blocks_20"
    wt_map = format_sequence_map(wt_result["sequence"], style)
    mut_map = format_sequence_map(mut_result["sequence"], style)
    per_region = comp.get("per_region_deltas") or []
    per_region_df = pd.DataFrame(per_region) if per_region else pd.DataFrame(
        columns=[
            "region",
            "dominant_issue",
            "wt_mean_hydro",
            "mut_mean_hydro",
            "delta_mean_hydro",
            "delta_local_net_charge",
            "interpretation",
        ]
    )

    session_state = session_state or {"history": []}
    session_state.setdefault("history", [])
    session_state["last_run"] = {"mode": "compare", "wt_result": wt_result, "mut_result": mut_result, "comparison": comp}
    session_state["history"].append(
        {"mode": "compare", "wt_result": wt_result, "mut_result": mut_result, "comparison": comp}
    )

    compare_state = comp
    return (
        compare_md,
        wt_map,
        mut_map,
        per_region_df,
        changed_df,
        risk_df,
        gained_df,
        lost_df,
        fig,
        compare_state,
        session_state,
    )


def export_tables_zip_callback(state: dict | None):
    path, err = write_tables_zip(state)
    if err:
        raise gr.Error(err)
    return path


def export_report_txt_callback(state: dict | None):
    path, err = write_report_txt(state)
    if err:
        raise gr.Error(err)
    return path


def run_structure_prediction(state: dict | None):
    if not state:
        return "### Run **Analyze** first.", None, "<div></div>"

    seq = state.get("sequence") or ""
    res = predict_structure(seq)
    md = res.get("markdown", "")
    pdb_text = res.get("pdb")
    pdb_path = None
    if pdb_text:
        p = Path(tempfile.mkstemp(suffix=".pdb", prefix="esmfold_")[1])
        p.write_text(pdb_text, encoding="utf-8")
        pdb_path = str(p)
    html = res.get("html") or ""
    if not html:
        html = "<div></div>"
    return md, pdb_path, html


def load_example_sequence(demo_key: str):
    key = demo_key if demo_key in DEMO_FASTAS else "hcv"
    fasta = DEMO_FASTAS[key]
    coord_path = demo_structure_path(key)
    return fasta, coord_path
