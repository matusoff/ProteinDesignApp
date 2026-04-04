from utils.constants import AROMATIC_AA, HYDROPHOBIC_AA, KD_SCALE, NEGATIVE_AA, POSITIVE_AA


def get_subsequence(seq: str, start: int, end: int) -> str:
    return seq[start - 1 : end]


def mutate_sequence(seq: str, position: int, new_residue: str) -> str:
    idx = position - 1
    return seq[:idx] + new_residue + seq[idx + 1 :]


def local_mean_hydrophobicity(seq: str) -> float:
    if not seq:
        return 0.0
    return sum(KD_SCALE[a] for a in seq) / len(seq)


def local_hydrophobic_fraction(seq: str) -> float:
    if not seq:
        return 0.0
    return sum(1 for a in seq if a in HYDROPHOBIC_AA) / len(seq)


def local_aromatic_fraction(seq: str) -> float:
    if not seq:
        return 0.0
    return sum(1 for a in seq if a in AROMATIC_AA) / len(seq)


def local_net_charge(seq: str) -> int:
    pos = sum(1 for a in seq if a in POSITIVE_AA)
    neg = sum(1 for a in seq if a in NEGATIVE_AA)
    return pos - neg


def local_charged_fraction(seq: str) -> float:
    if not seq:
        return 0.0
    return sum(1 for a in seq if a in POSITIVE_AA or a in NEGATIVE_AA) / len(seq)


def local_low_complexity(seq: str, unique_threshold: int = 4) -> bool:
    if not seq:
        return False
    return len(set(seq)) <= unique_threshold


def local_flexibility_proxy(seq: str) -> float:
    if not seq:
        return 0.0
    flexible = set("GSPNQEDK")
    return sum(1 for a in seq if a in flexible) / len(seq)
