"""
Geometry and simple exposure proxy from Cα (or centroid) neighbor counts.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def get_residue_centroid(residue) -> np.ndarray:
    atoms = list(residue.get_atoms())
    if not atoms:
        return np.zeros(3, dtype=np.float64)
    coords = np.array([a.coord for a in atoms], dtype=np.float64)
    return np.mean(coords, axis=0)


def get_ca_coord(residue) -> np.ndarray | None:
    for a in residue.get_atoms():
        if a.get_name() == "CA":
            return np.array(a.coord, dtype=np.float64)
    return None


def enrich_residue_table_with_coords(
    residues: list,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if len(residues) != len(rows):
        raise ValueError("residues and rows length mismatch")
    out = []
    for res, row in zip(residues, rows):
        r = dict(row)
        ca = get_ca_coord(res)
        if ca is not None:
            r["coord"] = ca
            r["centroid"] = ca
        else:
            c = get_residue_centroid(res)
            r["coord"] = c
            r["centroid"] = c
        out.append(r)
    return out


def compute_residue_exposure(rows: list[dict[str, Any]], radius: float = 10.0) -> list[dict[str, Any]]:
    """
    Neighbor count within `radius` Å of each Cα/centroid (excluding self).
    Higher count → more buried (simple proxy; not SASA).
    """
    if not rows:
        return []
    coords = np.array([r["centroid"] for r in rows], dtype=np.float64)
    n = len(coords)
    # NumPy only (no scipy): O(n^2); fine for typical chains.
    idx = np.arange(n)
    counts = np.zeros(n, dtype=np.int32)
    for i in range(n):
        d = np.linalg.norm(coords - coords[i], axis=1)
        counts[i] = int(np.sum((d <= radius) & (idx != i)))

    out = []
    for i, row in enumerate(rows):
        r = dict(row)
        r["neighbor_count_10A"] = int(counts[i])
        out.append(r)
    return out


def classify_exposure(neighbor_count: int, counts: np.ndarray) -> str:
    """Relative tertiles on the distribution."""
    if counts.size == 0:
        return "unknown"
    lo = np.percentile(counts, 33)
    hi = np.percentile(counts, 67)
    if neighbor_count <= lo:
        return "exposed"
    if neighbor_count >= hi:
        return "buried"
    return "intermediate"


def apply_exposure_classification(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    arr = np.array([r["neighbor_count_10A"] for r in rows], dtype=np.float64)
    out = []
    for r in rows:
        x = dict(r)
        x["exposure_class"] = classify_exposure(int(x["neighbor_count_10A"]), arr)
        out.append(x)
    return out
