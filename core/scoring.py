def label_score(score: float, low_thr: float, high_thr: float) -> str:
    if score < low_thr:
        return "Low"
    if score < high_thr:
        return "Medium"
    return "High"


def score_aggregation_risk(
    risk_regions: list[dict],
    liabilities: list[dict],
    global_features: dict,
) -> dict:
    score = 0.0
    for region in risk_regions:
        if region["risk_type"] == "hydrophobic_cluster":
            score += 3 if region["severity"] == "high" else 2
        elif region["risk_type"] == "aromatic_cluster":
            score += 2

    if global_features.get("gravy", 0) > 0.5:
        score += 1
    if global_features.get("aromatic_fraction", 0) > 0.12:
        score += 1

    return {"score": round(score, 2), "label": label_score(score, 3, 6)}


def score_solubility_risk(
    risk_regions: list[dict],
    liabilities: list[dict],
    global_features: dict,
) -> dict:
    score = 0.0
    if global_features.get("hydrophobic_fraction", 0) > 0.40:
        score += 2
    if abs(global_features.get("net_charge_pH7", 0)) < 1.0:
        score += 1

    for region in risk_regions:
        if region["risk_type"] == "charge_patch":
            score += 1
        if region["risk_type"] == "hydrophobic_cluster":
            score += 2 if region["severity"] == "high" else 1

    return {"score": round(score, 2), "label": label_score(score, 2, 5)}


def score_chemical_liability_risk(liabilities: list[dict]) -> dict:
    score = 0.0
    for item in liabilities:
        if item["liability_type"] == "N_glycosylation_motif":
            score += 1.5
        elif item["liability_type"] == "deamidation_prone_motif":
            score += 1
        elif item["liability_type"] == "oxidation_prone_residue":
            score += 0.5
        elif item["liability_type"] == "unpaired_cysteine_risk":
            score += 2

    return {"score": round(score, 2), "label": label_score(score, 2, 5)}


def compute_overall_risk(scores: dict) -> dict:
    total = (
        scores["aggregation"]["score"]
        + scores["solubility"]["score"]
        + scores["chemical"]["score"]
    ) / 3
    return {"score": round(total, 2), "label": label_score(total, 2.5, 5)}


def build_score_summary(
    global_features: dict,
    risk_regions: list[dict],
    liabilities: list[dict],
) -> dict:
    aggregation = score_aggregation_risk(risk_regions, liabilities, global_features)
    solubility = score_solubility_risk(risk_regions, liabilities, global_features)
    chemical = score_chemical_liability_risk(liabilities)
    scores = {
        "aggregation": aggregation,
        "solubility": solubility,
        "chemical": chemical,
    }
    scores["overall"] = compute_overall_risk(scores)
    return scores
