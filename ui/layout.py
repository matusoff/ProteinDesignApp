import gradio as gr
from config import APP_TITLE, APP_SUBTITLE
from ui.callbacks import run_analysis, load_example_sequence


def build_app_layout():
    with gr.Blocks(title=APP_TITLE) as demo:
        gr.Markdown(f"# {APP_TITLE}")
        gr.Markdown(APP_SUBTITLE)

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
            ],
        )

        example_btn.click(
            fn=load_example_sequence,
            inputs=[],
            outputs=[sequence_input],
        )

    return demo
