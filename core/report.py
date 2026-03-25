import pandas as pd


def build_global_features_table(global_features: dict) -> pd.DataFrame:
    rows = [
        {"Property": k, "Value": v}
        for k, v in global_features.items()
    ]
    return pd.DataFrame(rows)


def build_risk_regions_table(risk_regions: list[dict]) -> pd.DataFrame:
    if not risk_regions:
        return pd.DataFrame(columns=["Start", "End", "Sequence", "Risk Type", "Severity", "Score", "Reason"])

    rows = []
    for r in risk_regions:
        rows.append({
            "Start": r["start"],
            "End": r["end"],
            "Sequence": r["sequence"],
            "Risk Type": r["risk_type"],
            "Severity": r["severity"],
            "Score": r["score"],
            "Reason": r["reason"],
        })
    return pd.DataFrame(rows)


def build_liabilities_table(liabilities: list[dict]) -> pd.DataFrame:
    if not liabilities:
        return pd.DataFrame(columns=["Position", "Motif/Residue", "Liability Type", "Severity", "Comment"])

    rows = []
    for x in liabilities:
        rows.append({
            "Position": x["position"],
            "Motif/Residue": x["motif_or_residue"],
            "Liability Type": x["liability_type"],
            "Severity": x["severity"],
            "Comment": x["comment"],
        })
    return pd.DataFrame(rows)


def build_mutation_table(suggestions: list[dict]) -> pd.DataFrame:
    if not suggestions:
        return pd.DataFrame(columns=["Rank", "Mutation", "Category", "Expected Effect", "Confidence", "Rationale"])

    rows = []
    for s in suggestions:
        rows.append({
            "Rank": s["rank"],
            "Mutation": s["mutation"],
            "Category": s["category"],
            "Expected Effect": s["expected_effect"],
            "Confidence": s["confidence"],
            "Rationale": s["rationale"],
        })
    return pd.DataFrame(rows)


def generate_short_summary(
    seq_name: str,
    score_summary: dict,
    risk_regions: list[dict],
    liabilities: list[dict],
    suggestions: list[dict],
) -> str:
    alerts = []
    if risk_regions:
        top = risk_regions[:2]
        alerts.extend([f'{r["risk_type"]} at {r["start"]}-{r["end"]}' for r in top])
    if liabilities:
        top = liabilities[:2]
        alerts.extend([f'{x["liability_type"]} at {x["position"]}' for x in top])

    alert_text = "; ".join(alerts) if alerts else "No major sequence alerts detected."
    suggestion_text = ", ".join([s["mutation"] for s in suggestions[:3]]) if suggestions else "No suggestions generated."

    return (
        f"### Summary for {seq_name or 'input sequence'}\n\n"
        f"- **Overall risk:** {score_summary['overall']['label']}  \n"
        f"- **Aggregation concern:** {score_summary['aggregation']['label']}  \n"
        f"- **Solubility concern:** {score_summary['solubility']['label']}  \n"
        f"- **Chemical liability concern:** {score_summary['chemical']['label']}  \n\n"
        f"**Top alerts:** {alert_text}\n\n"
        f"**Suggested first-pass mutations:** {suggestion_text}"
    )


def generate_text_report(result: dict) -> str:
    lines = [
        f"Sequence name: {result['sequence_name']}",
        f"Goal: {result['goal']}",
        "",
        "Scores:",
        f"  Overall: {result['scores']['overall']['label']} ({result['scores']['overall']['score']})",
        f"  Aggregation: {result['scores']['aggregation']['label']} ({result['scores']['aggregation']['score']})",
        f"  Solubility: {result['scores']['solubility']['label']} ({result['scores']['solubility']['score']})",
        f"  Chemical: {result['scores']['chemical']['label']} ({result['scores']['chemical']['score']})",
        "",
        "Global features:",
    ]
    for k, v in result["global_features"].items():
        lines.append(f"  - {k}: {v}")

    lines.append("")
    lines.append("Risk regions:")
    for r in result["risk_regions"]:
        lines.append(f"  - {r['risk_type']} at {r['start']}-{r['end']} ({r['severity']})")

    lines.append("")
    lines.append("Liabilities:")
    for x in result["liabilities"]:
        lines.append(f"  - {x['liability_type']} at {x['position']} ({x['motif_or_residue']})")

    lines.append("")
    lines.append("Mutation suggestions:")
    for s in result["mutation_suggestions"]:
        lines.append(f"  - {s['mutation']}: {s['expected_effect']}")

    return "\n".join(lines)
