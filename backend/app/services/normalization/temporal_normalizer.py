"""
Temporal Normalizer for fiscal years, fiscal quarters, calendar years, exact dates, and cumulative periods.
Standardizes Indian and International fiscal time conventions into ISO-8601 Date ranges.
"""

import re
from datetime import date
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class NormalizedTime:
    time_type: str                  # 'fiscal_year', 'quarter', 'calendar_year', 'as_of', 'cumulative', 'unspecified'
    time_start: Optional[date]
    time_end: Optional[date]
    canonical_str: str              # e.g. "FY2023-24", "Q4 FY2023-24", "since_inception"
    raw: str


class TemporalNormalizer:
    MONTH_MAP = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
        "jul": 7, "july": 7, "aug": 8, "august": 8, "sep": 9, "september": 9,
        "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12
    }

    @classmethod
    def normalize_time(cls, raw_time: Optional[str]) -> NormalizedTime:
        """
        Parses arbitrary temporal expressions into structured Date boundaries and canonical strings.
        """
        if not raw_time or not raw_time.strip():
            return NormalizedTime(
                time_type="unspecified",
                time_start=None,
                time_end=None,
                canonical_str="unspecified",
                raw=raw_time or ""
            )

        text = raw_time.strip()
        text_lower = text.lower()

        # 1. Cumulative / Since inception
        if "since inception" in text_lower or "cumulative" in text_lower:
            return NormalizedTime(
                time_type="cumulative",
                time_start=None,
                time_end=None,
                canonical_str="since_inception",
                raw=text
            )

        # 2. Fiscal Quarters (e.g. Q4 FY24, Q1 FY25, Q1:2024-25, first quarter of FY2025/26)
        q_match = re.search(
            r'\b(q[1-4]|first quarter|second quarter|third quarter|fourth quarter)\s*(?:of|:)?\s*(?:fy\s*([0-9]{2,4})|([0-9]{4}))?',
            text_lower
        )
        if q_match:
            q_raw = q_match.group(1).upper()
            q_name_map = {
                "FIRST QUARTER": "Q1",
                "SECOND QUARTER": "Q2",
                "THIRD QUARTER": "Q3",
                "FOURTH QUARTER": "Q4"
            }
            q_code = q_name_map.get(q_raw, q_raw)
            yr_str = q_match.group(2) or q_match.group(3) or "2024"
            yr = int(yr_str) if len(yr_str) == 4 else 2000 + int(yr_str)

            # Indian fiscal year FY(yr) ends in year `yr` and begins in `yr-1`
            # Q1: Apr-Jun (yr-1)
            # Q2: Jul-Sep (yr-1)
            # Q3: Oct-Dec (yr-1)
            # Q4: Jan-Mar (yr)
            start_yr = yr - 1
            if q_code == "Q1":
                t_start = date(start_yr, 4, 1)
                t_end = date(start_yr, 6, 30)
            elif q_code == "Q2":
                t_start = date(start_yr, 7, 1)
                t_end = date(start_yr, 9, 30)
            elif q_code == "Q3":
                t_start = date(start_yr, 10, 1)
                t_end = date(start_yr, 12, 31)
            else:  # Q4
                t_start = date(yr, 1, 1)
                t_end = date(yr, 3, 31)

            canonical = f"{q_code} FY{start_yr}-{str(yr)[-2:]}"
            return NormalizedTime(
                time_type="quarter",
                time_start=t_start,
                time_end=t_end,
                canonical_str=canonical,
                raw=text
            )

        # 3. Fiscal Year Range (e.g. FY2024-25, FY2024/25, 2024-25, FY24-25)
        range_match = re.search(r'\b(?:fy\s*)?([0-9]{2,4})[-/]([0-9]{2,4})\b', text_lower)
        if range_match:
            y1_str, y2_str = range_match.group(1), range_match.group(2)
            y1 = int(y1_str) if len(y1_str) == 4 else 2000 + int(y1_str)
            y2 = int(y2_str) if len(y2_str) == 4 else 2000 + int(y2_str)
            t_start = date(y1, 4, 1)
            t_end = date(y2, 3, 31)
            canonical = f"FY{y1}-{str(y2)[-2:]}"
            return NormalizedTime(
                time_type="fiscal_year",
                time_start=t_start,
                time_end=t_end,
                canonical_str=canonical,
                raw=text
            )

        # 4. Single Fiscal Year (e.g. FY24, FY2024, FY25, fiscal 2024)
        single_fy = re.search(r'\b(?:fy\s*([0-9]{2,4})|fiscal\s*(?:year\s*)?([0-9]{4}))\b', text_lower)
        if single_fy:
            yr_str = single_fy.group(1) or single_fy.group(2)
            end_yr = int(yr_str) if len(yr_str) == 4 else 2000 + int(yr_str)
            start_yr = end_yr - 1
            t_start = date(start_yr, 4, 1)
            t_end = date(end_yr, 3, 31)
            canonical = f"FY{start_yr}-{str(end_yr)[-2:]}"
            return NormalizedTime(
                time_type="fiscal_year",
                time_start=t_start,
                time_end=t_end,
                canonical_str=canonical,
                raw=text
            )

        # 5. As-of date (e.g. As of March 31, 2024 or 31 March 2024)
        date_match = re.search(
            r'(?:as\s+of\s+)?([a-zA-Z]+)\s+(\d{1,2}),?\s+(\d{4})',
            text_lower
        )
        if not date_match:
            date_match = re.search(
                r'(?:as\s+of\s+)?(\d{1,2})\s+([a-zA-Z]+),?\s+(\d{4})',
                text_lower
            )
            if date_match:
                d_day = int(date_match.group(1))
                m_str = date_match.group(2)
                d_yr = int(date_match.group(3))
            else:
                d_day, m_str, d_yr = None, None, None
        else:
            m_str = date_match.group(1)
            d_day = int(date_match.group(2))
            d_yr = int(date_match.group(3))

        if m_str and m_str in cls.MONTH_MAP and d_day and d_yr:
            d_month = cls.MONTH_MAP[m_str]
            exact_d = date(d_yr, d_month, d_day)
            canonical = exact_d.isoformat()
            return NormalizedTime(
                time_type="as_of",
                time_start=exact_d,
                time_end=exact_d,
                canonical_str=canonical,
                raw=text
            )

        # 6. Standalone 4-digit Calendar Year (e.g. 2024, 2025)
        cal_match = re.search(r'\b(201[89]|202[0-9])\b', text)
        if cal_match:
            c_yr = int(cal_match.group(1))
            return NormalizedTime(
                time_type="calendar_year",
                time_start=date(c_yr, 1, 1),
                time_end=date(c_yr, 12, 31),
                canonical_str=f"CY{c_yr}",
                raw=text
            )

        # Fallback
        return NormalizedTime(
            time_type="unspecified",
            time_start=None,
            time_end=None,
            canonical_str=text,
            raw=text
        )
