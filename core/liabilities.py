def find_n_glycosylation_motifs(seq: str) -> list[dict]:
    hits = []
    for i in range(len(seq) - 2):
        tri = seq[i:i+3]
        if tri[0] == "N" and tri[1] != "P" and tri[2] in {"S", "T"}:
            hits.append({
                "position": i + 1,
                "motif_or_residue": tri,
                "liability_type": "N_glycosylation_motif",
                "severity": "medium",
                "comment": "N-X-S/T motif detected",
            })
    return hits


def find_deamidation_motifs(seq: str) -> list[dict]:
    hits = []
    motifs = {"NG", "NS", "NN", "NT"}
    for i in range(len(seq) - 1):
        di = seq[i:i+2]
        if di in motifs:
            hits.append({
                "position": i + 1,
                "motif_or_residue": di,
                "liability_type": "deamidation_prone_motif",
                "severity": "medium" if di in {"NG", "NS"} else "low",
                "comment": "Potential deamidation-prone motif",
            })
    return hits


def find_oxidation_sites(seq: str) -> list[dict]:
    hits = []
    for i, aa in enumerate(seq, start=1):
        if aa == "M":
            hits.append({
                "position": i,
                "motif_or_residue": aa,
                "liability_type": "oxidation_prone_residue",
                "severity": "medium",
                "comment": "Methionine may be oxidation-prone",
            })
        elif aa == "W":
            hits.append({
                "position": i,
                "motif_or_residue": aa,
                "liability_type": "oxidation_prone_residue",
                "severity": "low",
                "comment": "Tryptophan may be oxidation-prone",
            })
    return hits


def find_unpaired_cysteine_flags(seq: str) -> list[dict]:
    count = seq.count("C")
    if count % 2 == 1:
        return [{
            "position": seq.find("C") + 1,
            "motif_or_residue": "C",
            "liability_type": "unpaired_cysteine_risk",
            "severity": "medium",
            "comment": "Odd number of cysteines detected",
        }]
    return []


def find_repeat_or_flexible_regions(seq: str) -> list[dict]:
    hits = []
    for i in range(len(seq) - 3):
        chunk = seq[i:i+4]
        if chunk in {"GGGG", "SSSS", "GSGS", "SGSG"}:
            hits.append({
                "position": i + 1,
                "motif_or_residue": chunk,
                "liability_type": "flexible_repeat_region",
                "severity": "low",
                "comment": "Potentially flexible repeat-like segment",
            })
    return hits


def find_sequence_liabilities(seq: str) -> list[dict]:
    hits = []
    hits.extend(find_n_glycosylation_motifs(seq))
    hits.extend(find_deamidation_motifs(seq))
    hits.extend(find_oxidation_sites(seq))
    hits.extend(find_unpaired_cysteine_flags(seq))
    hits.extend(find_repeat_or_flexible_regions(seq))
    return sorted(hits, key=lambda x: x["position"])
