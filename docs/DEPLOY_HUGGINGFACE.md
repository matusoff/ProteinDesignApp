# Deploy the app live (Hugging Face Spaces)

This is the fastest way to get a **public URL** for evaluators. HF hosts Gradio apps for free (with limits: CPU, may sleep when idle).

## Prerequisites

- A [GitHub](https://github.com) account  
- A [Hugging Face](https://huggingface.co) account  
- This project pushed to a **GitHub repository** (public is simplest)

## 1. Push code to GitHub

From your project folder (adjust remote URL):

```bash
git init
git add .
git commit -m "Initial commit: Protein Developability Review Assistant"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

**Check before pushing**

- No `.env` files, API keys, or personal paths in `config.py`  
- Large `.cif` / `.pdb` files are not needed for the demo (optional `data/structures/*` is gitignored)

## 2. Create a Hugging Face Space (from your GitHub repo)

Your code: **`https://github.com/matusoff/ProteinDesignApp`** (branch **`main`**).

### Path A — GitHub offered when you create the Space (fastest)

1. Open **[huggingface.co/new-space](https://huggingface.co/new-space)** while logged in.  
2. **Owner:** your HF profile (e.g. `matusoff` if you use the same handle).  
3. **Space name:** e.g. `protein-developability-review` (becomes `huggingface.co/spaces/<you>/protein-developability-review`).  
4. **License:** MIT.  
5. **SDK:** **Gradio**.  
6. **Hardware:** **CPU basic** (free tier).  
7. If you see **“Import from GitHub”** / **“Link a repository”**: authorize GitHub if asked, then pick **`matusoff/ProteinDesignApp`** and branch **`main`**.  
8. Create the Space and wait for the first **build**.

### Path B — Space already exists or no GitHub option at creation

1. Create a **Gradio** Space as above (or open your Space).  
2. Go to **Settings** (gear on the Space page).  
3. Find **Repository** / **GitHub** / **Connect repository** (wording varies).  
4. Connect your GitHub account if needed, then select **`matusoff/ProteinDesignApp`**, branch **`main`**.  
5. Save; HF will sync files from GitHub and trigger a **rebuild**.

### What HF expects (you already have this)

- **`app.py`** at repo root with a top-level **`demo`** object (`build_app_layout()`).  
- **`requirements.txt`** at repo root.  
- **`python app.py`** is not required on HF for Gradio SDK — the platform loads `demo` — but your `app.py` is still valid for local runs.

## 3. Space README (card + description)

On the Space, open **Files** → `README.md` (HF creates one). Replace its contents with the block in  
[`HF_SPACE_README_SNIPPET.md`](HF_SPACE_README_SNIPPET.md) (YAML + short intro).

That sets the title, emoji, SDK, and the text people see above the app.

## 4. Wait for the build

Open the **Build** / **Logs** tab. First build runs `pip install -r requirements.txt` then starts Gradio.

**If the build fails**

- Read the log line that mentions `ImportError` or `ModuleNotFoundError`  
- Fix `requirements.txt` and push to GitHub; the Space will rebuild  

**If the app starts but errors on run**

- Check **Runtime** logs when you click **Run review**  
- Public CPU Spaces often **do not** have PyMOL — structure PNG may be missing; sequence review should still work  

## 5. Share the link

Your demo URL looks like:

`https://huggingface.co/spaces/YOUR_USERNAME/protein-developability-review`

Use that in LinkedIn / email; link **GitHub** second for code and `DISCLAIMER.md`.

## Optional: Hugging Face CLI

```bash
pip install huggingface_hub
huggingface-cli login
```

Then you can use `hf upload` / Git sync workflows; not required if you only use the website + GitHub sync.

## Alternative: Render / Railway / Fly.io

Any host that runs **Python** and sets **`PORT`** can run:

```bash
pip install -r requirements.txt
python app.py
```

Point the platform’s **start command** at that and map **PORT**. More setup than HF Spaces, but you get more control (always-on, custom image with PyMOL, etc.).
