import gradio as gr
from config import APP_TITLE, APP_SUBTITLE, APP_VERSION
from ui.callbacks import (
    run_analysis,
    load_example_sequence,
    export_tables_zip_callback,
    export_report_txt_callback,
    run_structure_prediction,
)


def build_app_layout():
    with gr.Blocks(title=APP_TITLE) as demo:
        gr.Markdown(f"# {APP_TITLE}")
        gr.Markdown(APP_SUBTITLE)
        gr.Markdown(f"**Version:** {APP_VERSION} — *baseline v1.0 is git-tagged; see README to roll back.*")

        analysis_state = gr.State(value=None)

        with gr.Row():
            with gr.Column(scale=1):
                sequence_input = gr.Textbox(
                    label="Protein sequence or FASTA",
                    lines=12,
                    placeholder="Paste sequence here...",
                )
                seq_name_input = gr.Textbox(
                    label="Protein / construct name (optional)",
                    value="",
                )
                goal_input = gr.Dropdown(
                    label="Goal",
                    choices=[
                        "General review",
                        "Reduce aggregation risk",
                        "Improve solubility",
                        "Flag sequence liabilities",
                    ],
                    value="General review",
                )
                protected_input = gr.Textbox(
                    label="Protected residues / regions (optional)",
                    placeholder="23-41, 98, 101, 104",
                )

                with gr.Row():
                    analyze_btn = gr.Button("Analyze")
                    example_btn = gr.Button("Load example")

            with gr.Column(scale=1):
                summary_output = gr.Markdown(label="Summary")

        global_df = gr.Dataframe(label="Global features")
        risk_df = gr.Dataframe(label="Risk regions")
        liabilities_df = gr.Dataframe(label="Sequence liabilities")
        mutations_df = gr.Dataframe(label="Mutation suggestions")
        hydro_plot = gr.Plot(label="Hydrophobicity profile")
        report_output = gr.Textbox(label="Copyable report", lines=18)

        gr.Markdown("### Exports (v1.1)")
        with gr.Row():
            export_zip_btn = gr.Button("Export tables (ZIP: CSVs + scores.json)")
            export_txt_btn = gr.Button("Export report (TXT)")
        export_zip_file = gr.File(label="Download CSV bundle")
        export_txt_file = gr.File(label="Download text report")
        gr.Markdown("*Run Analyze first. Each export writes a new temp file for download.*")

        gr.Markdown("### Structure prediction (optional — ESMFold)")
        structure_help = gr.Markdown(
            "Uses **ESMFold** via Hugging Face `transformers` (first run downloads weights). "
            "Install extras: `pip install -r requirements-structure.txt`. "
            "**GPU** strongly recommended; **CPU** is very slow."
        )
        predict_structure_btn = gr.Button("Predict structure (current analyzed sequence)")
        structure_status = gr.Markdown()
        structure_pdb = gr.File(label="Predicted structure (PDB)")
        structure_view = gr.HTML(label="Viewer (py3Dmol)")

        analyze_btn.click(
            fn=run_analysis,
            inputs=[sequence_input, seq_name_input, goal_input, protected_input],
            outputs=[
                summary_output,
                global_df,
                risk_df,
                liabilities_df,
                mutations_df,
                hydro_plot,
                report_output,
                analysis_state,
            ],
        )

        example_btn.click(
            fn=load_example_sequence,
            inputs=[],
            outputs=[sequence_input],
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

    return demo
