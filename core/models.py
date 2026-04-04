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


@dataclass
class RegionEvidence:
    mean_hydrophobicity: float
    hydrophobic_fraction: float
    aromatic_fraction: float
    local_net_charge: int
    charged_fraction: float
    low_complexity: bool
    flexibility_proxy: float
    liability_count: int


@dataclass
class RegionAnalysis:
    start: int
    end: int
    sequence: str
    dominant_issue: str
    severity: str
    confidence: str
    evidence: RegionEvidence
    reason_summary: str
    design_strategy: str
    source_flags: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MutationImpact:
    mutation: str
    position: int
    wt_residue: str
    mut_residue: str
    region_start: int
    region_end: int
    before_metrics: dict[str, Any]
    after_metrics: dict[str, Any]
    deltas: dict[str, float]
    liabilities_gained: list[dict[str, Any]]
    liabilities_lost: list[dict[str, Any]]
    benefit_score: float
    disruption_risk: float
    confidence: str
    recommendation_tier: str
    rationale: str


@dataclass
class DecisionSummary:
    dominant_region: dict[str, Any] | None
    primary_recommendation: str
    safer_option: str | None
    stronger_option: str | None
    interpretation: str
