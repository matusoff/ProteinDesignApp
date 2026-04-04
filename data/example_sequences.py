"""
Built-in FASTA demos for the Review tab.

Optional coordinates: drop AlphaFold 3 (or other) `.cif` / `.mmcif` files into
`data/structures/` using the names below — "Load demo" will attach them when present.
"""

from __future__ import annotations

from pathlib import Path

_DATA = Path(__file__).resolve().parent
STRUCTURES_DIR = _DATA / "structures"

# Original demo — mixed developability signals
EXAMPLE_HCV_NS3_FASTA = """>Demo_HCV_NS3_Nterm — sample for UI (charge + hydrophobic + motifs)
MSTNPKPQRKTKRNTNRRPQDVKFPGGGQIVGGVLTNQDKKVEAAMAEYKEAFSLFDKDGDGTITTKELGTVMRSLGQNPTEAELQDMINEVDADGNGTIDFPEFL
"""

# Mature human ubiquitin — compact, generally favorable solubility / low aggregation propensity
EXAMPLE_HUMAN_UBIQUITIN_FASTA = """>Human_ubiquitin_mature — low aggregation reference (76 aa)
MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG
"""

# Human α-synuclein (full-length) — intrinsically disordered / amyloid-associated (high aggregation context)
EXAMPLE_HUMAN_ASYN_FASTA = """>Human_alpha-synuclein — high aggregation reference (140 aa)
MDVFMKGLSKAKEGVVAAAEKTKQGVAEAAGKTKEGVLYVGSKTKEGVVHGVATVAEKTKEQVTNVGGAVVTGVTAVAQKTVEGAGSIAAATGFVKKDQLGKNEEGAPQEGILEDMPVDPDNEAYEMPSEEGYQDYEPEA
"""

DEMO_FASTAS: dict[str, str] = {
    "hcv": EXAMPLE_HCV_NS3_FASTA,
    "ubi": EXAMPLE_HUMAN_UBIQUITIN_FASTA,
    "syn": EXAMPLE_HUMAN_ASYN_FASTA,
}

# Backwards compatibility
EXAMPLE_FASTA = EXAMPLE_HCV_NS3_FASTA

DEMO_LABELS: list[tuple[str, str]] = [
    ("HCV NS3 fragment — mixed signals (original demo)", "hcv"),
    ("Human ubiquitin (mature) — low aggregation reference", "ubi"),
    ("Human α-synuclein — high aggregation reference", "syn"),
]


def demo_structure_path(demo_key: str) -> str | None:
    """
    If a matching file exists under data/structures/, return its path for gr.File.
    Checked names (first hit wins): .mmcif then .cif
    """
    base_names = {
        "hcv": "Demo_HCV_NS3_Nterm",
        "ubi": "Human_ubiquitin_mature",
        "syn": "Human_alpha-synuclein",
    }
    stem = base_names.get(demo_key)
    if not stem:
        return None
    for ext in (".mmcif", ".cif"):
        p = STRUCTURES_DIR / f"{stem}{ext}"
        if p.is_file():
            return str(p.resolve())
    return None
