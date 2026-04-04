"""
Load PDB/mmCIF and build ordered protein residue tables with sequence alignment hints.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from Bio.Data.IUPACData import protein_letters_3to1
from Bio.PDB import MMCIFParser, PDBParser
from Bio.PDB.Polypeptide import is_aa


def _parser_for_path(path: Path):
    suf = path.suffix.lower()
    if suf in (".cif", ".mmcif"):
        return MMCIFParser(QUIET=True), str(path)
    return PDBParser(QUIET=True), str(path)


def load_structure(path: str | Path) -> Any:
    """Return a Bio.PDB Structure object."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Not a file: {path}")
    parser, fn = _parser_for_path(p)
    structure = parser.get_structure(p.stem, fn)
    return structure


def _one_letter(residue) -> str | None:
    if not is_aa(residue, standard=True):
        return None
    rn = residue.get_resname().strip().title()
    return protein_letters_3to1.get(rn)


def extract_protein_residues(structure: Any, chain_id: str | None = None) -> tuple[Any, list]:
    """
    Return (chain, list of Bio.PDB Residue) in file order for that chain.
    Skips heteroatoms and non-standard amino acids.
    """
    models = list(structure)
    if not models:
        raise ValueError("Structure has no models.")
    model = models[0]
    chains = list(model.get_chains())
    if not chains:
        raise ValueError("Model has no chains.")

    if chain_id is not None:
        chain = next((c for c in chains if c.id == chain_id), None)
        if chain is None:
            raise ValueError(f"Chain {chain_id!r} not found. Available: {[c.id for c in chains]}")
    else:
        chain = chains[0]

    out: list = []
    for res in chain:
        if res.id[0] != " ":
            continue
        aa = _one_letter(res)
        if aa is None:
            continue
        out.append(res)
    return chain, out


def build_residue_table(
    residues: list,
    user_sequence: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Map ordered structure residues to 1..N sequence positions.

    v1: same-length + same letters → full confidence; otherwise warn and best-effort alignment.
    """
    warnings: list[str] = []
    chain_letters = "".join(_one_letter(r) or "X" for r in residues)
    seq = user_sequence.upper().strip()

    table: list[dict[str, Any]] = []
    if not residues:
        warnings.append("No standard amino-acid residues found in selected chain.")
        return table, warnings

    if len(chain_letters) == len(seq):
        mismatches = [i + 1 for i, (a, b) in enumerate(zip(chain_letters, seq)) if a != b]
        if mismatches:
            warnings.append(
                "Structure sequence differs from input at position(s): "
                + ", ".join(str(p) for p in mismatches[:20])
                + (" …" if len(mismatches) > 20 else "")
                + " — mapping uses index order; structural overlays are approximate."
            )
        for i, res in enumerate(residues):
            aa = _one_letter(res) or "X"
            table.append(
                {
                    "seq_index": i + 1,
                    "pdb_resseq": res.id[1],
                    "pdb_icode": res.id[2].strip() or "",
                    "one_letter": aa,
                    "resname": res.get_resname(),
                }
            )
        return table, warnings

    warnings.append(
        f"Length mismatch: structure chain has {len(chain_letters)} residues, "
        f"input sequence has {len(seq)}. Mapping truncated to min length."
    )
    n = min(len(chain_letters), len(seq))
    for i in range(n):
        res = residues[i]
        aa = _one_letter(res) or "X"
        table.append(
            {
                "seq_index": i + 1,
                "pdb_resseq": res.id[1],
                "pdb_icode": res.id[2].strip() or "",
                "one_letter": aa,
                "resname": res.get_resname(),
            }
        )
    return table, warnings
