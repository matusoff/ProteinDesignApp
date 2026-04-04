"""Entry point: local run (`python app.py`) and Hugging Face Spaces (Gradio SDK)."""

import os

from ui.layout import build_app_layout

demo = build_app_layout()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
