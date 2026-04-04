import gradio as gr
from config import APP_TITLE, APP_SUBTITLE, APP_VERSION, RESULT_SCHEMA_VERSION
from data.example_sequences import DEMO_LABELS
from ui.callbacks import (
    run_analysis,
    run_compare,
    load_example_sequence,
    export_tables_zip_callback,
    export_report_txt_callback,
    run_structure_prediction,
)


def build_app_layout():
    with gr.Blocks(
        title=APP_TITLE,
        css="""
        .risk-map-wrap { max-height: min(380px, 42vh); overflow-y: auto; }

        /* Structure block: light panel on dark Gradio themes */
        .structure-view-panel {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            padding: 14px 18px 18px !important;
            margin: 10px 0 16px !important;
            color-scheme: light !important;
            color: #0a0a0a !important;
        }
        /* Force readable black copy (dark Gradio themes were washing out markdown/HTML here) */
        .structure-view-panel .prose,
        .structure-view-panel .prose p,
        .structure-view-panel .prose h1,
        .structure-view-panel .prose h2,
        .structure-view-panel .prose h3,
        .structure-view-panel .prose h4,
        .structure-view-panel .prose li,
        .structure-view-panel .prose strong,
        .structure-view-panel .prose em,
        .structure-view-panel .prose a,
        .structure-view-panel p,
        .structure-view-panel h1,
        .structure-view-panel h2,
        .structure-view-panel h3,
        .structure-view-panel li,
        .structure-view-panel strong,
        .structure-view-panel em,
        .structure-view-panel a {
            color: #0a0a0a !important;
        }
        .structure-view-panel .prose code,
        .structure-view-panel code {
            color: #0a0a0a !important;
            background: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
        }
        .structure-view-panel .label-wrap label,
        .structure-view-panel .label-wrap span {
            color: #0a0a0a !important;
        }
        .structure-view-panel [class*="md"] p,
        .structure-view-panel [class*="md"] h1,
        .structure-view-panel [class*="md"] h2,
        .structure-view-panel [class*="md"] h3,
        .structure-view-panel [class*="markdown"] {
            color: #0a0a0a !important;
        }
        .structure-view-panel .gr-image,
        .structure-view-panel .image-container,
        .structure-view-panel .wrap.center {
            background-color: #ffffff !important;
        }

        /* Dataframe: scroll container must clip here, not on <table> (hidden overflow on table breaks scroll + clips text) */
        .pda-table-wrap {
            overflow-x: auto !important;
            overflow-y: visible !important;
            max-width: 100% !important;
            -webkit-overflow-scrolling: touch;
        }
        .pda-table-wrap table {
            border-collapse: separate !important;
            border-spacing: 0 !important;
            width: 100% !important;
            table-layout: auto !important;
            border-radius: 10px !important;
            border: 1px solid #94a3b8 !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
        }
        .pda-table-wrap thead th {
            background: linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%) !important;
            color: #f8fafc !important;
            font-weight: 600 !important;
            padding: 10px 12px !important;
            text-align: left !important;
            border-bottom: 2px solid #1e3a8a !important;
            white-space: normal !important;
            word-break: break-word !important;
            vertical-align: top !important;
        }
        .pda-table-wrap tbody td {
            padding: 8px 12px !important;
            border-bottom: 1px solid #e2e8f0 !important;
            color: #0f172a !important;
            white-space: normal !important;
            word-break: break-word !important;
            overflow-wrap: anywhere !important;
            vertical-align: top !important;
        }
        .pda-table-wrap tbody tr:nth-child(even) td {
            background-color: #eff6ff !important;
        }
        .pda-table-wrap tbody tr:nth-child(odd) td {
            background-color: #ffffff !important;
        }
        .pda-table-wrap tbody tr:hover td {
            background-color: #bfdbfe !important;
        }

        .pda-table-wrap.pda-df-risk thead th {
            background: linear-gradient(180deg, #f59e0b 0%, #d97706 100%) !important;
            border-bottom-color: #b45309 !important;
        }
        .pda-table-wrap.pda-df-liab thead th {
            background: linear-gradient(180deg, #a855f7 0%, #7c3aed 100%) !important;
            border-bottom-color: #5b21b6 !important;
        }
        .pda-table-wrap.pda-df-mut thead th {
            background: linear-gradient(180deg, #0d9488 0%, #0f766e 100%) !important;
            border-bottom-color: #115e59 !important;
        }
        .pda-table-wrap.pda-df-gained thead th {
            background: linear-gradient(180deg, #22c55e 0%, #15803d 100%) !important;
            border-bottom-color: #166534 !important;
        }
        .pda-table-wrap.pda-df-lost thead th {
            background: linear-gradient(180deg, #fb7185 0%, #e11d48 100%) !important;
            border-bottom-color: #be123c !important;
        }
        """,
    ) as demo:
        gr.Markdown(f"# {APP_TITLE}")
        gr.Markdown(APP_SUBTITLE)
        gr.Markdown(
            f'<p style="margin:0;color:#64748b;font-size:14px;">Version <code>{APP_VERSION}</code> · '
            f'Data schema <code>{RESULT_SCHEMA_VERSION}</code> · '
            f"Expand <strong>About this prototype</strong> for capabilities and limits.</p>"
        )

        with gr.Accordion("About this prototype (read first)", open=True):
            gr.Markdown(
                """
### What this app does (today)

- **Flags** sequence-level chemical liabilities (rule-based heuristics)
- **Highlights** local risk regions (hydrophobic clusters, charge patches, aromatics, low complexity)
- **Proposes** first-pass mutation hypotheses with simple simulated local metrics
- **Exports** tables + JSON (ZIP) and a full-text report (TXT)
- **Optional structure:** upload **PDB / mmCIF** that matches your sequence for structure-aware mapping; a **PyMOL PNG** appears only if PyMOL is installed on the server running the app (many public hosts will not have it)

### What it does *not* claim

- **Not** a validated predictor of experimental developability, solubility, or aggregation
- **Heuristic / prototype** logic — use for **exploratory review** only
- **Mutation suggestions** must be judged in structural and functional context by experts

### Public demo note

Use **Load demo** to try packaged examples, or paste your own FASTA / raw sequence. Keep coordinate files reasonably small; very large uploads may fail or time out on shared hosting.

---

**Use for exploratory review, not as a substitute for experimental validation.** See the project `DISCLAIMER.md` on GitHub for full disclaimer text.
"""
            )

        analysis_state = gr.State(value=None)
        compare_state = gr.State(value=None)
        session_state = gr.State(value={"history": []})

        with gr.Tabs():
            with gr.Tab("Review", id="tab_review"):
                gr.Markdown("### Input")
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1):
                        sequence_input = gr.Textbox(
                            label="Sequence or FASTA",
                            lines=11,
                            placeholder="Paste sequence or FASTA...",
                        )
                        seq_name_input = gr.Textbox(
                            label="Construct name",
                            value="",
                            placeholder="Optional",
                        )
                        protected_input = gr.Textbox(
                            label="Locked residues (no mutation suggestions)",
                            placeholder="e.g. 23-41, 98, 101",
                        )
                        sequence_map_style = gr.Dropdown(
                            label="Numbered sequence format",
                            choices=[
                                ("20 aa / line", "blocks_20"),
                                ("50 aa / line · groups of 10", "50_ten_groups"),
                            ],
                            value="blocks_20",
                        )
                        demo_sequence = gr.Dropdown(
                            label="Demo sequence",
                            choices=DEMO_LABELS,
                            value="hcv",
                        )
                        with gr.Row():
                            analyze_btn = gr.Button("Run review", variant="primary", scale=1)
                            example_btn = gr.Button("Load demo", scale=1)
                        gr.Markdown(
                            "<small>Loads selected FASTA into the sequence box. "
                            "If you add matching <code>.cif</code>/<code>.mmcif</code> under "
                            "<code>data/structures/</code> (see <code>README.txt</code> there), "
                            "coordinates are attached too — then click <strong>Run review</strong>.</small>"
                        )

                        gr.Markdown("#### Optional structure (PDB / mmCIF)")
                        structure_file = gr.File(
                            label="Coordinates",
                            file_types=[".pdb", ".cif", ".mmcif"],
                        )
                        structure_chain = gr.Textbox(
                            label="Chain ID",
                            value="",
                            placeholder="Blank = first chain",
                        )
                        gr.Markdown(
                            "<small>Must match the sequence above (AF3 / AlphaFold models from the same sequence work best). "
                            "After upload, click <strong>Run review</strong> — results appear in this tab, including "
                            "<strong>Structure-aware view</strong> below.</small>"
                        )

                gr.Markdown(
                    "### At a glance\n\n"
                    "<p style='margin:0 0 10px 0;color:#64748b;font-size:14px;'>"
                    "Summary scores and primary hotspot — updates when you click <strong>Run review</strong> "
                    "(natural next step: scroll here from the inputs above, then the risk map below).</p>"
                )
                executive_card = gr.HTML(
                    value="<p style='color:#94a3b8;'>Run review to see scores and primary hotspot.</p>"
                )

                gr.Markdown("### Sequence risk map")
                risk_map_html = gr.HTML(
                    value="<p style='color:#94a3b8;'>Residue coloring by scanner flags (see legend below map).</p>",
                    elem_classes=["risk-map-wrap"],
                )

                insights_md = gr.Markdown(
                    value="**Insights** will appear after the first run.",
                )

                gr.Markdown("### Hydrophobicity (sliding window)")
                hydro_plot = gr.Plot(label="KD mean · window")

                with gr.Column(elem_classes=["structure-view-panel"]):
                    gr.HTML(
                        value=(
                            "<h3 style='margin:0 0 10px 0;font-size:1.15rem;font-weight:700;color:#0a0a0a;'>"
                            "Structure-aware view (optional upload)</h3>"
                            "<p style='margin:0;line-height:1.55;font-size:14px;color:#0a0a0a;'>"
                            "With <strong>PyMOL</strong> on the server, the app renders a <strong>PNG</strong> "
                            "(cartoon + hotspot sticks + exposed-liability spheres). "
                            "Use the <strong>PyMOL / ChimeraX</strong> box below to reproduce the same view locally."
                            "</p>"
                        )
                    )
                    structure_image = gr.Image(
                        label="Structure (PyMOL render)",
                        type="filepath",
                        interactive=False,
                        height=420,
                    )
                    structure_panel = gr.HTML(
                        value="<p style='color:#0a0a0a;'>Attach coordinates in the input column, then run review.</p>",
                    )

                with gr.Accordion("Physicochemical snapshot", open=False):
                    global_df = gr.Dataframe(
                        label="Metrics",
                        wrap=True,
                        elem_classes=["pda-table-wrap", "pda-df-global"],
                    )

                with gr.Accordion("Raw scanner spans", open=False):
                    risk_df = gr.Dataframe(
                        label="Hits",
                        wrap=True,
                        elem_classes=["pda-table-wrap", "pda-df-risk"],
                    )

                with gr.Accordion("Chemical liabilities", open=False):
                    liabilities_df = gr.Dataframe(
                        label="Sites",
                        wrap=True,
                        elem_classes=["pda-table-wrap", "pda-df-liab"],
                    )

                with gr.Accordion("Region diagnostics", open=False):
                    region_analysis_df = gr.Dataframe(
                        label="Evidence",
                        wrap=True,
                        elem_classes=["pda-table-wrap", "pda-df-region"],
                    )

                with gr.Accordion("Mutation impacts (simulated local metrics)", open=True):
                    mutation_impact_df = gr.Dataframe(
                        label="Candidates",
                        wrap=True,
                        elem_classes=["pda-table-wrap", "pda-df-mut"],
                    )

                with gr.Accordion("Top suggestions (compact)", open=True):
                    mutations_df = gr.Dataframe(
                        label="Short list",
                        wrap=True,
                        elem_classes=["pda-table-wrap", "pda-df-mut"],
                    )

                with gr.Accordion("Numbered sequence (find positions)", open=False):
                    sequence_map_code = gr.Code(
                        label="1-based index",
                        language=None,
                        interactive=False,
                        lines=18,
                    )

                with gr.Accordion("Full text report", open=False):
                    report_output = gr.Code(
                        label="Full text report",
                        language=None,
                        interactive=False,
                        lines=16,
                    )

                gr.Markdown("#### Export")
                with gr.Row():
                    export_zip_btn = gr.Button("Tables + JSON (ZIP)")
                    export_txt_btn = gr.Button("Report (TXT)")
                export_zip_file = gr.File(label="ZIP")
                export_txt_file = gr.File(label="TXT")

                with gr.Accordion("Structure (optional · local ESMFold)", open=False):
                    gr.Markdown(
                        "Requires `pip install -r requirements-structure.txt`. First run downloads weights; **GPU** recommended."
                    )
                    predict_structure_btn = gr.Button("Predict structure")
                    structure_status = gr.Markdown()
                    structure_pdb = gr.File(label="PDB")
                    structure_view = gr.HTML(label="Viewer")

                analyze_btn.click(
                    fn=run_analysis,
                    inputs=[
                        sequence_input,
                        seq_name_input,
                        protected_input,
                        sequence_map_style,
                        session_state,
                        structure_file,
                        structure_chain,
                    ],
                    outputs=[
                        executive_card,
                        risk_map_html,
                        insights_md,
                        global_df,
                        risk_df,
                        liabilities_df,
                        region_analysis_df,
                        mutation_impact_df,
                        mutations_df,
                        hydro_plot,
                        report_output,
                        sequence_map_code,
                        analysis_state,
                        session_state,
                        structure_image,
                        structure_panel,
                    ],
                )

                example_btn.click(
                    fn=load_example_sequence,
                    inputs=[demo_sequence],
                    outputs=[sequence_input, structure_file],
                )

                export_zip_btn.click(
                    fn=export_tables_zip_callback,
                    inputs=[analysis_state],
                    outputs=[export_zip_file],
                )

                export_txt_btn.click(
                    fn=export_report_txt_callback,
                    inputs=[analysis_state],
                    outputs=[export_txt_file],
                )

                predict_structure_btn.click(
                    fn=run_structure_prediction,
                    inputs=[analysis_state],
                    outputs=[structure_status, structure_pdb, structure_view],
                )

            with gr.Tab("Compare", id="tab_compare"):
                gr.Markdown("### Wild-type vs mutant")
                with gr.Row():
                    with gr.Column():
                        wt_sequence_input = gr.Textbox(
                            label="Wild-type FASTA / sequence",
                            lines=9,
                            placeholder="WT…",
                        )
                        wt_name_input = gr.Textbox(label="WT label", value="WT")
                    with gr.Column():
                        mutant_sequence_input = gr.Textbox(
                            label="Mutant FASTA / sequence",
                            lines=9,
                            placeholder="Mutant…",
                        )
                        mutant_name_input = gr.Textbox(label="Mutant label", value="Mutant")

                protected_input_compare = gr.Textbox(
                    label="Locked residues",
                    placeholder="e.g. 23-41",
                )

                sequence_map_style_compare = gr.Dropdown(
                    label="Numbered sequence format",
                    choices=[
                        ("20 aa / line", "blocks_20"),
                        ("50 aa / line · groups of 10", "50_ten_groups"),
                    ],
                    value="blocks_20",
                )

                compare_btn = gr.Button("Compare sequences", variant="primary")

                compare_summary_output = gr.Markdown(label="Summary")

                with gr.Row():
                    wt_sequence_map_code = gr.Code(
                        label="WT · indexed",
                        language=None,
                        interactive=False,
                        lines=12,
                    )
                    mut_sequence_map_code = gr.Code(
                        label="Mutant · indexed",
                        language=None,
                        interactive=False,
                        lines=12,
                    )

                gr.Markdown("#### Per-region biophysics")
                per_region_compare_df = gr.Dataframe(
                    label="Δ local metrics by region",
                    wrap=True,
                    elem_classes=["pda-table-wrap", "pda-df-region"],
                )

                with gr.Accordion("Residue changes", open=True):
                    changed_df = gr.Dataframe(
                        label="Diffs",
                        wrap=True,
                        elem_classes=["pda-table-wrap", "pda-df-global"],
                    )

                with gr.Accordion("Score deltas", open=False):
                    risk_compare_df = gr.Dataframe(
                        label="Composite scores",
                        wrap=True,
                        elem_classes=["pda-table-wrap", "pda-df-risk"],
                    )

                with gr.Accordion("Liability changes", open=False):
                    with gr.Row():
                        gained_df = gr.Dataframe(
                            label="Gained",
                            wrap=True,
                            elem_classes=["pda-table-wrap", "pda-df-gained"],
                        )
                        lost_df = gr.Dataframe(
                            label="Lost",
                            wrap=True,
                            elem_classes=["pda-table-wrap", "pda-df-lost"],
                        )

                gr.Markdown("#### Profiles")
                hydro_compare_plot = gr.Plot(label="Hydrophobicity overlay")

                compare_btn.click(
                    fn=run_compare,
                    inputs=[
                        wt_sequence_input,
                        wt_name_input,
                        mutant_sequence_input,
                        mutant_name_input,
                        protected_input_compare,
                        sequence_map_style_compare,
                        session_state,
                    ],
                    outputs=[
                        compare_summary_output,
                        wt_sequence_map_code,
                        mut_sequence_map_code,
                        per_region_compare_df,
                        changed_df,
                        risk_compare_df,
                        gained_df,
                        lost_df,
                        hydro_compare_plot,
                        compare_state,
                        session_state,
                    ],
                )

    return demo
