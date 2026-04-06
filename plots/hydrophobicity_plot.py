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
    ax.set_xlabel("Window start position (1-based)")
    ax.set_ylabel("Mean hydropathy (Kyte–Doolittle)\n9-residue window")
    ax.set_title("Sliding-window hydropathy (Kyte–Doolittle scale)")

    if risk_regions:
        for r in risk_regions:
            if r["risk_type"] == "hydrophobic_cluster":
                ax.axvspan(r["start"], r["end"], alpha=0.2)

    return fig


def make_hydrophobicity_comparison_plot(
    wt_seq: str,
    mut_seq: str,
    wt_profile: list[float],
    mut_profile: list[float],
    changed_positions: list[int],
    window: int = 9,
):
    """
    Overlay WT vs Mutant hydrophobicity profiles and mark changed residues.
    """

    fig, ax = plt.subplots(figsize=(10, 3.5))
    if not wt_profile and not mut_profile:
        ax.text(0.5, 0.5, "No profiles to plot (sequence too short)", ha="center", va="center")
        ax.set_axis_off()
        return fig

    if wt_profile:
        x_wt = list(range(1, len(wt_profile) + 1))
        ax.plot(x_wt, wt_profile, label="WT")
    if mut_profile:
        x_mut = list(range(1, len(mut_profile) + 1))
        ax.plot(x_mut, mut_profile, label="Mutant")

    ax.set_xlabel("Window start position (1-based)")
    ax.set_ylabel("Mean hydropathy (Kyte–Doolittle)\n9-residue window")
    ax.set_title("WT vs Mutant — Kyte–Doolittle hydropathy")
    ax.legend(loc="best")

    if changed_positions:
        half = window // 2
        for pos in changed_positions:
            x = pos - half
            if x > 0:
                ax.axvline(x, alpha=0.2, linewidth=1.5, color="red")

    return fig
