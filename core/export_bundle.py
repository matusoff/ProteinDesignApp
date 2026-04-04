"""Write analysis results to downloadable files (CSV bundle / TXT)."""

from __future__ import annotations

import io
import json
import tempfile
import zipfile
from pathlib import Path

import pandas as pd


def _df_to_zip_str(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def write_report_txt(state: dict | None) -> tuple[str | None, str]:
    if not state:
        return None, "Run Analyze first, then export."
    path = Path(tempfile.mkstemp(suffix=".txt", prefix="protein_review_")[1])
    path.write_text(state.get("report_text", ""), encoding="utf-8")
    return str(path), ""


def write_tables_zip(state: dict | None) -> tuple[str | None, str]:
    if not state:
        return None, "Run Analyze first, then export."
    gf = state.get("global_features") or {}
    rr = state.get("risk_regions") or []
    liab = state.get("liabilities") or []
    mut = state.get("mutation_suggestions") or []
    scores = state.get("scores") or {}

    zip_path = Path(tempfile.mkstemp(suffix=".zip", prefix="protein_review_tables_")[1])
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "global_features.csv",
            _df_to_zip_str(pd.DataFrame([{"Property": k, "Value": v} for k, v in gf.items()])),
        )
        zf.writestr("risk_regions.csv", _df_to_zip_str(pd.DataFrame(rr)) if rr else "")
        zf.writestr("liabilities.csv", _df_to_zip_str(pd.DataFrame(liab)) if liab else "")
        zf.writestr(
            "mutation_suggestions.csv",
            _df_to_zip_str(pd.DataFrame(mut)) if mut else "",
        )
        zf.writestr("scores.json", json.dumps(scores, indent=2))
        zf.writestr("region_analyses.json", json.dumps(state.get("region_analyses") or [], indent=2))
        zf.writestr("mutation_impacts.json", json.dumps(state.get("mutation_impacts") or [], indent=2, default=str))
        zf.writestr("decision_summary.json", json.dumps(state.get("decision_summary") or {}, indent=2, default=str))
        sc = state.get("structure_context") or {}
        if sc:
            sc_json = dict(sc)
            zf.writestr("structure_context.json", json.dumps(sc_json, indent=2, default=str))
            p = sc.get("pymol_png_full")
            if p and Path(p).is_file():
                zf.write(p, arcname="structure_preview.png")

    return str(zip_path), ""
