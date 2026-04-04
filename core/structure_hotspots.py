"""
Surface-exposed hydrophobic patches in 3D (heuristic).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

# For aggregation-style surface concern
HYDROPHOBIC = set("AVILMFYW")
# M/W/N often flagged in developability
MWN = set("MWN")


def find_surface_hydrophobic_residues(residue_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits = []
    for r in residue_table:
        if r.get("exposure_class") != "exposed":
            continue
        aa = r.get("one_letter", "")
        if aa in HYDROPHOBIC:
            hits.append(dict(r))
    return hits


def _dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def cluster_surface_residues(
    residues: list[dict[str, Any]],
    cutoff: float = 8.0,
) -> list[list[dict[str, Any]]]:
    """Connected components: edges if centroid distance ≤ cutoff (single linkage–style)."""
    if not residues:
        return []
    pts = [np.array(r["centroid"], dtype=np.float64) for r in residues]
    n = len(residues)
    adj: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if _dist(pts[i], pts[j]) <= cutoff:
                adj[i].append(j)
                adj[j].append(i)

    seen = [False] * n
    clusters_idx: list[list[int]] = []
    for i in range(n):
        if seen[i]:
            continue
        stack = [i]
        comp: list[int] = []
        while stack:
            u = stack.pop()
            if seen[u]:
                continue
            seen[u] = True
            comp.append(u)
            for v in adj[u]:
                if not seen[v]:
                    stack.append(v)
        clusters_idx.append(comp)

    return [[dict(residues[i]) for i in grp] for grp in clusters_idx]


def score_hydrophobic_patch(cluster: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(cluster)
    mean_nb = sum(r.get("neighbor_count_10A", 0) for r in cluster) / max(n, 1)
    return {
        "size": n,
        "mean_neighbor_count_10A": round(mean_nb, 2),
        "score": round(n * math.log1p(mean_nb), 3),
    }


def find_exposed_mwn(residue_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in residue_table:
        if r.get("exposure_class") != "exposed":
            continue
        if r.get("one_letter") in MWN:
            out.append(dict(r))
    return out


def identify_structural_hotspots(residue_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    surface_h = find_surface_hydrophobic_residues(residue_table)
    groups = cluster_surface_residues(surface_h, cutoff=8.0)
    hotspots: list[dict[str, Any]] = []
    for i, grp in enumerate(groups, start=1):
        if len(grp) < 2:
            continue
        sc = score_hydrophobic_patch(grp)
        seq_positions = sorted({int(r["seq_index"]) for r in grp})
        hotspots.append(
            {
                "id": f"hpatch_{i}",
                "kind": "hydrophobic_surface_patch",
                "seq_positions": seq_positions,
                "pdb_resseq": [int(r["pdb_resseq"]) for r in grp],
                "size": sc["size"],
                "patch_score": sc["score"],
                "mean_neighbor_count_10A": sc["mean_neighbor_count_10A"],
            }
        )
    hotspots.sort(key=lambda x: -x["patch_score"])
    return hotspots
