import matplotlib.pyplot as plt
from utils.constants import KD_SCALE


def compute_hydrophobicity_profile(seq: str, window: int = 9) -> list[float]:
    if len(seq) < window:
        return []
    values = []
    for i in range(len(seq) - window + 1):
        chunk = seq[i:i+window]
        score = sum(KD_SCALE[aa] for aa in chunk) / window
        values.append(score)
    return values


def make_hydrophobicity_plot(
    seq: str,
    profile: list[float],
    risk_regions: list[dict] | None = None,
    protected_positions: set[int] | None = None,
):
    fig, ax = plt.subplots(figsize=(10, 3.5))
    if not profile:
        ax.text(0.5, 0.5, "Sequence too short for hydrophobicity profile", ha="center", va="center")
        ax.set_axis_off()
        return fig

    x = list(range(1, len(profile) + 1))
    ax.plot(x, profile)
    ax.set_xlabel("Window start position")
    ax.set_ylabel("Mean hydrophobicity")
    ax.set_title("Sliding-window hydrophobicity profile")

    if risk_regions:
        for r in risk_regions:
            if r["risk_type"] == "hydrophobic_cluster":
                ax.axvspan(r["start"], r["end"], alpha=0.2)

    return fig
