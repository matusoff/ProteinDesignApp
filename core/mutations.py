from utils.constants import PATCH_BREAKING_MAP
from config import TOP_N_SUGGESTIONS


def _make_mutation_record(
    position: int,
    wt: str,
    mut: str,
    category: str,
    expected_effect: str,
    rationale: str,
    confidence: str,
) -> dict:
    return {
        "rank": 0,
        "position": position,
        "wt_residue": wt,
        "mut_residue": mut,
        "mutation": f"{wt}{position}{mut}",
        "category": category,
        "expected_effect": expected_effect,
        "rationale": rationale,
        "confidence": confidence,
        "protected_filtered": True,
    }


def suggest_patch_breaking_mutations(
    seq: str,
    risk_regions: list[dict],
    protected_positions: set[int],
) -> list[dict]:
    suggestions = []
    for region in risk_regions:
        if region["risk_type"] != "hydrophobic_cluster":
            continue

        start, end = region["start"], region["end"]
        for pos in range(start, end + 1):
            if pos in protected_positions:
                continue
            wt = seq[pos - 1]
            if wt in PATCH_BREAKING_MAP:
                mut = PATCH_BREAKING_MAP[wt][0]
                suggestions.append(_make_mutation_record(
                    position=pos,
                    wt=wt,
                    mut=mut,
                    category="patch_breaking",
                    expected_effect="Reduce local hydrophobicity",
                    rationale="Residue lies within a hydrophobic risk region",
                    confidence="medium",
                ))
                break
    return suggestions


def suggest_oxidation_mitigations(
    seq: str,
    liabilities: list[dict],
    protected_positions: set[int],
) -> list[dict]:
    suggestions = []
    for item in liabilities:
        if item["liability_type"] != "oxidation_prone_residue":
            continue
        pos = item["position"]
        if pos in protected_positions:
            continue
        wt = seq[pos - 1]
        if wt == "M":
            suggestions.append(_make_mutation_record(
                position=pos,
                wt="M",
                mut="L",
                category="oxidation_mitigation",
                expected_effect="Reduce oxidation sensitivity",
                rationale="Methionine flagged as oxidation-prone",
                confidence="low",
            ))
    return suggestions


def suggest_motif_breaking_mutations(
    seq: str,
    liabilities: list[dict],
    protected_positions: set[int],
) -> list[dict]:
    suggestions = []
    for item in liabilities:
        if item["liability_type"] != "N_glycosylation_motif":
            continue
        pos = item["position"]
        if pos in protected_positions:
            continue
        wt = seq[pos - 1]
        suggestions.append(_make_mutation_record(
            position=pos,
            wt=wt,
            mut="Q",
            category="motif_breaking",
            expected_effect="Break N-linked glycosylation motif",
            rationale="N-X-S/T motif detected",
            confidence="low",
        ))
    return suggestions


def deduplicate_mutation_suggestions(suggestions: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for s in suggestions:
        key = s["mutation"]
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def rank_mutation_suggestions(suggestions: list[dict]) -> list[dict]:
    category_priority = {
        "patch_breaking": 0,
        "oxidation_mitigation": 1,
        "motif_breaking": 2,
    }
    suggestions = sorted(
        suggestions,
        key=lambda x: (category_priority.get(x["category"], 99), x["position"])
    )
    for i, s in enumerate(suggestions, start=1):
        s["rank"] = i
    return suggestions


def generate_mutation_suggestions(
    seq: str,
    risk_regions: list[dict],
    liabilities: list[dict],
    protected_positions: set[int],
) -> list[dict]:
    suggestions = []
    suggestions.extend(suggest_patch_breaking_mutations(seq, risk_regions, protected_positions))
    suggestions.extend(suggest_oxidation_mitigations(seq, liabilities, protected_positions))
    suggestions.extend(suggest_motif_breaking_mutations(seq, liabilities, protected_positions))
    suggestions = deduplicate_mutation_suggestions(suggestions)
    suggestions = rank_mutation_suggestions(suggestions)
    return suggestions[:TOP_N_SUGGESTIONS]
