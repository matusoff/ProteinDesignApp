"""
HTML snippets for a richer Gradio UI (cards, sequence risk strip).
"""

from __future__ import annotations

import html
from typing import Any


def _badge(label: str, value: str, tone: str) -> str:
    bg = {
        "ok": "#e8f5e9",
        "warn": "#fff8e1",
        "bad": "#ffebee",
        "neutral": "#f5f5f5",
    }.get(tone, "#f5f5f5")
    border = {
        "ok": "#a5d6a7",
        "warn": "#ffe082",
        "bad": "#ef9a9a",
        "neutral": "#e0e0e0",
    }.get(tone, "#e0e0e0")
    esc_label = html.escape(label)
    esc_val = html.escape(value)
    return (
        f'<div style="flex:1;min-width:120px;padding:12px 14px;border-radius:10px;'
        f'background:{bg};border:1px solid {border};">'
        f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:0.06em;'
        f'color:#616161;margin-bottom:4px;">{esc_label}</div>'
        f'<div style="font-size:18px;font-weight:600;color:#212121;">{esc_val}</div>'
        f"</div>"
    )


def _tone_from_label(label: str) -> str:
    t = (label or "").lower()
    if "low" in t:
        return "ok"
    if "medium" in t:
        return "warn"
    if "high" in t:
        return "bad"
    return "neutral"


def _mutation_label_text(x: Any) -> str | None:
    if x is None:
        return None
    s = str(x).strip()
    return s if s else None


def _sort_by_disruption_then_benefit(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: (r.get("disruption_risk", 99), -float(r.get("benefit_score", -99.0) or 0.0)))


def _sort_by_benefit_then_disruption(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: (-float(r.get("benefit_score", -99.0) or 0.0), r.get("disruption_risk", 99)))


