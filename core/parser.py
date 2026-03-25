from config import MIN_SEQUENCE_LENGTH
from utils.validators import validate_sequence_symbols


def strip_fasta_header(raw_text: str) -> str:
    lines = raw_text.strip().splitlines()
    lines = [line.strip() for line in lines if line.strip()]
    if not lines:
        return ""
    if lines[0].startswith(">"):
        lines = lines[1:]
    return "".join(lines)


def normalize_sequence(seq: str) -> str:
    return seq.replace(" ", "").replace("\n", "").replace("\r", "").upper()


def extract_sequence(raw_text: str) -> str:
    no_header = strip_fasta_header(raw_text)
    return normalize_sequence(no_header)


def check_min_length(seq: str, min_len: int = MIN_SEQUENCE_LENGTH) -> bool:
    return len(seq) >= min_len


def validate_sequence(seq: str) -> tuple[bool, list[str]]:
    errors = []
    if not seq:
        errors.append("Sequence is empty.")
        return False, errors

    invalid = validate_sequence_symbols(seq)
    if invalid:
        errors.append(f"Invalid amino acid symbols detected: {', '.join(invalid[:10])}")

    if not check_min_length(seq):
        errors.append(f"Sequence is too short. Minimum length is {MIN_SEQUENCE_LENGTH} aa.")

    return len(errors) == 0, errors
