# Hugging Face Space README (copy-paste)

When you create a **Gradio Space** on Hugging Face, replace the Space’s `README.md` content with the block below (YAML frontmatter + short page copy).  
Keep your **GitHub** `README.md` without this frontmatter so the repo page stays clean.

```markdown
---
title: Protein Developability Review Assistant
emoji: 🧬
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.50.0
python_version: 3.12
app_file: app.py
pinned: false
license: mit
short_description: "Protein developability: risks, liabilities, mutations."
---

# Protein Developability Review Assistant

**One-line:** Paste a protein sequence (FASTA or raw), get a structured developability-style review — flags, regions, and first-pass mutation hypotheses.

**Try this**
- Use **Load demo** for built-in examples (e.g. ubiquitin vs α-synuclein).
- Paste your own sequence and click **Run review**.
- Optionally attach a **PDB / mmCIF** that matches your sequence (structure-aware extras; PyMOL PNG only if the Space has PyMOL — often it will not).

**Caution:** Exploratory tool only — **not** a substitute for experimental validation. See the in-app **About this prototype** and the repo `DISCLAIMER.md`.

**GitHub:** [matusoff/ProteinDesignApp](https://github.com/matusoff/ProteinDesignApp) — source, `README`, `DISCLAIMER.md`.
```

After the first push, open **Space Settings → Repository** and point the Space at your GitHub repo (or duplicate from GitHub). Ensure `requirements.txt` and `app.py` are at the repository root.
