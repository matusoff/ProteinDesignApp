"""Entry point: local run (`python app.py`) and Hugging Face Spaces (Gradio SDK)."""

import os

from ui.layout import build_app_layout

demo = build_app_layout()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    # Local: 127.0.0.1 so the printed URL opens in the browser. Cloud (HF, Render, …) sets PORT — bind 0.0.0.0.
    server_name = (
        os.environ.get("GRADIO_SERVER_NAME")
        or ("0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
    )
    demo.launch(server_name=server_name, server_port=port)
