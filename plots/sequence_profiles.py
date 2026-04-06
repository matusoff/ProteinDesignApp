from __future__ import annotations

import math

import matplotlib.pyplot as plt

from utils.constants import KD_SCALE, NEGATIVE_AA, POSITIVE_AA


def _sliding(seq: str, window: int, fn) -> list[float]:
    if not seq or len(seq) < window:
        return []
    return [fn(seq[i : i + window]) for i in range(len(seq) - window + 1)]


def compute_charge_profile(seq: str, window: int = 9) -> list[float]:
    return _sliding(
        seq,
        window,
        lambda chunk: (sum(1 for aa in chunk if aa in POSITIVE_AA) - sum(1 for aa in chunk if aa in NEGATIVE_AA)) / window,
    )


def compute_aromatic_profile(seq: str, window: int = 9) -> list[float]:
    aromatic = {"F", "W", "Y"}
    return _sliding(seq, window, lambda chunk: sum(1 for aa in chunk if aa in aromatic) / window)


def compute_low_complexity_profile(seq: str, window: int = 9) -> list[float]:
    def low_complexity_score(chunk: str) -> float:
        n = len(chunk)
        if n == 0:
            return 0.0
        counts: dict[str, int] = {}
        for aa in chunk:
            counts[aa] = counts.get(aa, 0) + 1
        entropy = 0.0
        for c in counts.values():
            p = c / n
            entropy -= p * math.log2(p)
        max_entropy = math.log2(min(20, n))
        if max_entropy <= 0:
            return 0.0
        # 0 = diverse window, 1 = repetitive / low-complexity window.
        return 1.0 - (entropy / max_entropy)

    return _sliding(seq, window, low_complexity_score)


def make_sequence_tracks_plot(
    seq: str,
    hydrophobicity_profile: list[float],
    charge_profile: list[float],
    aromatic_profile: list[float],
    low_complexity_profile: list[float],
):
    fig, axes = plt.subplots(4, 1, figsize=(11, 8), sharex=True)

    if not hydrophobicity_profile:
        axes[0].text(0.5, 0.5, "Sequence too short for sliding-window profiles", ha="center", va="center")
        for ax in axes:
            ax.set_axis_off()
        return fig

    x = list(range(1, len(hydrophobicity_profile) + 1))

    axes[0].plot(x, hydrophobicity_profile, color="#1d4ed8", linewidth=1.8)
    axes[0].set_ylabel("KD mean")
    axes[0].set_title("Sequence biophysics tracks")
    axes[0].grid(alpha=0.2, linestyle="--")

    axes[1].plot(x, charge_profile, color="#9333ea", linewidth=1.6)
    axes[1].axhline(0.0, color="#64748b", linewidth=1.0, alpha=0.7)
    axes[1].set_ylabel("Net charge")
    axes[1].grid(alpha=0.2, linestyle="--")

    axes[2].plot(x, aromatic_profile, color="#ea580c", linewidth=1.6)
    axes[2].set_ylabel("Aromatic frac")
    axes[2].set_ylim(-0.02, 1.02)
    axes[2].grid(alpha=0.2, linestyle="--")

    axes[3].plot(x, low_complexity_profile, color="#0891b2", linewidth=1.6)
    axes[3].set_ylabel("Low-complex")
    axes[3].set_ylim(-0.02, 1.02)
    axes[3].set_xlabel("Window start position")
    axes[3].grid(alpha=0.2, linestyle="--")

    fig.tight_layout()
    return fig


def make_profile_delta_plot(
    wt_hydro: list[float],
    mut_hydro: list[float],
    wt_charge: list[float],
    mut_charge: list[float],
    wt_aromatic: list[float],
    mut_aromatic: list[float],
    wt_low_complexity: list[float],
    mut_low_complexity: list[float],
):
    n = min(
        len(wt_hydro),
        len(mut_hydro),
        len(wt_charge),
        len(mut_charge),
        len(wt_aromatic),
        len(mut_aromatic),
        len(wt_low_complexity),
        len(mut_low_complexity),
    )
    fig, axes = plt.subplots(4, 1, figsize=(11, 8), sharex=True)
    if n == 0:
        axes[0].text(0.5, 0.5, "No overlapping profiles to compare", ha="center", va="center")
        for ax in axes:
            ax.set_axis_off()
        return fig

    x = list(range(1, n + 1))
    delta_h = [mut_hydro[i] - wt_hydro[i] for i in range(n)]
    delta_c = [mut_charge[i] - wt_charge[i] for i in range(n)]
    delta_a = [mut_aromatic[i] - wt_aromatic[i] for i in range(n)]
    delta_lc = [mut_low_complexity[i] - wt_low_complexity[i] for i in range(n)]

    data = [
        (delta_h, "Δ KD mean", "#1d4ed8"),
        (delta_c, "Δ net charge", "#9333ea"),
        (delta_a, "Δ aromatic frac", "#ea580c"),
        (delta_lc, "Δ low-complex", "#0891b2"),
    ]
    for ax, (y, label, color) in zip(axes, data):
        ax.plot(x, y, color=color, linewidth=1.6)
        ax.axhline(0.0, color="#64748b", linewidth=1.0, alpha=0.7)
        ax.set_ylabel(label)
        ax.grid(alpha=0.2, linestyle="--")

    axes[0].set_title("Mutant - WT profile deltas")
    axes[-1].set_xlabel("Window start position")
    fig.tight_layout()
    return fig
