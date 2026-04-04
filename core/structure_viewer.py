"""PyMOL / ChimeraX copy-paste snippet for structure hotspots (PNG render lives in `structure_pymol_render`)."""

from __future__ import annotations


def build_pymol_hotspot_snippet(chain_id: str, hotspots: list[dict]) -> str:
    """Compact PyMOL commands (hotspot patches only) — copy/paste friendly."""
    ch = (chain_id or "A").strip() or "A"
    lines = [
        "# PyMOL — hydrophobic surface patches (red sticks). PDB residue numbers.",
        "hide everything",
        "show cartoon",
        "color silver, all",
    ]
    for i, h in enumerate(hotspots, 1):
        rs = h.get("pdb_resseq") or []
        rs = sorted({int(x) for x in rs if int(x) > 0})
        if len(rs) < 2:
            continue
        joined = "+".join(str(x) for x in rs)
        lines.append(f"select hp{i}, chain {ch} and resi {joined}")
        lines.append(f"color tv_red, hp{i}")
        lines.append(f"show sticks, hp{i}")
    if len(lines) <= 4:
        lines.append("# (No multi-residue patches — check structure-mapped liabilities in the table.)")
    else:
        lines.append("orient visible")
    return "\n".join(lines)
