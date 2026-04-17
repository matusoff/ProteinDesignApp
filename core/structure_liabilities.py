"""
Map sequence liabilities onto structure rows and refine severity by exposure.
"""

from __future__ import annotations

from typing import Any


def map_liabilities_to_structure(
    liabilities: list[dict[str, Any]],
    residue_table: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_pos: dict[int, dict[str, Any]] = {int(r["seq_index"]): r for r in residue_table}
    out: list[dict[str, Any]] = []
    for li in liabilities:
        pos = int(li["position"])
        row = by_pos.get(pos)
        m = dict(li)
        if row:
            m["structure_exposure"] = row.get("exposure_class", "unknown")
            m["pdb_resseq"] = row.get("pdb_resseq")
            m["neighbor_count_10A"] = row.get("neighbor_count_10A")
            m["dist_to_ca_centroid_A"] = row.get("dist_to_ca_centroid_A")
            m["radial_shell_percentile"] = row.get("radial_shell_percentile")
        else:
            m["structure_exposure"] = "unmapped"
            m["pdb_resseq"] = None
            m["dist_to_ca_centroid_A"] = None
            m["radial_shell_percentile"] = None
        out.append(m)
    return out


def refine_liability_severity_by_exposure(mapped_liabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for m in mapped_liabilities:
        x = dict(m)
        exp = x.get("structure_exposure")
        sev = str(x.get("severity", "medium"))
        note = ""
        if exp == "exposed":
            if sev == "low":
                x["severity_structure_adjusted"] = "medium"
            else:
                x["severity_structure_adjusted"] = sev
            note = "Exposed site — higher visibility to solvent / processing."
        elif exp == "buried":
            x["severity_structure_adjusted"] = sev
            note = "Buried site — may be partially shielded in fold (still consider context)."
        else:
            x["severity_structure_adjusted"] = sev
        if note:
            x["structure_note"] = note
        out.append(x)
    return out
