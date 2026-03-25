from collections import Counter
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from utils.constants import HYDROPHOBIC_AA, AROMATIC_AA, POLAR_AA, CHARGED_AA


def calc_length(seq: str) -> int:
    return len(seq)


def calc_molecular_weight(seq: str) -> float:
    return ProteinAnalysis(seq).molecular_weight()


def calc_theoretical_pi(seq: str) -> float:
    return ProteinAnalysis(seq).isoelectric_point()


def calc_net_charge(seq: str, ph: float = 7.0) -> float:
    return ProteinAnalysis(seq).charge_at_pH(ph)


def calc_aa_composition(seq: str) -> dict[str, float]:
    counts = Counter(seq)
    total = len(seq)
    return {aa: counts.get(aa, 0) / total for aa in sorted(counts)}


def calc_hydrophobic_fraction(seq: str) -> float:
    return sum(1 for aa in seq if aa in HYDROPHOBIC_AA) / len(seq)


def calc_aromatic_fraction(seq: str) -> float:
    return sum(1 for aa in seq if aa in AROMATIC_AA) / len(seq)


def calc_polar_fraction(seq: str) -> float:
    return sum(1 for aa in seq if aa in POLAR_AA) / len(seq)


def calc_charged_fraction(seq: str) -> float:
    return sum(1 for aa in seq if aa in CHARGED_AA) / len(seq)


def calc_gravy(seq: str) -> float:
    return ProteinAnalysis(seq).gravy()


def calc_cysteine_count(seq: str) -> int:
    return seq.count("C")


def summarize_global_features(seq: str) -> dict:
    return {
        "length": calc_length(seq),
        "molecular_weight": round(calc_molecular_weight(seq), 2),
        "theoretical_pI": round(calc_theoretical_pi(seq), 2),
        "net_charge_pH7": round(calc_net_charge(seq, ph=7.0), 2),
        "hydrophobic_fraction": round(calc_hydrophobic_fraction(seq), 3),
        "aromatic_fraction": round(calc_aromatic_fraction(seq), 3),
        "polar_fraction": round(calc_polar_fraction(seq), 3),
        "charged_fraction": round(calc_charged_fraction(seq), 3),
        "gravy": round(calc_gravy(seq), 3),
        "cysteine_count": calc_cysteine_count(seq),
    }
