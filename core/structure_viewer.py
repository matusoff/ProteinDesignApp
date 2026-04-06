"""Structure view helpers: interactive HTML + PyMOL/ChimeraX snippet."""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path


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


def build_interactive_structure_html(
    structure_path: str | Path,
    chain_id: str,
    hotspots: list[dict],
    mapped_liabilities: list[dict],
) -> str:
    """
    Build a 3Dmol.js viewer for uploaded PDB/mmCIF.

    Gradio injects callback HTML with innerHTML, which does **not** run inline
    ``<script>`` tags. We embed a full mini-page in an ``iframe`` via a data:
    URL so 3Dmol initializes correctly.

    - Cartoon backbone in neutral grey
    - Hydrophobic hotspot residues as red sticks
    - Exposed liabilities as blue spheres
    """
    p = Path(structure_path)
    if not p.is_file():
        return "<p style='color:#b91c1c;'>Structure file not found for 3D view.</p>"

    suffix = p.suffix.lower()
    model_fmt = "pdb" if suffix == ".pdb" else "mmcif"
    try:
        model_text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"<p style='color:#b91c1c;'>Could not read structure for 3D view: {html.escape(str(e))}</p>"

    hotspot_residues: list[int] = []
    for h in hotspots or []:
        for resi in h.get("pdb_resseq") or []:
            try:
                x = int(resi)
            except Exception:
                continue
            if x > 0:
                hotspot_residues.append(x)
    hotspot_residues = sorted(set(hotspot_residues))

    liability_residues: list[int] = []
    for li in mapped_liabilities or []:
        if li.get("structure_exposure") != "exposed":
            continue
        try:
            x = int(li.get("pdb_resseq"))
        except Exception:
            continue
        if x > 0:
            liability_residues.append(x)
    liability_residues = sorted(set(liability_residues))

    # Avoid huge data: URLs (browser limits vary; ~1–2 MB is a safe ceiling).
    b64_model = base64.b64encode(model_text.encode("utf-8")).decode("ascii")
    if len(b64_model) > 1_800_000:
        return (
            "<p style='color:#b45309;padding:12px;border:1px solid #fdba74;border-radius:8px;background:#fffbeb;'>"
            "Structure file is too large for the inline 3D viewer in the browser. "
            "Use a smaller coordinate file, or open the PDB/mmCIF locally (PyMOL / ChimeraX snippet below).</p>"
        )

    chain = (chain_id or "").strip() or "A"
    fmt_js = json.dumps(model_fmt)
    chain_js = json.dumps(chain)
    hotspot_js = json.dumps(hotspot_residues)
    liab_js = json.dumps(liability_residues)

    # Script runs inside iframe — model as base64 avoids breaking </script> in PDB text.
    inner_page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<script src="https://3Dmol.org/build/3Dmol-min.js"></script>
<style>html,body{{margin:0;height:100%;background:#fff;}}</style>
</head><body>
<div id="pda3d" style="width:100%;height:460px;"></div>
<script>
(function() {{
  function go() {{
    var el = document.getElementById("pda3d");
    if (!el) return;
    if (typeof $3Dmol === "undefined") {{
      setTimeout(go, 30);
      return;
    }}
    var modelData = atob({json.dumps(b64_model)});
    var fmt = {fmt_js};
    var chain = {chain_js};
    var hotspotResi = {hotspot_js};
    var liabResi = {liab_js};
    var viewer = $3Dmol.createViewer(el, {{ backgroundColor: "white" }});
    viewer.addModel(modelData, fmt);
    viewer.setStyle({{ chain: chain }}, {{ cartoon: {{ color: "#94a3b8", opacity: 0.95 }} }});
    if (hotspotResi.length) {{
      viewer.setStyle(
        {{ chain: chain, resi: hotspotResi }},
        {{ stick: {{ color: "#dc2626", radius: 0.2 }} }}
      );
    }}
    if (liabResi.length) {{
      viewer.addStyle(
        {{ chain: chain, resi: liabResi }},
        {{ sphere: {{ color: "#2563eb", radius: 0.85, opacity: 0.85 }} }}
      );
    }}
    viewer.zoomTo();
    viewer.render();
  }}
  go();
}})();
</script>
</body></html>"""

    page_b64 = base64.b64encode(inner_page.encode("utf-8")).decode("ascii")
    data_url = f"data:text/html;charset=utf-8;base64,{page_b64}"

    return (
        "<div style='border:1px solid #e2e8f0;border-radius:12px;padding:10px;background:#ffffff;'>"
        f'<iframe title="3D structure" sandbox="allow-scripts allow-same-origin" '
        f'src="{html.escape(data_url, quote=True)}" '
        'style="width:100%;height:460px;border:0;display:block;border-radius:8px;"></iframe>'
        "<div style='margin-top:8px;font-size:12px;color:#334155;'>"
        "<strong>3D legend:</strong> grey cartoon backbone; red sticks = hydrophobic hotspot residues; "
        "blue spheres = exposed liability residues."
        "</div>"
        "</div>"
    )
