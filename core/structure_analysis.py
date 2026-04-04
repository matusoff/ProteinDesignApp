"""
End-to-end optional structure file analysis (PDB/mmCIF).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.structure_features import (
    apply_exposure_classification,
    compute_residue_exposure,
    enrich_residue_table_with_coords,
)
from core.structure_hotspots import find_exposed_mwn, identify_structural_hotspots
from core.structure_integration import (
    adjust_mutations_for_structure,
    integrate_sequence_and_structure,
)
from core.structure_liabilities import map_liabilities_to_structure, refine_liability_severity_by_exposure
from core.structure_parser import build_residue_table, extract_protein_residues, load_structure
from core.structure_pymol_render import run_pymol_render
from core.structure_viewer import build_pymol_hotspot_snippet

from config import TOP_N_SUGGESTIONS


def _json_safe_rows(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        x = dict(r)
        c = x.get("centroid")
        if hasattr(c, "tolist"):
            x["centroid"] = c.tolist()
        coord = x.get("coord")
        if hasattr(coord, "tolist"):
            x["coord"] = coord.tolist()
        out.append(x)
    return out


def analyze_structure_context(
    sequence: str,
    structure_path: str | Path,
    chain_id: str | None,
    liabilities: list[dict[str, Any]],
    risk_regions: list[dict[str, Any]],
    mutation_suggestions: list[dict[str, Any]],
    mutation_impacts: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Returns a dict suitable for merging into `result` under key `structure_context`.
    On failure, returns {"ok": False, "error": str, ...}.
    """
    path = Path(structure_path)
    try:
        struct = load_structure(path)
    except Exception as e:
        return {"ok": False, "error": f"Parse error: {e}"}

    try:
        chain, residues = extract_protein_residues(struct, chain_id=chain_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    cid = chain.id
    table, seq_warnings = build_residue_table(residues, sequence)
    if not table:
        return {
            "ok": False,
            "error": "No mappable residues in structure.",
            "warnings": seq_warnings,
        }

    table = enrich_residue_table_with_coords(residues, table)
    table = compute_residue_exposure(table)
    table = apply_exposure_classification(table)

    hotspots = identify_structural_hotspots(table)
    mwn = find_exposed_mwn(table)

    mapped = map_liabilities_to_structure(liabilities, table)
    mapped_refined = refine_liability_severity_by_exposure(mapped)

    integration = integrate_sequence_and_structure(
        risk_regions,
        liabilities,
        table,
        hotspots,
        mapped_refined,
        seq_warnings,
    )

    mut_sugg_adj = adjust_mutations_for_structure(mutation_suggestions, table)[:TOP_N_SUGGESTIONS]
    mut_imp_adj = adjust_mutations_for_structure(mutation_impacts, table)

    pymol_snippet = build_pymol_hotspot_snippet(cid, hotspots)
    png_full, pml_err = run_pymol_render(
        path,
        str(cid),
        hotspots,
        mapped_refined,
    )

    return {
        "ok": True,
        "chain_id": cid,
        "residue_table": _json_safe_rows(table),
        "structural_hotspots": hotspots,
        "exposed_mwn": mwn,
        "liabilities_mapped": mapped_refined,
        "integration": integration,
        "mutation_suggestions_structure": mut_sugg_adj,
        "mutation_impacts_structure": mut_imp_adj,
        "pymol_png_full": png_full,
        "pymol_render_error": pml_err,
        "pymol_snippet": pymol_snippet,
        "warnings": seq_warnings,
    }
