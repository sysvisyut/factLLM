"""
Multidimensional Fact Comparator.
Compares candidate fact pairs across 6 distinct dimensions:
1. Value Equality (within tolerance)
2. Unit Alignment
3. Temporal Alignment (identical, sub-period, consecutive, different)
4. Scope Alignment (consolidated vs subsidiary vs regional)
5. Measurement Basis Alignment (GAAP vs Non-GAAP, FAE vs SAE, Budget vs Actual)
6. Polarity Alignment
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ComparisonResult:
    value_match: bool
    value_delta_abs: float
    value_delta_pct: float
    unit_match: bool
    temporal_match: bool
    temporal_relation: str          # 'SAME_PERIOD', 'SUB_PERIOD', 'DIFFERENT_PERIOD', 'BOTH_CUMULATIVE', 'UNSPECIFIED'
    scope_match: bool
    scope_relation: str             # 'SAME_SCOPE', 'SUBSIDIARY_VS_PARENT', 'REGIONAL_DIFFERENCE', 'DIFFERENT_SCOPE'
    basis_match: bool
    basis_relation: str             # 'SAME_BASIS', 'GAAP_VS_NON_GAAP', 'FAE_VS_SAE', 'BUDGET_VS_ACTUAL', 'DIFFERENT_BASIS'
    polarity_match: bool
    important_differences: List[str] = field(default_factory=list)

    def to_dimensions_dict(self) -> Dict[str, Any]:
        return {
            "value_match": self.value_match,
            "value_delta_abs": self.value_delta_abs,
            "value_delta_pct": self.value_delta_pct,
            "unit_match": self.unit_match,
            "temporal_match": self.temporal_match,
            "temporal_relation": self.temporal_relation,
            "scope_match": self.scope_match,
            "scope_relation": self.scope_relation,
            "basis_match": self.basis_match,
            "basis_relation": self.basis_relation,
            "polarity_match": self.polarity_match
        }


class DimensionComparator:
    TOLERANCE_PCT = 0.5   # 0.5% tolerance for rounding in financial/macro metrics
    TOLERANCE_ABS = 0.01  # absolute tolerance for small numbers (e.g. GDP growth rates)

    @classmethod
    def compare_facts(cls, fact_a: Any, fact_b: Any) -> ComparisonResult:
        """Compares two facts across all dimensions and compiles dimensional analysis."""
        ctx_a = fact_a.context
        ctx_b = fact_b.context
        important_diffs: List[str] = []

        # 1. Value comparison
        v_a = fact_a.value_normalized
        v_b = fact_b.value_normalized

        if v_a is not None and v_b is not None:
            delta_abs = abs(v_a - v_b)
            denom = max(abs(v_a), abs(v_b))
            delta_pct = (delta_abs / denom) * 100.0 if denom > 0 else 0.0
            value_match = (delta_pct <= cls.TOLERANCE_PCT) or (delta_abs <= cls.TOLERANCE_ABS)
        else:
            delta_abs = 0.0
            delta_pct = 0.0
            value_match = (fact_a.value_raw.strip().lower() == fact_b.value_raw.strip().lower())

        if not value_match:
            important_diffs.append(f"Value difference: '{fact_a.value_raw}' vs '{fact_b.value_raw}'")

        # 2. Unit comparison
        u_a = (fact_a.unit_canonical or "").strip().lower()
        u_b = (fact_b.unit_canonical or "").strip().lower()
        unit_match = (u_a == u_b) if (u_a and u_b) else True

        if not unit_match:
            important_diffs.append(f"Unit difference: '{fact_a.unit_canonical}' vs '{fact_b.unit_canonical}'")

        # 3. Temporal comparison
        t_start_a = ctx_a.time_start if ctx_a else None
        t_end_a = ctx_a.time_end if ctx_a else None
        t_type_a = ctx_a.time_type if ctx_a else None
        t_raw_a = (ctx_a.time_raw or "").strip().lower() if ctx_a else ""

        t_start_b = ctx_b.time_start if ctx_b else None
        t_end_b = ctx_b.time_end if ctx_b else None
        t_type_b = ctx_b.time_type if ctx_b else None
        t_raw_b = (ctx_b.time_raw or "").strip().lower() if ctx_b else ""

        temporal_match = False
        temporal_relation = "DIFFERENT_PERIOD"

        if t_type_a == "cumulative" and t_type_b == "cumulative":
            temporal_match = True
            temporal_relation = "BOTH_CUMULATIVE"
        elif t_start_a and t_end_a and t_start_b and t_end_b:
            if t_start_a == t_start_b and t_end_a == t_end_b:
                temporal_match = True
                temporal_relation = "SAME_PERIOD"
            elif (t_start_a >= t_start_b and t_end_a <= t_end_b) or (t_start_b >= t_start_a and t_end_b <= t_end_a):
                temporal_match = False
                temporal_relation = "SUB_PERIOD"
                important_diffs.append(f"Temporal period mismatch (Sub-period vs Full period): {ctx_a.time_raw} vs {ctx_b.time_raw}")
            else:
                temporal_match = False
                temporal_relation = "DIFFERENT_PERIOD"
                important_diffs.append(f"Different time periods: {ctx_a.time_raw} vs {ctx_b.time_raw}")
        elif t_raw_a and t_raw_b and t_raw_a == t_raw_b:
            temporal_match = True
            temporal_relation = "SAME_PERIOD"
        elif not t_raw_a and not t_raw_b:
            temporal_match = True
            temporal_relation = "UNSPECIFIED"
        else:
            temporal_relation = "DIFFERENT_PERIOD"
            if t_raw_a or t_raw_b:
                important_diffs.append(f"Temporal context differs: '{ctx_a.time_raw if ctx_a else ''}' vs '{ctx_b.time_raw if ctx_b else ''}'")

        # 4. Scope comparison
        sc_a = (ctx_a.scope or "consolidated").strip().lower() if ctx_a else "consolidated"
        sc_b = (ctx_b.scope or "consolidated").strip().lower() if ctx_b else "consolidated"

        scope_match = (sc_a == sc_b)
        scope_relation = "SAME_SCOPE"
        if not scope_match:
            if "subsidiary" in (sc_a, sc_b) or "spoton" in (sc_a, sc_b):
                scope_relation = "SUBSIDIARY_VS_PARENT"
                important_diffs.append(f"Scope difference: Subsidiary ({sc_a}) vs Parent/Consolidated ({sc_b})")
            elif "regional" in sc_a or "regional" in sc_b:
                scope_relation = "REGIONAL_DIFFERENCE"
                important_diffs.append(f"Scope difference: Regional ({sc_a}) vs Consolidated ({sc_b})")
            else:
                scope_relation = "DIFFERENT_SCOPE"
                important_diffs.append(f"Scope difference: {sc_a} vs {sc_b}")

        # 5. Measurement basis comparison
        b_a = (ctx_a.measurement_basis or "standard").strip().lower() if ctx_a else "standard"
        b_b = (ctx_b.measurement_basis or "standard").strip().lower() if ctx_b else "standard"

        basis_match = (b_a == b_b)
        basis_relation = "SAME_BASIS"
        if not basis_match:
            if any("advance" in x or "fae" in x or "sae" in x for x in (b_a, b_b)):
                basis_relation = "FAE_VS_SAE"
                important_diffs.append(f"Measurement basis revision: First Advance Estimates vs Second Advance Estimates ({ctx_a.measurement_basis} vs {ctx_b.measurement_basis})")
            elif any("gaap" in x or "adjusted" in x or "service" in x for x in (b_a, b_b)):
                basis_relation = "GAAP_VS_NON_GAAP"
                important_diffs.append(f"Accounting basis discrepancy: GAAP Reported vs Non-GAAP Adjusted / Service ({ctx_a.measurement_basis} vs {ctx_b.measurement_basis})")
            elif any("budget" in x for x in (b_a, b_b)):
                basis_relation = "BUDGET_VS_ACTUAL"
                important_diffs.append(f"Basis discrepancy: Budget Estimates vs Actuals ({ctx_a.measurement_basis} vs {ctx_b.measurement_basis})")
            else:
                basis_relation = "DIFFERENT_BASIS"
                important_diffs.append(f"Measurement basis differs: {ctx_a.measurement_basis} vs {ctx_b.measurement_basis}")

        # 6. Polarity comparison
        pol_a = (fact_a.polarity or "positive").strip().lower()
        pol_b = (fact_b.polarity or "positive").strip().lower()
        polarity_match = (pol_a == pol_b)
        if not polarity_match:
            important_diffs.append(f"Opposing polarities: {fact_a.polarity} vs {fact_b.polarity}")

        return ComparisonResult(
            value_match=value_match,
            value_delta_abs=round(delta_abs, 4),
            value_delta_pct=round(delta_pct, 4),
            unit_match=unit_match,
            temporal_match=temporal_match,
            temporal_relation=temporal_relation,
            scope_match=scope_match,
            scope_relation=scope_relation,
            basis_match=basis_match,
            basis_relation=basis_relation,
            polarity_match=polarity_match,
            important_differences=important_diffs
        )