def build_executive_summary_html(result: dict[str, Any]) -> str:
    name = html.escape(result.get("sequence_name") or "Construct")
    ln = len(result.get("sequence") or "")
    scores = result.get("scores") or {}
    overall = scores.get("overall", {})
    agg = scores.get("aggregation", {})
    sol = scores.get("solubility", {})
    chem = scores.get("chemical", {})
    ds = result.get("decision_summary") or {}
    dom = ds.get("dominant_region")

    badges = "".join(
        [
            _badge("Overall", str(overall.get("label", "—")), _tone_from_label(str(overall.get("label", "")))),
            _badge("Aggregation", str(agg.get("label", "—")), _tone_from_label(str(agg.get("label", "")))),
            _badge("Solubility", str(sol.get("label", "—")), _tone_from_label(str(sol.get("label", "")))),
            _badge("Chemical", str(chem.get("label", "—")), _tone_from_label(str(chem.get("label", "")))),
        ]
    )

    hotspot = ""
    if dom:
        ev = dom.get("evidence") or {}
        hotspot = (
            f"<div style='margin-top:14px;padding:12px 14px;border-radius:10px;"
            f"background:#e3f2fd;border:1px solid #90caf9;'>"
            f"<div style='font-size:11px;text-transform:uppercase;color:#1565c0;letter-spacing:0.05em;'>"
            f"Primary focus region</div>"
            f"<div style='font-size:15px;font-weight:600;color:#0d47a1;margin-top:4px;'>"
            f"{dom['start']}–{dom['end']}</div>"
            f"<div style='font-size:13px;color:#37474f;margin-top:6px;line-height:1.45;'>"
            f"{html.escape(str(dom.get('reason_summary', '')))}</div>"
            f"</div>"
        )

    # CONSERVATIVE / STRONGER: heuristic “less disruptive” vs “more benefit” picks from
    # patch-breaking suggestions (see core/decision_engine.py). Not physics — exploratory only.
    safer = _mutation_label_text(ds.get("safer_option"))
    stronger = _mutation_label_text(ds.get("stronger_option"))

    # Fallback when decision_engine could not pair options (e.g. dominant region is not
    # hydrophobic_cluster so patch-breaking list is empty there). Use full impact list, then table shortlist.
    if not safer or not stronger:
        impacts = result.get("mutation_impacts") or []
        if impacts:
            by_d = _sort_by_disruption_then_benefit(impacts)
            by_b = _sort_by_benefit_then_disruption(impacts)
            safer = safer or _mutation_label_text(by_d[0].get("mutation"))
            stronger = stronger or _mutation_label_text(by_b[0].get("mutation"))
            if safer == stronger and len(by_b) > 1:
                stronger = _mutation_label_text(by_b[1].get("mutation"))
    if not safer or not stronger:
        sugg = result.get("mutation_suggestions") or []
        if sugg:
            by_d = _sort_by_disruption_then_benefit(sugg)
            by_b = _sort_by_benefit_then_disruption(sugg)
            safer = safer or _mutation_label_text(by_d[0].get("mutation"))
            stronger = stronger or _mutation_label_text(by_b[0].get("mutation"))
            if safer == stronger and len(by_b) > 1:
                stronger = _mutation_label_text(by_b[1].get("mutation"))

    opts = ""
    mut_span = (
        'style="display:inline-block;margin-top:6px;font-family:ui-monospace,Consolas,monospace;'
        'font-size:15px;font-weight:600;color:#0f172a;line-height:1.4;"'
    )
    if safer or stronger:
        s_disp = html.escape(safer) if safer else "(none)"
        t_disp = html.escape(stronger) if stronger else "(none)"
        opts = (
            f"<div style='margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;'>"
            f"<div style='flex:1;min-width:200px;padding:10px 12px;border-radius:8px;background:#f1f8e9;border:1px solid #c5e1a5;'>"
            f"<span style='font-size:11px;color:#558b2f;font-weight:600;'>CONSERVATIVE</span><br/>"
            f"<span {mut_span}>{s_disp}</span></div>"
            f"<div style='flex:1;min-width:200px;padding:10px 12px;border-radius:8px;background:#fff3e0;border:1px solid #ffcc80;'>"
            f"<span style='font-size:11px;color:#e65100;font-weight:600;'>STRONGER</span><br/>"
            f"<span {mut_span}>{t_disp}</span></div>"
            f"</div>"
            f"<p style='margin:8px 0 0 0;font-size:12px;color:#94a3b8;line-height:1.45;'>"
            "<strong>Conservative</strong> = lowest modeled disruption risk among ranked suggestions; "
            "<strong>Stronger</strong> = highest modeled benefit score (local metrics / liabilities). "
            "Heuristic only — confirm in structure and assays.</p>"
        )
    elif dom:
        opts = (
            "<p style='margin:12px 0 0 0;font-size:13px;color:#94a3b8;line-height:1.45;'>"
            "No mutation pair to highlight for this run (no ranked suggestions). "
            "See <strong>Mutation impacts</strong> / <strong>Top suggestions</strong> tables below if present.</p>"
        )

    return (
        f"<div style='font-family:system-ui,-apple-system,sans-serif;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;'>"
        f"<div style='font-size:20px;font-weight:700;color:#f8fafc;'>{name}</div>"
        f"<div style='font-size:13px;color:#94a3b8;'>{ln} aa · schema v{html.escape(str(result.get('version','')))}</div>"
        f"</div>"
        f"<div style='display:flex;gap:10px;margin-top:14px;flex-wrap:wrap;'>{badges}</div>"
        f"{hotspot}"
        f"{opts}"
        f"</div>"
    )


def _severity_style(risk_type: str, severity: str) -> tuple[str, str]:
    """Return (bg, border) for residue cell."""
    sev = (severity or "").lower()
    if risk_type == "hydrophobic_cluster":
        if sev == "high":
            return "#c62828", "#b71c1c"
        return "#ef9a9a", "#e57373"
    if risk_type == "aromatic_cluster":
        return "#ce93d8", "#8e24aa"
    if risk_type == "charge_patch":
        return "#90caf9", "#1565c0"
    if risk_type == "low_complexity":
        # Brown/tan — distinct from liability orange (#ffe0b2) and from charge blue
        return "#d7ccc8", "#5d4037"
    return "#ffffff", "#e0e0e0"


