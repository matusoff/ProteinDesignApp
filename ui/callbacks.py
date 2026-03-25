import tempfile
from pathlib import Path

import gradio as gr

from core.parser import extract_sequence, validate_sequence
from core.features import summarize_global_features
from core.scanner import identify_risk_regions
from core.liabilities import find_sequence_liabilities
from core.protected_regions import parse_protected_regions
from core.scoring import build_score_summary
from core.mutations import generate_mutation_suggestions
from core.export_bundle import write_report_txt, write_tables_zip
from core.structure_prediction import predict_structure
from core.report import (
    build_global_features_table,
    build_risk_regions_table,
    build_liabilities_table,
    build_mutation_table,
    generate_short_summary,
    generate_text_report,
)
from plots.hydrophobicity_plot import compute_hydrophobicity_profile, make_hydrophobicity_plot
from data.example_sequences import EXAMPLE_FASTA


def run_analysis(sequence_text: str, seq_name: str, goal: str, protected_text: str):
    seq = extract_sequence(sequence_text)
    is_valid, errors = validate_sequence(seq)
    if not is_valid:
        error_md = "### Input error\n\n" + "\n".join([f"- {e}" for e in errors])
        return (
            error_md,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )

    protected_positions = parse_protected_regions(protected_text)

    global_features = summarize_global_features(seq)
    risk_regions = identify_risk_regions(seq)
    liabilities = find_sequence_liabilities(seq)
    scores = build_score_summary(global_features, risk_regions, liabilities)
    suggestions = generate_mutation_suggestions(seq, risk_regions, liabilities, protected_positions)

    summary_md = generate_short_summary(
        seq_name=seq_name or "input sequence",
        score_summary=scores,
        risk_regions=risk_regions,
        liabilities=liabilities,
        suggestions=suggestions,
    )

    result = {
        "sequence": seq,
        "sequence_name": seq_name or "input sequence",
        "goal": goal,
        "protected_positions": sorted(protected_positions),
        "global_features": global_features,
        "risk_regions": risk_regions,
        "liabilities": liabilities,
        "scores": scores,
        "mutation_suggestions": suggestions,
    }
    report_text = generate_text_report(result)

    gf_df = build_global_features_table(global_features)
    rr_df = build_risk_regions_table(risk_regions)
    liab_df = build_liabilities_table(liabilities)
    mut_df = build_mutation_table(suggestions)

    profile = compute_hydrophobicity_profile(seq)
    fig = make_hydrophobicity_plot(seq, profile, risk_regions, protected_positions)

    state = {
        "sequence": seq,
        "sequence_name": result["sequence_name"],
        "goal": goal,
        "report_text": report_text,
        "global_features": global_features,
        "risk_regions": risk_regions,
        "liabilities": liabilities,
        "scores": scores,
        "mutation_suggestions": suggestions,
    }

    return summary_md, gf_df, rr_df, liab_df, mut_df, fig, report_text, state


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


def load_example_sequence():
    return EXAMPLE_FASTA
