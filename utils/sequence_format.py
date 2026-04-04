"""Numbered sequence display for locating residues (e.g. mutation N92Q)."""


def format_sequence_blocks(seq: str, line_width: int = 20) -> str:
    """
    One continuous string per line; left column = 1-based index of first residue on that line.

      1  ABCDEFGHIJKLMNOPQRST
     21  ...
    """
    if not seq:
        return ""
    lines: list[str] = []
    for i in range(0, len(seq), line_width):
        chunk = seq[i : i + line_width]
        start = i + 1
        lines.append(f"{start:>4}  {chunk}")
    return "\n".join(lines)


def format_sequence_ten_groups_fifty(seq: str) -> str:
    """
    Up to 50 residues per line as five groups of 10 separated by spaces.

      1  ABCDEFGHIJ KLMNOPQRST UVWXYABCDE FGHIJKLMNO PQRSTUVWXY
     51  ...
    """
    if not seq:
        return ""
    group = 10
    line_aa = 50
    lines: list[str] = []
    i = 0
    while i < len(seq):
        start_pos = i + 1
        parts: list[str] = []
        for _ in range(line_aa // group):
            if i >= len(seq):
                break
            parts.append(seq[i : i + group])
            i += group
        lines.append(f"{start_pos:>4}  {' '.join(parts)}")
    return "\n".join(lines)


def format_sequence_map(seq: str, style: str) -> str:
    if not seq:
        return ""
    header = f"Length {len(seq)} aa (positions are 1-based)\n"
    if style == "50_ten_groups":
        return header + format_sequence_ten_groups_fifty(seq)
    return header + format_sequence_blocks(seq, line_width=20)