def _priority_for_cell(risk_type: str, severity: str) -> int:
    sev = (severity or "").lower()
    base = {
        "hydrophobic_cluster": 40,
        "aromatic_cluster": 35,
        "charge_patch": 30,
        "low_complexity": 20,
    }.get(risk_type, 10)
    if sev == "high":
        base += 3
    elif sev == "medium":
        base += 2
    else:
        base += 1
    return base


def build_sequence_risk_map_html(
    seq: str,
    risk_regions: list[dict[str, Any]],
    liabilities: list[dict[str, Any]],
    protected_positions: set[int],
    line_width: int = 60,
) -> str:
    if not seq:
        return "<p style='color:#666;'>No sequence.</p>"

    n = len(seq)
    best: list[tuple[int, str, str, str]] = [(0, "#ffffff", "#e0e0e0", "") for _ in range(n)]

    for r in risk_regions:
        s, e = int(r["start"]), int(r["end"])
        rt = str(r.get("risk_type", ""))
        sev = str(r.get("severity", ""))
        bg, bd = _severity_style(rt, sev)
        pr = _priority_for_cell(rt, sev)
        for j in range(s - 1, min(e, n)):
            if pr > best[j][0]:
                best[j] = (pr, bg, bd, rt)

    for li in liabilities:
        p = int(li["position"])
        if 1 <= p <= n:
            i = p - 1
            pr = 90
            if pr >= best[i][0]:
                best[i] = (pr, "#ffe0b2", "#ff6f00", "liability")

    for i in range(n):
        pos = i + 1
        if pos in protected_positions:
            # Was #eceff1 / #78909c — too pale on #fafafa
            best[i] = (100, "#c8e6c9", "#2e7d32", "protected")

    lines: list[str] = []
    for i in range(0, n, line_width):
        chunk_end = min(i + line_width, n)
        start_idx = i + 1
        cells: list[str] = []
        for j in range(i, chunk_end):
            aa = html.escape(seq[j])
            pr, bg, bd, _rt = best[j]
            cells.append(
                f"<span title='pos {j+1}' style='display:inline-block;width:12px;text-align:center;"
                f"padding:2px 0;margin:0 1px;border-radius:3px;background:{bg};"
                f"border-bottom:2px solid {bd};font-family:ui-monospace,monospace;font-size:12px;color:#000'"
                f">{aa}</span>"
            )
        line_html = "".join(cells)
        lines.append(
            f"<div style='display:flex;align-items:flex-start;gap:6px;margin:2px 0;'>"
            f"<span style='font-size:11px;color:#000;width:36px;text-align:right;flex-shrink:0;font-family:monospace;'>{start_idx}</span>"
            f"<div style='flex:1;overflow-x:auto;'>{line_html}</div>"
            f"</div>"
        )

    legend = (
        "<div style='display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:8px;font-size:11px;color:#000000 !important;'>"
        "<span style='color:#000000 !important;'><span style='display:inline-block;width:10px;height:10px;background:#c62828;border-radius:2px;vertical-align:middle;'></span> hydrophobic (high)</span>"
        "<span style='color:#000000 !important;'><span style='display:inline-block;width:10px;height:10px;background:#ef9a9a;border:1px solid #e57373;border-radius:2px;vertical-align:middle;'></span> hydrophobic (moderate)</span>"
        "<span style='color:#000000 !important;'><span style='display:inline-block;width:10px;height:10px;background:#8e24aa;border-radius:2px;vertical-align:middle;'></span> aromatic</span>"
        "<span style='color:#000000 !important;'><span style='display:inline-block;width:10px;height:10px;background:#1565c0;border-radius:2px;vertical-align:middle;'></span> charge patch</span>"
        "<span style='color:#000000 !important;'><span style='display:inline-block;width:10px;height:10px;background:#d7ccc8;border:1px solid #5d4037;border-radius:2px;vertical-align:middle;'></span> low complexity</span>"
        "<span style='color:#000000 !important;'><span style='display:inline-block;width:10px;height:10px;background:#ffe0b2;border-radius:2px;vertical-align:middle;'></span> liability</span>"
        "<span style='color:#000000 !important;'><span style='display:inline-block;width:10px;height:10px;background:#c8e6c9;border:1px solid #2e7d32;border-radius:2px;vertical-align:middle;'></span> protected</span>"
        "</div>"
    )

    return (
        f"<div style='font-family:system-ui,-apple-system,sans-serif;color:#000000 !important;'>"
        f"<div style='padding:8px 10px;border-radius:10px;border:1px solid #e0e0e0;background:#fafafa;color:#000000 !important;'>"
        f"{''.join(lines)}"
        f"{legend}"
        f"</div></div>"
    )


