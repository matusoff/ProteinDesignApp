"""
Optional ESMFold structure prediction (Hugging Face transformers).

Install: pip install -r requirements-structure.txt

Heavy: downloads model weights on first use; GPU strongly recommended.
"""

from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from config import ESMFOLD_MAX_LENGTH

_model = None
_tokenizer = None
_device = None
_load_lock = threading.Lock()


def structure_dependencies_available() -> tuple[bool, str]:
    try:
        import torch  # noqa: F401
        from transformers import AutoTokenizer, EsmForProteinFolding  # noqa: F401
    except ImportError as e:
        return False, (
            "Structure prediction is **not installed**. "
            "In your venv run:\n\n"
            "`pip install -r requirements-structure.txt`\n\n"
            f"Import error: `{e}`"
        )
    return True, ""


def _get_device():
    import torch

    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_model():
    global _model, _tokenizer, _device
    with _load_lock:
        if _model is not None:
            return
        from transformers import AutoTokenizer, EsmForProteinFolding

        _device = _get_device()
        _tokenizer = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
        _model = EsmForProteinFolding.from_pretrained(
            "facebook/esmfold_v1",
            low_cpu_mem_usage=True,
        )
        _model = _model.to(_device)
        _model.eval()
        if _device.type == "cuda" and hasattr(_model, "esm"):
            try:
                _model.esm = _model.esm.half()
            except Exception:
                pass
        if _device.type == "cuda" and hasattr(_model.trunk, "set_chunk_size"):
            try:
                _model.trunk.set_chunk_size(64)
            except Exception:
                pass


def _convert_outputs_to_pdb(outputs: Any) -> list[str]:
    from transformers.models.esm.openfold_utils.feats import atom14_to_atom37
    from transformers.models.esm.openfold_utils.protein import Protein as OFProtein
    from transformers.models.esm.openfold_utils.protein import to_pdb

    final_atom_positions = atom14_to_atom37(outputs["positions"][-1], outputs)
    outputs_cpu = {k: v.to("cpu").numpy() for k, v in outputs.items()}
    final_atom_positions = final_atom_positions.cpu().numpy()
    final_atom_mask = outputs_cpu["atom37_atom_exists"]
    pdbs: list[str] = []
    for i in range(outputs_cpu["aatype"].shape[0]):
        aa = outputs_cpu["aatype"][i]
        pred_pos = final_atom_positions[i]
        mask = final_atom_mask[i]
        resid = outputs_cpu["residue_index"][i] + 1
        pred = OFProtein(
            aatype=aa,
            atom_positions=pred_pos,
            atom_mask=mask,
            residue_index=resid,
            b_factors=outputs_cpu["plddt"][i],
            chain_index=outputs_cpu["chain_index"][i]
            if "chain_index" in outputs_cpu
            else None,
        )
        pdbs.append(to_pdb(pred))
    return pdbs


def _pdb_to_viewer_html(pdb_str: str) -> str:
    try:
        import py3Dmol
    except ImportError:
        return ""
    try:
        view = py3Dmol.view(
            js="https://cdn.jsdelivr.net/npm/3dmol@2.0.4/build/3Dmol-min.js",
            width=800,
            height=400,
        )
        view.addModel(pdb_str, "pdb")
        view.setStyle({"model": -1}, {"cartoon": {"color": "spectrum"}})
        view.zoomTo()
        if hasattr(view, "write_html"):
            fd, path = tempfile.mkstemp(suffix=".html")
            os.close(fd)
            try:
                view.write_html(path)
                return Path(path).read_text(encoding="utf-8")
            finally:
                Path(path).unlink(missing_ok=True)
    except Exception:
        return ""
    return ""


def predict_structure(sequence: str) -> dict[str, Any]:
    """
    Returns dict: ok (bool), markdown (str), pdb (str|None), html (str|None).
    """
    ok, msg = structure_dependencies_available()
    if not ok:
        return {"ok": False, "markdown": msg, "pdb": None, "html": None}

    seq = sequence.strip().upper()
    if not seq:
        return {"ok": False, "markdown": "Empty sequence.", "pdb": None, "html": None}

    truncated = False
    if len(seq) > ESMFOLD_MAX_LENGTH:
        seq = seq[:ESMFOLD_MAX_LENGTH]
        truncated = True

    warn = ""
    if truncated:
        warn = (
            f"\n\n**Note:** Sequence truncated to **{ESMFOLD_MAX_LENGTH}** aa "
            f"(config `ESMFOLD_MAX_LENGTH`). Full ESMFold runs are memory-heavy.\n"
        )

    import torch

    try:
        _load_model()
    except Exception as e:
        return {
            "ok": False,
            "markdown": f"Could not load ESMFold model: `{e}`",
            "pdb": None,
            "html": None,
        }

    try:
        with torch.no_grad():
            tokenized = _tokenizer(
                [seq],
                return_tensors="pt",
                add_special_tokens=False,
            )["input_ids"]
            tokenized = tokenized.to(_device)
            output = _model(tokenized)
            pdbs = _convert_outputs_to_pdb(output)
        pdb_text = "".join(pdbs)
    except Exception as e:
        return {
            "ok": False,
            "markdown": f"ESMFold inference failed: `{e}`",
            "pdb": None,
            "html": None,
        }

    dev = "GPU (CUDA)" if _device.type == "cuda" else "CPU (expect very long runtime)"
    md = (
        f"**ESMFold** finished on **{dev}**.{warn}\n\n"
        "Download the PDB below or use the viewer if shown."
    )
    html = _pdb_to_viewer_html(pdb_text)
    if not html:
        md += "\n\n*(Install `py3Dmol` in the structure extras for an inline viewer.)*"

    return {"ok": True, "markdown": md, "pdb": pdb_text, "html": html or None}
