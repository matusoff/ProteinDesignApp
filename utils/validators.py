from utils.constants import STANDARD_AA


def validate_sequence_symbols(seq: str) -> list[str]:
    invalid = []
    for idx, aa in enumerate(seq, start=1):
        if aa not in STANDARD_AA:
            invalid.append(f"{aa}@{idx}")
    return invalid
