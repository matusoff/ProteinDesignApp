from utils.constants import KD_SCALE, AROMATIC_AA, POSITIVE_AA, NEGATIVE_AA


def sliding_window(seq: str, window: int) -> list[tuple[int, int, str]]:
    chunks = []
    if len(seq) < window:
        return chunks
    for i in range(len(seq) - window + 1):
        start = i + 1
        end = i + window
        chunks.append((start, end, seq[i:i + window]))
    return chunks


def scan_local_hydrophobicity(seq: str, window: int = 9) -> list[dict]:
    regions = []
    for start, end, chunk in sliding_window(seq, window):
        score = sum(KD_SCALE[aa] for aa in chunk) / window
        if score >= 1.5:
            severity = "high" if score >= 2.0 else "medium"
            regions.append({
                "start": start,
                "end": end,
                "sequence": chunk,
                "risk_type": "hydrophobic_cluster",
                "severity": severity,
                "score": round(score, 3),
                "reason": "Hydrophobic-rich local stretch",
            })
    return regions


def scan_aromatic_clusters(seq: str, window: int = 7) -> list[dict]:
    regions = []
    for start, end, chunk in sliding_window(seq, window):
        aromatic_count = sum(1 for aa in chunk if aa in AROMATIC_AA)
        if aromatic_count >= 3:
            regions.append({
                "start": start,
                "end": end,
                "sequence": chunk,
                "risk_type": "aromatic_cluster",
                "severity": "medium" if aromatic_count == 3 else "high",
                "score": aromatic_count,
                "reason": "Aromatic-rich local region",
            })
    return regions


def scan_charge_patches(seq: str, window: int = 9) -> list[dict]:
    regions = []
    for start, end, chunk in sliding_window(seq, window):
        pos = sum(1 for aa in chunk if aa in POSITIVE_AA)
        neg = sum(1 for aa in chunk if aa in NEGATIVE_AA)
        net = pos - neg
        if abs(net) >= 5:
            regions.append({
                "start": start,
                "end": end,
                "sequence": chunk,
                "risk_type": "charge_patch",
                "severity": "medium" if abs(net) == 5 else "high",
                "score": net,
                "reason": "Highly charged local patch",
            })
    return regions


def scan_low_complexity_regions(seq: str, window: int = 12) -> list[dict]:
    regions = []
    for start, end, chunk in sliding_window(seq, window):
        unique = len(set(chunk))
        if unique <= 4:
            regions.append({
                "start": start,
                "end": end,
                "sequence": chunk,
                "risk_type": "low_complexity",
                "severity": "low",
                "score": unique,
                "reason": "Low-complexity segment",
            })
    return regions


def merge_overlapping_regions(regions: list[dict]) -> list[dict]:
    if not regions:
        return []
    regions = sorted(regions, key=lambda x: (x["risk_type"], x["start"], x["end"]))
    merged = [regions[0]]

    for region in regions[1:]:
        prev = merged[-1]
        same_type = region["risk_type"] == prev["risk_type"]
        overlap = region["start"] <= prev["end"] + 1

        if same_type and overlap:
            prev["end"] = max(prev["end"], region["end"])
            prev["sequence"] = ""
            prev["score"] = max(prev["score"], region["score"])
            if region["severity"] == "high":
                prev["severity"] = "high"
        else:
            merged.append(region)

    return merged


def identify_risk_regions(seq: str) -> list[dict]:
    regions = []
    regions.extend(scan_local_hydrophobicity(seq))
    regions.extend(scan_aromatic_clusters(seq))
    regions.extend(scan_charge_patches(seq))
    regions.extend(scan_low_complexity_regions(seq))
    return merge_overlapping_regions(regions)
