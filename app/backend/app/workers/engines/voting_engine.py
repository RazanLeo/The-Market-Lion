"""Voting Engine — produces Confluence Score 0..100 + decision buy|sell|wait.

Categories with default weights (configurable from Admin):
  fundamental: 20%
  basics: 30%
  schools: 30%
  indicators: 10%
  flow: 10%
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable, Literal


Decision = Literal["buy", "sell", "wait"]


@dataclass
class AnalyzerResult:
    code: str
    result: Literal["buy", "sell", "neutral"]
    confidence: float  # 0..100
    weight: float = 1.0
    payload: dict[str, Any] = field(default_factory=dict)


CATEGORY_WEIGHTS = {
    "fundamental": 20.0,
    "basics": 30.0,
    "schools": 30.0,
    "indicators": 10.0,
    "flow": 10.0,
}


def _category_score(items: Iterable[AnalyzerResult]) -> tuple[float, float]:
    """Returns (signed_score [-100..+100], total_weight)."""
    items = list(items)
    if not items: return 0.0, 0.0
    total_w = sum(it.weight for it in items) or 1.0
    signed = 0.0
    for it in items:
        sign = +1 if it.result == "buy" else (-1 if it.result == "sell" else 0)
        signed += sign * it.confidence * it.weight
    return signed / total_w, total_w


def compute_confluence(
    fundamental: list[AnalyzerResult],
    basics: list[AnalyzerResult],
    schools: list[AnalyzerResult],
    indicators: list[AnalyzerResult],
    flow: list[AnalyzerResult],
    *,
    category_weights: dict[str, float] | None = None,
    threshold: float = 80.0,
) -> dict[str, Any]:
    cw = category_weights or CATEGORY_WEIGHTS
    fund_s, _ = _category_score(fundamental)
    bas_s, _ = _category_score(basics)
    sch_s, _ = _category_score(schools)
    ind_s, _ = _category_score(indicators)
    flo_s, _ = _category_score(flow)

    # final direction = sign of weighted sum of category signed-scores
    weighted_sum = (
        cw["fundamental"] * fund_s +
        cw["basics"] * bas_s +
        cw["schools"] * sch_s +
        cw["indicators"] * ind_s +
        cw["flow"] * flo_s
    )
    direction: Decision = "buy" if weighted_sum > 0 else ("sell" if weighted_sum < 0 else "wait")

    def aligned(score: float) -> float:
        if direction == "buy": return max(score, 0)
        if direction == "sell": return -min(score, 0)
        return 0

    confluence = (
        cw["fundamental"] / 100 * aligned(fund_s) +
        cw["basics"]      / 100 * aligned(bas_s) +
        cw["schools"]     / 100 * aligned(sch_s) +
        cw["indicators"]  / 100 * aligned(ind_s) +
        cw["flow"]        / 100 * aligned(flo_s)
    )

    decision: Decision = direction if confluence >= threshold else "wait"

    return {
        "fundamental_score": round(fund_s, 2),
        "basics_score": round(bas_s, 2),
        "schools_score": round(sch_s, 2),
        "indicators_score": round(ind_s, 2),
        "flow_score": round(flo_s, 2),
        "fundamental_pct": round(aligned(fund_s) * cw["fundamental"] / 100, 2),
        "basics_pct": round(aligned(bas_s) * cw["basics"] / 100, 2),
        "schools_pct": round(aligned(sch_s) * cw["schools"] / 100, 2),
        "indicators_pct": round(aligned(ind_s) * cw["indicators"] / 100, 2),
        "flow_pct": round(aligned(flo_s) * cw["flow"] / 100, 2),
        "total_pct": round(confluence, 2),
        "direction": direction,
        "decision": decision,
        "threshold": threshold,
        "contributions": {
            "fundamental": [{"code": x.code, "result": x.result, "confidence": x.confidence, "weight": x.weight} for x in fundamental],
            "basics": [{"code": x.code, "result": x.result, "confidence": x.confidence, "weight": x.weight} for x in basics],
            "schools": [{"code": x.code, "result": x.result, "confidence": x.confidence, "weight": x.weight} for x in schools],
            "indicators": [{"code": x.code, "result": x.result, "confidence": x.confidence, "weight": x.weight} for x in indicators],
            "flow": [{"code": x.code, "result": x.result, "confidence": x.confidence, "weight": x.weight} for x in flow],
        },
    }
