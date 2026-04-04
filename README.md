# Protein Developability Review Assistant

**Version 1.3.0** · Exploratory **sequence** developability review in one pass: liabilities, regional risk heuristics, mutation ideas, and optional **structure-aware** context when you upload matching coordinates.

> **Not validated for the lab.** This is a prototype for discussion, teaching, and iteration — see [DISCLAIMER.md](DISCLAIMER.md).

---

## What it does

| Area | Capability |
|------|------------|
| **Sequence** | Parse FASTA or raw one-letter amino acid sequence |
| **Liabilities** | Flag common sequence motifs / hot-spots (heuristic rules) |
| **Regions** | Scan for local hydrophobic, charge, aromatic, and low-complexity patterns |
| **Scoring** | Composite readouts (overall / aggregation / solubility / chemical) — **illustrative**, not calibrated to experiments |
| **Mutations** | Ranked suggestions + simulated local metric deltas — **hypotheses only** |
| **Export** | ZIP (tables + JSON) and plain-text report |
| **Structure (optional)** | PDB/mmCIF upload; mapping and PyMOL PNG **if** PyMOL is available on the machine running the app |

Built with **Gradio** (UI), **Biopython**, **pandas**, **NumPy**, **matplotlib**.

---

## What it does *not* claim

- It is **not** an experimentally validated predictor of aggregation, solubility, or developability.
- It does **not** replace structural biology, formulation work, or program-specific assays.
- **Mutation suggestions** must be reviewed by someone who knows the target and the assay plan.

---

## Try it live (recommended for evaluators)

**Step-by-step:** [**docs/DEPLOY_HUGGINGFACE.md**](docs/DEPLOY_HUGGINGFACE.md) (GitHub → HF Space → share URL).

Short path:

1. Push this repo to **GitHub** (clean tree, no secrets).
2. **Hugging Face** → **New Space** → SDK **Gradio** → import from that repo.
3. Paste the Space `README` from [`docs/HF_SPACE_README_SNIPPET.md`](docs/HF_SPACE_README_SNIPPET.md).
4. Share `https://huggingface.co/spaces/<you>/<space-name>` plus your GitHub link.

**Public demo hygiene:** Free CPU Spaces usually **do not** have PyMOL — structure PNGs may be missing; sequence review + exports still work.

**Sanity check before you push:** `pip install -r requirements.txt` then `python -c "import app; print(app.demo)"` should print a Gradio Blocks object without error.

---

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
python app.py
```

Open the printed local URL (default port **7860**). The app respects the **`PORT`** environment variable (used by many hosts).

### Optional extras

| File | Purpose |
|------|---------|
| `requirements-structure.txt` | ESMFold-related stack (heavy; GPU recommended) |
| `requirements-pymol.txt` | Notes / optional conda stack for headless PyMOL |
| `data/structures/README.txt` | Naming convention for optional demo coordinate files |

### Demo sequences

Use **Demo sequence** → **Load demo** in the UI. Optional mmCIF/CIF files can be placed under `data/structures/` as described in `data/structures/README.txt`.

---

## Repository layout (high level)

```
app.py                 # Launches Gradio; exposes `demo` for HF Spaces
config.py              # Tunables (no secrets — use env for PyMOL path if needed)
ui/                    # Layout + callbacks
core/                  # Scanner, scoring, mutations, structure pipeline, …
data/                  # Example FASTAs + optional structures folder
plots/                 # Hydrophobicity figures
```

---

## Roadmap ideas (not commitments)

- Goal-specific review modes (aggregation vs solubility) with distinct weighting
- Clearer calibration / uncertainty language on scores
- Optional API or batch mode for internal use

---

## License

MIT — see [LICENSE](LICENSE). If you omit or change the license, update this section.

---

## Contact / citation

Add your name, lab, or preferred citation here when you publish the demo.
