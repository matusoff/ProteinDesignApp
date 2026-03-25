# Protein Developability Review Assistant

Sequence-based developability review tool for protein constructs.

## Versions

| Tag    | Description |
|--------|-------------|
| `v1.0` | Baseline: analysis UI, tables, plot, text report (no exports / no structure). |
| `v1.1` | Adds ZIP export of tables + JSON scores, TXT report export, optional ESMFold structure prediction. |

**Roll back to the basic app** (discard v1.1 changes in the working tree):

```bash
git checkout v1.0
```

**Return to latest v1.1:**

```bash
git checkout main
# or: git checkout v1.1
```

Use a virtual environment for installs (see below), not the Anaconda base env.

## Features in v1.0

- FASTA / raw sequence input
- Global physicochemical properties
- Hydrophobic / aromatic / charge patch scanning
- Sequence liability detection
- Rule-based risk scoring
- First-pass mutation suggestions
- Hydrophobicity profile plot

## Features added in v1.1

- **Export tables** — ZIP containing `global_features.csv`, `risk_regions.csv`, `liabilities.csv`, `mutation_suggestions.csv`, and `scores.json`
- **Export report** — plain-text report file
- **Structure prediction** — optional local **ESMFold** via Hugging Face `transformers` (large download; GPU recommended). Install extras:

```bash
pip install -r requirements-structure.txt
```

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Use the project venv (`.venv`) so dependencies stay isolated from conda base.
