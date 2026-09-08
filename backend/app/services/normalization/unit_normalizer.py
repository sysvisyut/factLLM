"""
Unit Normalizer for standardizing currency, physical volume, operational metrics, and percentages.
"""

import re
from typing import Optional


class UnitNormalizer:
    # Mapping of raw unit patterns to canonical unit strings
    CANONICAL_UNITS = {
        # Currencies
        "inr": "INR",
        "rs": "INR",
        "rs.": "INR",
        "₹": "INR",
        "rupees": "INR",
        "cr": "INR",
        "crore": "INR",
        "crores": "INR",
        "lakh": "INR",
        "lakhs": "INR",
        "usd": "USD",
        "$": "USD",
        "dollar": "USD",
        "dollars": "USD",

        # Macro & Rates
        "percent": "percent",
        "per cent": "percent",
        "%": "percent",
        "pct": "percent",
        "bps": "basis_points",
        "basis points": "basis_points",

        # Logistics & Operational
        "tonnes": "metric_tonnes",
        "tons": "metric_tonnes",
        "mn tons": "metric_tonnes",
        "metric tonnes": "metric_tonnes",
        "metric tons": "metric_tonnes",
        "k tons": "metric_tonnes",

        "shipments": "shipments",
        "parcels": "shipments",
        "express parcel shipments": "shipments",
        "bn": "shipments",

        "pin codes": "pin_codes",
        "pin_codes": "pin_codes",
        "pincodes": "pin_codes",

        "centres": "centres",
        "centers": "centres",
        "delivery centres": "centres",

        "vehicles": "vehicles",
        "tractors": "vehicles",
        "46-ft tractors": "vehicles",
        "trucks": "vehicles",

        "persons": "persons",
        "people": "persons",
        "employees": "persons",
        "workforce": "persons",

        "sq ft": "sq_ft",
        "sq_ft": "sq_ft",
        "sq. ft.": "sq_ft",
        "mn sq ft": "sq_ft",
        "million sq ft": "sq_ft",

        "days": "days",
    }

    @classmethod
    def normalize_unit(cls, raw_unit: Optional[str], predicate_hint: Optional[str] = None) -> Optional[str]:
        """
        Normalizes a raw unit or derives a canonical unit from a predicate hint.
        Examples:
            "₹" -> "INR"
            "Cr" -> "INR"
            "mn tons" -> "metric_tonnes"
            "pin codes" -> "pin_codes"
            "%" -> "percent"
        """
        if raw_unit:
            clean = raw_unit.strip().lower()
            if clean in cls.CANONICAL_UNITS:
                return cls.CANONICAL_UNITS[clean]
            
            # Substring matching for multi-word or compound strings
            for pattern, canonical in cls.CANONICAL_UNITS.items():
                if re.search(rf'\b{re.escape(pattern)}\b', clean):
                    return canonical

        # Fallback to predicate hint
        if predicate_hint:
            pred_lower = predicate_hint.lower()
            if any(term in pred_lower for term in ["revenue", "ebitda", "profit", "loss", "pat", "expenditure"]):
                return "INR"
            if any(term in pred_lower for term in ["growth", "inflation", "deficit", "rate", "margin", "share"]):
                return "percent"
            if "tonnage" in pred_lower or "freight" in pred_lower:
                return "metric_tonnes"
            if "parcel" in pred_lower or "shipment" in pred_lower:
                return "shipments"
            if "pin code" in pred_lower:
                return "pin_codes"
            if "tractor" in pred_lower:
                return "vehicles"
            if "centre" in pred_lower or "center" in pred_lower:
                return "centres"
            if "area" in pred_lower:
                return "sq_ft"
            if "workforce" in pred_lower:
                return "persons"

        return raw_unit.strip() if raw_unit else None
