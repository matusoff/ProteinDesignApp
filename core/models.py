from dataclasses import dataclass, field
from typing import Any


@dataclass
class RiskRegion:
    start: int
    end: int
    sequence: str
    risk_type: str
    severity: str
    score: float
    reason: str


@dataclass
class LiabilityFlag:
    position: int
    motif_or_residue: str
    liability_type: str
    severity: str
    comment: str


@dataclass
class MutationSuggestion:
    rank: int
    position: int
    wt_residue: str
    mut_residue: str
    mutation: str
    category: str
    expected_effect: str
    rationale: str
    confidence: str
    protected_filtered: bool = True


@dataclass
class AnalysisResult:
    sequence: str
    sequence_name: str
    goal: str
    protected_positions: list[int]
    global_features: dict[str, Any] = field(default_factory=dict)
    risk_regions: list[dict[str, Any]] = field(default_factory=list)
    liabilities: list[dict[str, Any]] = field(default_factory=list)
    scores: dict[str, Any] = field(default_factory=dict)
    mutation_suggestions: list[dict[str, Any]] = field(default_factory=list)
    summary_text: str = ""
    report_text: str = ""
