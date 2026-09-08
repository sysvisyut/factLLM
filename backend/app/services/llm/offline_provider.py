import re
from typing import List, Dict, Any, Optional
from app.services.llm.base import LLMProvider
from app.schemas.fact import (
    FactBase,
    EntityInfo,
    PredicateInfo,
    ValueInfo,
    FactContextSchema,
    TimeContext,
    ConfidenceBreakdown
)
from app.schemas.relationship import RelationshipCreate
from app.models.evidence import EvidenceAtom
from app.core.logging import logger


class OfflineHeuristicProvider(LLMProvider):
    """
    Deterministic rule & pattern extractor providing zero-cost, reproducible,
    and grounded fact extraction and relationship reasoning without external APIs.
    """

    def __init__(self):
        # Known entity dictionary
        self.known_entities = {
            "delhivery": {
                "canonical": "Delhivery Limited",
                "type": "organization",
                "aliases": ["Delhivery", "Delhivery Ltd.", "Delhivery Limited", "Company"]
            },
            "spoton": {
                "canonical": "Spoton Logistics",
                "type": "subsidiary",
                "aliases": ["Spoton", "Spoton Logistics Private Limited"]
            },
            "rbi": {
                "canonical": "Reserve Bank of India",
                "type": "central_bank",
                "aliases": ["RBI", "Reserve Bank", "Central Bank"]
            },
            "india": {
                "canonical": "Republic of India",
                "type": "country",
                "aliases": ["India", "Indian Economy", "Government of India", "MoF"]
            },
            "imf": {
                "canonical": "International Monetary Fund",
                "type": "multilateral_institution",
                "aliases": ["IMF", "Fund"]
            }
        }

    def _detect_subject(self, text: str, default_subject: str = "Delhivery Limited") -> EntityInfo:
        text_lower = text.lower()
        if "spoton" in text_lower:
            ent = self.known_entities["spoton"]
            return EntityInfo(canonical=ent["canonical"], type=ent["type"], aliases=ent["aliases"])
        if "delhivery" in text_lower:
            ent = self.known_entities["delhivery"]
            return EntityInfo(canonical=ent["canonical"], type=ent["type"], aliases=ent["aliases"])
        if "reserve bank of india" in text_lower or " rbi " in text_lower or "rbi annual report" in text_lower:
            ent = self.known_entities["rbi"]
            return EntityInfo(canonical=ent["canonical"], type=ent["type"], aliases=ent["aliases"])
        if "international monetary fund" in text_lower or " imf " in text_lower:
            ent = self.known_entities["imf"]
            return EntityInfo(canonical=ent["canonical"], type=ent["type"], aliases=ent["aliases"])
        if "economic survey" in text_lower or "indian economy" in text_lower:
            ent = self.known_entities["india"]
            return EntityInfo(canonical=ent["canonical"], type=ent["type"], aliases=ent["aliases"])
        
        ent = self.known_entities["delhivery"]
        return EntityInfo(canonical=ent["canonical"], type=ent["type"], aliases=ent["aliases"])

    def _detect_time_context(self, text: str) -> TimeContext:
        tc = TimeContext()
        text_lower = text.lower()

        # Fiscal quarters (e.g., Q1 FY25, first quarter of FY2025/26, Q1:2024-25)
        q_match = re.search(r'\b(q[1-4]|first quarter|second quarter|third quarter|fourth quarter)\s*(?:of|:)?\s*(?:fy\s*([0-9]{2,4})|([0-9]{4}))?', text_lower)
        if q_match:
            q_raw = q_match.group(1).upper()
            q_map = {"FIRST QUARTER": "Q1", "SECOND QUARTER": "Q2", "THIRD QUARTER": "Q3", "FOURTH QUARTER": "Q4"}
            q_code = q_map.get(q_raw, q_raw)
            yr = q_match.group(2) or q_match.group(3) or "2024"
            if len(yr) == 2:
                yr = "20" + yr
            tc.type = "quarter"
            tc.raw = f"{q_code} FY{yr[-2:]}"
            return tc

        # Fiscal year (e.g. FY24, FY2024/25, FY2024-25, FY25)
        fy_match = re.search(r'\b(?:fy\s*([0-9]{2,4})(?:[-/]([0-9]{2,4}))?|fiscal\s*(?:year\s*)?([0-9]{4}))\b', text_lower)
        if fy_match:
            yr = fy_match.group(1) or fy_match.group(3)
            yr2 = fy_match.group(2)
            if len(yr) == 2:
                yr = "20" + yr
            tc.type = "fiscal_year"
            tc.raw = f"FY{yr[-2:]}{f'-{yr2[-2:]}' if yr2 else ''}"
            return tc

        # Year range without explicit FY (e.g. 2024-25, 2024/25)
        yr_range = re.search(r'\b(202[0-9])[-/](2[0-9])\b', text)
        if yr_range:
            tc.type = "fiscal_year"
            tc.raw = f"FY{yr_range.group(1)[-2:]}-{yr_range.group(2)}"
            return tc

        # Since inception
        if "since inception" in text_lower:
            tc.type = "cumulative"
            tc.raw = "since inception"
            return tc

        # As of date
        as_of_match = re.search(r'as\s+of\s+([a-zA-Z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[a-zA-Z]+\s+\d{4})', text_lower)
        if as_of_match:
            tc.type = "as_of"
            tc.raw = as_of_match.group(1).title()
            return tc

        # Standalone 4-digit year
        yr_match = re.search(r'\b(201[89]|202[0-9])\b', text)
        if yr_match:
            tc.type = "calendar_year"
            tc.raw = yr_match.group(1)
            return tc

        return tc

    def _detect_scope(self, text: str) -> str:
        text_lower = text.lower()
        if "since inception" in text_lower or "cumulative" in text_lower:
            return "cumulative_since_inception"
        if "spoton" in text_lower:
            return "subsidiary"
        if "north america" in text_lower:
            return "regional_north_america"
        if "q4" in text_lower or "q1" in text_lower or "q2" in text_lower or "q3" in text_lower:
            return "quarterly_period"
        if "fy" in text_lower or "annual" in text_lower or "fiscal" in text_lower:
            return "annual_period"
        return "consolidated_company"

    def _detect_measurement_basis(self, text: str) -> str:
        text_lower = text.lower()
        if "first advance estimate" in text_lower or "fae" in text_lower:
            return "First_Advance_Estimates"
        if "second advance estimate" in text_lower or "sae" in text_lower:
            return "Second_Advance_Estimates"
        if "provisional estimate" in text_lower:
            return "Provisional_Estimates"
        if "revised estimate" in text_lower:
            return "Revised_Estimates"
        if "budget estimate" in text_lower or "budgeted" in text_lower:
            return "Budget_Estimates"
        if "service ebitda" in text_lower:
            return "Service_EBITDA"
        if "adj. ebitda" in text_lower or "adjusted ebitda" in text_lower:
            return "Non-GAAP_Adjusted"
        if "pro forma" in text_lower or "pro-forma" in text_lower:
            return "Pro_forma"
        if "ebitda" in text_lower:
            return "GAAP_Reported"
        if "constant currency" in text_lower:
            return "Constant_Currency"
        return "Standard_Reported"

    def extract_facts(
        self,
        text: str,
        page_number: int,
        evidence_atoms: List[EvidenceAtom]
    ) -> List[FactBase]:
        """Extracts structured claims from page evidence using high-precision metric matchers."""
        facts: List[FactBase] = []
        subject_info = self._detect_subject(text)

        # Metric definitions: (Predicate, Type, [Regex Patterns], Default Unit)
        metric_definitions = [
            (
                "revenue from services",
                "financial_metric",
                [
                    r'(?:(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion)?|([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion))\s*(?:in\s*)?(?:(?:fy|q[1-4])[0-9]{2,4}\s*)?revenue',
                    r'(?:revenue(?:\s+from\s+services)?)[^\w\n\r]*[:=]?\s*(?:(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion)?|([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion))'
                ],
                "INR"
            ),
            (
                "service EBITDA",
                "financial_metric",
                [
                    r'(?:(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion)?|([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion))\s*service\s+ebitda',
                    r'service\s+ebitda[^\w\n\r]*[:=]?\s*(?:(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion)?|([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion))'
                ],
                "INR"
            ),
            (
                "adjusted EBITDA",
                "financial_metric",
                [
                    r'(?:(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion)?|([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion))\s*(?:/\s*[0-9.]+%\s*)?(?:(?:in\s*)?(?:fy|q[1-4])[0-9]{2,4}\s*)?adj\.?\s*ebitda',
                    r'(?:adj\.?|adjusted)\s+ebitda[^\w\n\r]*[:=]?\s*(?:(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion)?|([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion))'
                ],
                "INR"
            ),
            (
                "EBITDA",
                "financial_metric",
                [
                    r'(?:(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion)?|([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion))\s*(?:/\s*[0-9.]+%\s*)?(?:(?:in\s*)?(?:fy|q[1-4])[0-9]{2,4}\s*)?\bebitda\b',
                    r'\bebitda\b[^\w\n\r]*[:=]?\s*(?:(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion)?|([0-9,]+(?:\.[0-9]+)?)\s*(cr|crore|million|mn|bn|billion))'
                ],
                "INR"
            ),
            (
                "express parcel shipments volume",
                "operational_metric",
                [
                    r'(?:>|>=)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(bn|billion|mn|million)\+?\s*(?:\([0-9,]+\)\s*)?express\s+parcel\s+shipments',
                    r'express\s+parcel\s+(?:shipments|shipment\s+volume)[^\w\n\r]*[:=]?\s*(?:>|>=)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(bn|billion|mn|million)'
                ],
                "shipments"
            ),
            (
                "PTL freight tonnage",
                "operational_metric",
                [
                    r'([0-9,]+(?:\.[0-9]+)?)\s*(mn\s*tons|thousand\s*tonnes|tonnes|k\s*tons|tons)\+?\s*(?:\([0-9,]+\)\s*)?(?:part-truckload|ptl)',
                    r'(?:part-truckload|ptl)(?:\s+freight)?\s+tonnage[^\w\n\r]*[:=]?\s*([0-9,]+(?:\.[0-9]+)?)\s*(mn\s*tons|thousand\s*tonnes|tonnes|k\s*tons|tons)'
                ],
                "tonnes"
            ),
            (
                "pin codes covered",
                "operational_metric",
                [
                    r'([0-9,]{4,6})\s*(?:\([0-9,]+\)\s*)?pin\s*codes',
                    r'pin\s*codes\s*(?:covered)?[^\w\n\r]*[:=]?\s*([0-9,]{4,6})'
                ],
                "pin_codes"
            ),
            (
                "last-mile delivery centres",
                "operational_metric",
                [
                    r'([0-9,]{3,6})\s*(?:\([0-9,]+\)\s*)?last-mile\s+delivery\s+centres',
                    r'last-mile\s+delivery\s+centres[^\w\n\r]*[:=]?\s*([0-9,]{3,6})'
                ],
                "centres"
            ),
            (
                "count of 46-ft tractors",
                "operational_metric",
                [
                    r'([0-9,]{2,5})\s*(?:\([0-9,]+\)\s*)?(?:count\s+of\s+)?46-ft\s+tractors',
                    r'(?:count\s+of\s+46-ft\s+tractors|tractors)[^\w\n\r]*[:=]?\s*([0-9,]{2,5})'
                ],
                "vehicles"
            ),
            (
                "workforce strength",
                "operational_metric",
                [
                    r'([0-9,]{4,6})\s*(?:\([0-9,]+\)\s*)?workforce\s+strength',
                    r'workforce\s+strength[^\w\n\r]*[:=]?\s*([0-9,]{4,6})'
                ],
                "persons"
            ),
            (
                "logistics area under management",
                "operational_metric",
                [
                    r'([0-9,]+(?:\.[0-9]+)?)\s*(mn\s*sq\s*ft|sq\s*ft)\s*(?:\([0-9,]+\)\s*)?logistics\s+area',
                    r'logistics\s+area\s+under\s+management[^\w\n\r]*[:=]?\s*([0-9,]+(?:\.[0-9]+)?)\s*(mn\s*sq\s*ft|sq\s*ft)'
                ],
                "sq_ft"
            ),
            (
                "real GDP growth rate",
                "macroeconomic_metric",
                [
                    r'(?:real\s+(?:gross\s+domestic\s+product|\(gdp\)|gdp)[^.\n]{0,60}?(?:grow(?:th)?|expanded|moderated|projected)[^.\n]{0,30}?(?:by|to|at|of)?\s*([0-9]+(?:\.[0-9]+)?)\s*(%|per\s*cent))',
                    r'(?:economic\s+growth)[^.\n]{0,30}?(?:of|at|by|to)?\s*([0-9]+(?:\.[0-9]+)?)\s*(%|per\s*cent)',
                    r'([0-9]+(?:\.[0-9]+)?)\s*(%|per\s*cent)\s*(?:real\s+gdp\s+growth|gdp\s+growth)',
                    r'(?:real\s+gdp\s+growth|gdp\s+growth)[^\w\n\r]*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(%|per\s*cent)'
                ],
                "percent"
            ),
            (
                "headline CPI inflation",
                "macroeconomic_metric",
                [
                    r'(?:(?:headline\s+)?cpi\s+inflation|retail\s+inflation|headline\s+inflation)[^.\n]{0,30}?(?:declined\s+to|moderated\s+to|stood\s+at|at|of|to)?\s*([0-9]+(?:\.[0-9]+)?)\s*(%|per\s*cent)',
                    r'([0-9]+(?:\.[0-9]+)?)\s*(%|per\s*cent)\s*(?:headline\s+cpi\s+inflation|cpi\s+inflation|retail\s+inflation)'
                ],
                "percent"
            ),
            (
                "gross fiscal deficit",
                "macroeconomic_metric",
                [
                    r'(?:(?:gross\s+)?fiscal\s+deficit|gfd)[^.\n]{0,40}?(?:declining\s+to|contained\s+at|budgeted\s+at|stood\s+at|at|of)?\s*([0-9]+(?:\.[0-9]+)?)\s*(%|per\s*cent)\s*(?:of\s+gdp)?',
                    r'([0-9]+(?:\.[0-9]+)?)\s*(%|per\s*cent)\s*(?:of\s+gdp\s+)?(?:fiscal\s+deficit|gfd)'
                ],
                "percent"
            ),
            (
                "current account deficit",
                "macroeconomic_metric",
                [
                    r'(?:current\s+account\s+deficit|cad)[^.\n]{0,40}?(?:contained\s+at|declined\s+to|widened\s+to|projected\s+at|at|of)?\s*([0-9]+(?:\.[0-9]+)?)\s*(%|per\s*cent)\s*(?:of\s+gdp)?',
                    r'([0-9]+(?:\.[0-9]+)?)\s*(%|per\s*cent)\s*(?:of\s+gdp\s+)?(?:current\s+account\s+deficit|cad)'
                ],
                "percent"
            )
        ]

        for atom in evidence_atoms:
            atom_text = atom.exact_text
            atom_inline = " ".join(atom_text.split()).lower()

            for pred_name, pred_type, patterns, default_unit in metric_definitions:
                for pattern in patterns:
                    match = re.search(pattern, atom_inline)
                    if not match:
                        continue

                    # Extract non-None capture groups
                    valid_groups = [g for g in match.groups() if g is not None]
                    if not valid_groups:
                        continue

                    # Number is the group that has digits
                    num_candidate = None
                    unit_candidate = default_unit
                    for g in valid_groups:
                        if any(c.isdigit() for c in g):
                            num_candidate = g
                        elif not any(c.isdigit() for c in g) and g.strip():
                            unit_candidate = g.strip()

                    if not num_candidate:
                        continue

                    num_clean = num_candidate.replace(",", "")
                    try:
                        normalized_float = float(num_clean)
                    except ValueError:
                        continue

                    full_raw_val = f"{num_candidate} {unit_candidate if unit_candidate else ''}".strip()

                    time_ctx = self._detect_time_context(atom_text)
                    scope_str = self._detect_scope(atom_text)
                    basis_str = self._detect_measurement_basis(atom_text)

                    # Dynamic Subject assignment: Macro metrics belong to Republic of India
                    if pred_type == "macroeconomic_metric":
                        subj = EntityInfo(
                            canonical=self.known_entities["india"]["canonical"],
                            type=self.known_entities["india"]["type"],
                            aliases=self.known_entities["india"]["aliases"]
                        )
                        scope_str = "national_economy"
                    else:
                        subj = subject_info

                    context_obj = FactContextSchema(
                        time=time_ctx,
                        geography="India",
                        scope=scope_str,
                        population=None,
                        measurement_basis=basis_str,
                        qualifiers=[]
                    )

                    polarity = "positive"
                    if "loss" in atom_inline or "reduction" in atom_inline or "deficit" in atom_inline:
                        polarity = "negative"

                    fact = FactBase(
                        subject=subj,
                        predicate=PredicateInfo(canonical=pred_name, type=pred_type),
                        value=ValueInfo(
                            raw=full_raw_val,
                            normalized=normalized_float,
                            unit=unit_candidate,
                            value_type="currency" if default_unit == "INR" else "numeric"
                        ),
                        context=context_obj,
                        polarity=polarity,
                        confidence=ConfidenceBreakdown(
                            extraction=0.98,
                            normalization=0.95,
                            overall=0.96,
                            level="HIGH"
                        ),
                        evidence_id=atom.id
                    )
                    facts.append(fact)
                    break  # Matched this predicate, continue to check remaining predicates

        return facts

    def resolve_relationship(
        self,
        fact_a: Dict[str, Any],
        fact_b: Dict[str, Any]
    ) -> RelationshipCreate:
        """Determines relationship type and multi-dimensional difference analysis."""
        # Stage C multidimensional logic will be invoked in Phase 6
        return RelationshipCreate(
            fact_a_id=fact_a["id"],
            fact_b_id=fact_b["id"],
            relationship_type="UNCERTAIN",
            confidence=0.5,
            explanation="Preliminary unresolved relationship.",
            dimensions={},
            important_differences=[],
            reasoning_basis="deterministic"
        )

    def generate_explanation(
        self,
        fact_a: Dict[str, Any],
        fact_b: Dict[str, Any],
        dimensions: Dict[str, str],
        rel_type: str
    ) -> str:
        return f"Relationship {rel_type} established across dimensions: {dimensions}."
