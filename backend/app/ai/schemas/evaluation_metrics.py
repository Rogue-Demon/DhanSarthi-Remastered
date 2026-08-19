"""
Evaluation & Aggregation Metric Schemas for DhanSarthi Phase L.10.

Defines mathematical distribution models, percentile summaries, and RAG/Quality
evaluation containers used across in-memory aggregation and health scorecard calculation.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PercentileDistribution(BaseModel):
    """Statistical summary of numeric observations."""

    count: int = Field(default=0, description="Total sample count")
    min: float = Field(default=0.0, description="Minimum observed value")
    mean: float = Field(default=0.0, description="Arithmetic mean")
    p50: float = Field(default=0.0, description="50th percentile (median)")
    p90: float = Field(default=0.0, description="90th percentile")
    p95: float = Field(default=0.0, description="95th percentile")
    p99: float = Field(default=0.0, description="99th percentile")
    max: float = Field(default=0.0, description="Maximum observed value")

    @classmethod
    def from_values(cls, values: List[float]) -> PercentileDistribution:
        """Compute percentiles safely from a list of float/int values."""
        clean = [float(v) for v in values if v is not None and not math.isnan(float(v))]
        if not clean:
            return cls()

        clean.sort()
        n = len(clean)
        min_v = clean[0]
        max_v = clean[-1]
        mean_v = sum(clean) / n

        def _percentile(p: float) -> float:
            if n == 1:
                return clean[0]
            k = (n - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return clean[int(k)]
            d0 = clean[int(f)] * (c - k)
            d1 = clean[int(c)] * (k - f)
            return d0 + d1

        return cls(
            count=n,
            min=round(min_v, 2),
            mean=round(mean_v, 2),
            p50=round(_percentile(0.50), 2),
            p90=round(_percentile(0.90), 2),
            p95=round(_percentile(0.95), 2),
            p99=round(_percentile(0.99), 2),
            max=round(max_v, 2),
        )


class RAGEvaluationSummary(BaseModel):
    """Aggregated retrieval metrics (Hit@K, MRR, Citations, Grounding)."""

    total_queries: int = Field(default=0)
    hit_at_1: float = Field(default=0.0, description="Hit rate @ 1")
    hit_at_3: float = Field(default=0.0, description="Hit rate @ 3")
    hit_at_5: float = Field(default=0.0, description="Hit rate @ 5")
    mrr: float = Field(default=0.0, description="Mean Reciprocal Rank")
    citation_accuracy: float = Field(default=0.0, description="Valid citation reference rate")
    authority_accuracy: float = Field(default=0.0, description="High authority source rate")
    grounding_score: float = Field(default=0.0, description="Average response grounding score")
