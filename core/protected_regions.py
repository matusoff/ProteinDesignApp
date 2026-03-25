def parse_protected_regions(raw_text: str) -> set[int]:
    positions = set()
    if not raw_text.strip():
        return positions

    for token in raw_text.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start, end = token.split("-")
            start, end = int(start), int(end)
            positions.update(range(start, end + 1))
        else:
            positions.add(int(token))
    return positions


def is_position_protected(position: int, protected_positions: set[int]) -> bool:
    return position in protected_positions


def filter_positions_by_protection(
    positions: list[int],
    protected_positions: set[int],
) -> list[int]:
    return [p for p in positions if p not in protected_positions]
