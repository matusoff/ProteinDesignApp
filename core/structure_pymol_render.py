"""
Headless PyMOL: render a single full-structure PNG (cartoon + hotspot / liability highlights).

Requires PyMOL on PATH (e.g. conda install -c conda-forge pymol-open-source).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

_HOTSPOT_COLORS = [
    "tv_red",
    "tv_orange",
    "tv_green",
    "tv_blue",
    "magenta",
    "yellow",
    "salmon",
    "pink",
]
_LIABILITY_COLOR = "tv_blue"


def find_pymol_executable() -> str | None:
    """Resolve PyMOL: config/env path, PATH, CONDA_PREFIX, then Python prefix (conda base/env)."""
    from config import PYMOL_EXECUTABLE

    if PYMOL_EXECUTABLE:
        p = Path(PYMOL_EXECUTABLE)
        if p.is_file():
            return str(p.resolve())

    for name in (
        "pymol",
        "pymol2",
        "PyMOL",
        "pymol.exe",
        "pymol.cmd",
        "pymol.bat",
        "PyMOLWin",
        "PyMOLWin.exe",
    ):
        w = shutil.which(name)
        if w:
            return w

    def _scan_scripts(base: Path) -> str | None:
        for rel in (
            ("Scripts", "pymol.bat"),
            ("Scripts", "pymol.cmd"),
            ("Scripts", "pymol.exe"),
            ("Library", "bin", "pymol.exe"),
            ("bin", "pymol"),
        ):
            c = base.joinpath(*rel)
            if c.is_file():
                return str(c.resolve())
        return None

    cp = os.environ.get("CONDA_PREFIX", "").strip()
    if cp:
        hit = _scan_scripts(Path(cp))
        if hit:
            return hit

    for prefix in (getattr(sys, "base_prefix", "") or "", sys.prefix or ""):
        if not prefix:
            continue
        hit = _scan_scripts(Path(prefix))
        if hit:
            return hit

    return None


def _p(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def _chain_part(chain_id: str) -> str:
    c = str(chain_id).strip()
    if not c:
        return 'chain ""'
    return f"chain {c}"


def build_render_pml(
    structure_path: Path,
    chain_id: str,
    hotspots: list[dict[str, Any]],
    liabilities_mapped: list[dict[str, Any]],
    out_dir: Path,
    full_name: str = "structure_full.png",
) -> str:
    """Classic PyMOL command script (.pml), single PNG output."""
    cp = _chain_part(chain_id)
    sp = _p(structure_path)
    full_png = _p(out_dir / full_name)

    lines: list[str] = [
        "reinitialize",
        f'load "{sp}", mol',
        "hide everything",
        "show cartoon, mol",
        "color grey, mol",
        "bg_color white",
        "set ray_opaque_background, 0",
        "set antialias, 2",
        "set cartoon_smooth_loops, 0",
        "",
    ]

    created_hp: list[str] = []
    for i, h in enumerate(hotspots, start=1):
        rs = h.get("pdb_resseq") or []
        rs = sorted({int(x) for x in rs if int(x) > 0})
        if not rs:
            continue
        joined = "+".join(str(x) for x in rs)
        sel = f"hp{i}"
        created_hp.append(sel)
        lines.append(f"select {sel}, mol and {cp} and resi {joined}")
        col = _HOTSPOT_COLORS[(i - 1) % len(_HOTSPOT_COLORS)]
        lines.append(f"color {col}, {sel}")
        lines.append(f"show sticks, {sel}")
        lines.append(f"set stick_radius, 0.18, {sel}")

    for j, li in enumerate(liabilities_mapped, start=1):
        if li.get("structure_exposure") != "exposed":
            continue
        pr = li.get("pdb_resseq")
        if pr is None:
            continue
        sel = f"liab{j}"
        lines.append(f"select {sel}, mol and {cp} and resi {int(pr)}")
        lines.append(f"color {_LIABILITY_COLOR}, {sel}")
        lines.append(f"show spheres, {sel}")
        lines.append(f"set sphere_scale, 0.32, {sel}")

    lines.extend(
        [
            "",
            "zoom mol",
            "orient mol",
            f"png {full_png}, width=1200, height=800, dpi=150",
            "",
            "quit",
            "",
        ]
    )
    return "\n".join(lines)


def run_pymol_render(
    structure_path: str | Path,
    chain_id: str,
    hotspots: list[dict[str, Any]],
    liabilities_mapped: list[dict[str, Any]],
) -> tuple[str | None, str | None]:
    """Returns (png_full_path, error_message)."""
    structure_path = Path(structure_path)
    exe = find_pymol_executable()
    out_dir = Path(tempfile.mkdtemp(prefix="pda_pymol_"))
    full_png = out_dir / "structure_full.png"

    pml_text = build_render_pml(
        structure_path,
        chain_id,
        hotspots,
        liabilities_mapped,
        out_dir,
        full_name=full_png.name,
    )

    if not exe:
        return (
            None,
            "PyMOL not detected — use the interactive viewer or the copy-paste snippet. "
            "For an offline PNG, install PyMOL and ensure it is on PATH or set env PYMOL_EXECUTABLE.",
        )

    pml_path = out_dir / "render.pml"
    pml_path.write_text(pml_text, encoding="utf-8")

    kwargs: dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "timeout": 300,
        "cwd": str(out_dir),
    }
    if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        r = subprocess.run([exe, "-cq", str(pml_path)], **kwargs)
    except subprocess.TimeoutExpired:
        return None, "PyMOL timed out."
    except OSError:
        return None, "PyMOL failed to start."

    if r.returncode != 0:
        return None, "PyMOL render failed (non-zero exit)."

    if not full_png.is_file():
        return None, "PyMOL ran but no PNG was produced."

    return str(full_png), None