def build_structure_section_html(structure_context: dict[str, Any] | None) -> str:
    """Summary + PyMOL note + copy-paste snippet (PNG is shown in a separate `gr.Image`)."""
    if not structure_context:
        return (
            "<div style='color:#0a0a0a;font-size:14px;line-height:1.5;'>"
            "<p style='margin:0 0 8px 0;'><strong>What to do:</strong> (1) Paste the sequence that matches your model. "
            "(2) Under <em>Optional structure</em>, attach your <code style=\"background:#f1f5f9;padding:1px 4px;border-radius:3px;border:1px solid #e2e8f0;\">.pdb</code> / <code style=\"background:#f1f5f9;padding:1px 4px;border-radius:3px;border:1px solid #e2e8f0;\">.cif</code> file and set "
            "<strong>Chain ID</strong> if needed (blank = first chain). "
            "(3) Click <strong>Run review</strong>.</p>"
            "<p style='margin:0;'>The <strong>interactive 3D viewer</strong> above works in the browser. "
            "Optional <strong>PyMOL PNG</strong> and the script box below are for local use if PyMOL is not on the server.</p>"
            "</div>"
        )
    if not structure_context.get("ok"):
        err = html.escape(str(structure_context.get("error", "Unknown error")))
        return f"<div style='padding:12px;border-radius:8px;background:#ffebee;color:#b71c1c;'>{err}</div>"

    integ = structure_context.get("integration") or {}
    summary = html.escape(str(integ.get("summary_line", "")))
    warns = structure_context.get("warnings") or []
    warn_html = ""
    if warns:
        items = "".join(f"<li>{html.escape(str(w))}</li>" for w in warns)
        warn_html = (
            f"<ul style='margin:8px 0 0 16px;color:#0a0a0a;font-size:13px;'>{items}</ul>"
        )
    n_hp = len(structure_context.get("structural_hotspots") or [])
    chain = html.escape(str(structure_context.get("chain_id", "")))
    head = (
        f"<div style='font-size:14px;color:#0a0a0a;margin-bottom:8px;line-height:1.5;'>"
        f"<strong>Structure</strong> · chain <code style='background:#f1f5f9;padding:1px 6px;border-radius:3px;"
        f"border:1px solid #e2e8f0;color:#0a0a0a;'>{chain}</code> · "
        f"{n_hp} hydrophobic patch(es) (surface heuristic).<br/>"
        f"<span style='color:#0a0a0a;'>{summary}</span>{warn_html}"
        f"</div>"
    )

    lps = structure_context.get("liability_patch_stats") or {}
    patch_html = ""
    if lps.get("ok"):
        esc_disc = html.escape(str(lps.get("disclaimer", "")))
        esc_interp = html.escape(str(lps.get("interpretation", "")))
        ec = lps.get("exposure_counts") or {}
        exp_line = html.escape(
            f"At liability sites — exposed: {ec.get('exposed', 0)}, intermediate: {ec.get('intermediate', 0)}, "
            f"buried: {ec.get('buried', 0)} (from 10 Å neighbor tertiles on this chain)."
        )
        patch_html = (
            "<div style='margin:10px 0;padding:10px 12px;border-radius:10px;border:1px solid #94a3b8;"
            "background:#e2e8f0;color:#0a0a0a;font-size:13px;line-height:1.5;'>"
            "<strong>Liability patch (Cα geometry)</strong>"
            "<p style='margin:6px 0 4px 0;font-size:12px;color:#334155;'>" + esc_disc + "</p>"
            "<p style='margin:0 0 6px 0;'>" + esc_interp + "</p>"
            "<p style='margin:0;font-size:12px;color:#1e293b;'>" + exp_line + "</p>"
            "</div>"
        )
    elif lps.get("interpretation"):
        patch_html = (
            "<div style='margin:10px 0;padding:8px 10px;border-radius:8px;background:#f1f5f9;"
            "color:#0a0a0a;font-size:13px;'>" + html.escape(str(lps.get("interpretation", ""))) + "</div>"
        )

    png_path = structure_context.get("pymol_png_full") or ""
    has_png = bool(png_path)
    render_err = structure_context.get("pymol_render_error")

    status = ""
    if has_png:
        status = (
            "<p style='margin:0 0 8px 0;font-size:13px;color:#0a0a0a;'>"
            "PyMOL PNG available — expand <strong>PyMOL PNG render (server only)</strong> above to view it. "
            "(Same coloring as the interactive viewer: cartoon + hotspot sticks + exposed-liability spheres.)</p>"
        )
    elif render_err:
        status = (
            f"<p style='margin:0 0 8px 0;font-size:13px;color:#0a0a0a;background:#fff7ed;"
            f"padding:8px 10px;border-radius:8px;border:1px solid #fdba74;'>{html.escape(str(render_err))}</p>"
        )
    else:
        status = (
            "<p style='margin:0 0 8px 0;font-size:13px;color:#0a0a0a;'>"
            "No PyMOL PNG this run — use the <strong>interactive 3D viewer</strong> above, or the script below in PyMOL/ChimeraX locally.</p>"
        )

    legend = (
        "<p style='margin:0;font-size:13px;color:#0a0a0a;line-height:1.45;'>"
        "<strong>PyMOL PNG (when present):</strong> grey cartoon; colored sticks = hydrophobic patches; "
        "blue spheres = exposed liabilities (same idea as the 3D view).</p>"
    )

    pymol = (structure_context.get("pymol_snippet") or "").strip()
    pymol_html = ""
    if pymol:
        esc = html.escape(pymol)
        pymol_html = (
            "<details style='margin-top:12px;color-scheme:light;background:#e2e8f0;border-radius:8px;padding:10px 12px;"
            "border:1px solid #94a3b8;'>"
            "<summary style='cursor:pointer;font-weight:600;color:#0a0a0a;'>PyMOL / ChimeraX script</summary>"
            "<p style='font-size:13px;color:#0a0a0a;margin:8px 0;'>Copy into PyMOL or ChimeraX after loading your coordinates file.</p>"
            f"<pre style='white-space:pre-wrap;word-break:break-all;color:#0a0a0a !important;background:#f8fafc !important;"
            f"border:1px solid #64748b;border-radius:6px;padding:10px;font-size:12px;line-height:1.45;margin:0;"
            f"font-family:ui-monospace,Consolas,monospace;'>{esc}</pre>"
            "</details>"
        )

    return (
        f"<div style='font-family:system-ui,sans-serif;color:#0a0a0a;background:transparent;'>"
        f"{head}{patch_html}{status}{legend}{pymol_html}</div>"
    )
