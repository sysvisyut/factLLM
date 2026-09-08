"""
Number Normalizer for financial, operational, and macroeconomic metrics.
Handles Indian (Crores, Lakhs) and Western (Millions, Billions) scales,
negative accounting notation (parentheses), and currency prefixes.
"""

import re
from typing import Tuple, Optional


class NumberNormalizer:
    # Scale multipliers
    SCALE_FACTORS = {
        "crore": 10_000_000.0,
        "crores": 10_000_000.0,
        "cr": 10_000_000.0,
        "lakh": 100_000.0,
        "lakhs": 100_000.0,
        "lac": 100_000.0,
        "lacs": 100_000.0,
        "thousand": 1_000.0,
        "thousands": 1_000.0,
        "k": 1_000.0,
        "million": 1_000_000.0,
        "millions": 1_000_000.0,
        "mn": 1_000_000.0,
        "m": 1_000_000.0,
        "billion": 1_000_000_000.0,
        "billions": 1_000_000_000.0,
        "bn": 1_000_000_000.0,
        "b": 1_000_000_000.0,
        "trillion": 1_000_000_000_000.0,
        "trillions": 1_000_000_000_000.0,
        "tn": 1_000_000_000_000.0,
    }

    @classmethod
    def normalize_number(
        cls,
        raw_text: str,
        unit_hint: Optional[str] = None
    ) -> Tuple[Optional[float], float, str]:
        """
        Parses raw text containing a number and optional scale/unit.
        Returns:
            (normalized_base_value, scale_multiplier, detected_scale)
        Example:
            "₹8,142 Cr" -> (81420000000.0, 10000000.0, "cr")
            "(127) Cr"  -> (-1270000000.0, 10000000.0, "cr")
            "1.4 Mn"    -> (1400000.0, 1000000.0, "mn")
            "6.4%"      -> (6.4, 1.0, "none")
        """
        if not raw_text:
            return None, 1.0, "none"

        text = raw_text.strip()
        text_lower = text.lower()

        # Check for negative accounting figures in parentheses: (123.45)
        is_negative = False
        paren_match = re.search(r'\(\s*([0-9,]+(?:\.[0-9]+)?)\s*\)', text)
        if paren_match:
            is_negative = True
            num_str = paren_match.group(1)
        else:
            # Check for leading minus
            if "-" in text and not re.search(r'\b[0-9]{4}-[0-9]{2,4}\b', text):
                is_negative = True

            # Extract digits and decimal point
            num_match = re.search(r'([0-9,]+(?:\.[0-9]+)?)', text)
            if not num_match:
                return None, 1.0, "none"
            num_str = num_match.group(1)

        # Clean commas
        clean_num_str = num_str.replace(",", "")
        try:
            val = float(clean_num_str)
        except ValueError:
            return None, 1.0, "none"

        if is_negative:
            val = -abs(val)

        # Detect scale in text or unit_hint
        combined = f"{text_lower} {unit_hint.lower() if unit_hint else ''}"
        
        # Don't scale if it's explicitly a rate or percentage
        if "%" in combined or "percent" in combined or "per cent" in combined:
            return val, 1.0, "none"

        # Search for scale words as whole tokens
        detected_scale = "none"
        multiplier = 1.0

        for scale_name, factor in cls.SCALE_FACTORS.items():
            pattern = rf'\b{re.escape(scale_name)}\b'
            if re.search(pattern, combined):
                detected_scale = scale_name
                multiplier = factor
                break

        normalized_base_value = val * multiplier
        return normalized_base_value, multiplier, detected_scale
