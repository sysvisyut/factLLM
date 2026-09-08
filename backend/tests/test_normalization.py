"""
Unit tests for Fact Normalization, Scale Conversion, Unit Canonicalization,
Temporal Bounding, Entity Canonicalization, and Fact Fingerprinting.
"""

from datetime import date
from app.services.normalization import (
    NumberNormalizer,
    UnitNormalizer,
    TemporalNormalizer,
    EntityCanonicalizer,
    FactFingerprintGenerator,
    FactNormalizationService
)
from app.schemas.fact import (
    FactBase,
    EntityInfo,
    PredicateInfo,
    ValueInfo,
    FactContextSchema,
    TimeContext
)


def test_number_normalizer_scales():
    # Indian Crore (10^7)
    val, mult, scale = NumberNormalizer.normalize_number("₹8,142 Cr")
    assert val == 81_420_000_000.0
    assert mult == 10_000_000.0
    assert scale == "cr"

    # Indian Lakh (10^5)
    val, mult, scale = NumberNormalizer.normalize_number("50 Lakhs")
    assert val == 5_000_000.0
    assert mult == 100_000.0

    # Western Million (10^6)
    val, mult, scale = NumberNormalizer.normalize_number("1.4 Mn Tons")
    assert val == 1_400_000.0
    assert mult == 1_000_000.0

    # Western Billion (10^9)
    val, mult, scale = NumberNormalizer.normalize_number(">2.8 Bn")
    assert val == 2_800_000_000.0
    assert mult == 1_000_000_000.0


def test_number_normalizer_negative_and_percentages():
    # Negative in parentheses (accounting format)
    val, mult, scale = NumberNormalizer.normalize_number("(127) Cr")
    assert val == -1_270_000_000.0

    # Percentage should NOT be multiplied by Crore/Million
    val, mult, scale = NumberNormalizer.normalize_number("6.4%")
    assert val == 6.4
    assert mult == 1.0

    val2, mult2, _ = NumberNormalizer.normalize_number("4.7 per cent", unit_hint="percent")
    assert val2 == 4.7
    assert mult2 == 1.0


def test_unit_normalizer():
    assert UnitNormalizer.normalize_unit("₹") == "INR"
    assert UnitNormalizer.normalize_unit("Rs.") == "INR"
    assert UnitNormalizer.normalize_unit("Cr") == "INR"
    assert UnitNormalizer.normalize_unit("mn tons") == "metric_tonnes"
    assert UnitNormalizer.normalize_unit("express parcel shipments") == "shipments"
    assert UnitNormalizer.normalize_unit("pin codes") == "pin_codes"
    assert UnitNormalizer.normalize_unit("%") == "percent"
    assert UnitNormalizer.normalize_unit("per cent") == "percent"

    # Fallback to predicate hint
    assert UnitNormalizer.normalize_unit(None, predicate_hint="service EBITDA") == "INR"
    assert UnitNormalizer.normalize_unit(None, predicate_hint="real GDP growth rate") == "percent"
    assert UnitNormalizer.normalize_unit(None, predicate_hint="PTL freight tonnage") == "metric_tonnes"


def test_temporal_normalizer():
    # Fiscal Year FY24 (Apr 1, 2023 to Mar 31, 2024)
    t_fy24 = TemporalNormalizer.normalize_time("FY24")
    assert t_fy24.time_type == "fiscal_year"
    assert t_fy24.time_start == date(2023, 4, 1)
    assert t_fy24.time_end == date(2024, 3, 31)
    assert t_fy24.canonical_str == "FY2023-24"

    # Multi-format Fiscal Year (FY2024/25)
    t_fy25 = TemporalNormalizer.normalize_time("FY2024/25")
    assert t_fy25.time_type == "fiscal_year"
    assert t_fy25.time_start == date(2024, 4, 1)
    assert t_fy25.time_end == date(2025, 3, 31)
    assert t_fy25.canonical_str == "FY2024-25"

    # Quarters: Q4 FY24 (Jan 1, 2024 to Mar 31, 2024)
    t_q4 = TemporalNormalizer.normalize_time("Q4 FY24")
    assert t_q4.time_type == "quarter"
    assert t_q4.time_start == date(2024, 1, 1)
    assert t_q4.time_end == date(2024, 3, 31)

    # Quarters: Q1 FY25 (Apr 1, 2024 to Jun 30, 2024)
    t_q1 = TemporalNormalizer.normalize_time("Q1 FY25")
    assert t_q1.time_type == "quarter"
    assert t_q1.time_start == date(2024, 4, 1)
    assert t_q1.time_end == date(2024, 6, 30)

    # Cumulative: since inception
    t_cum = TemporalNormalizer.normalize_time("since inception")
    assert t_cum.time_type == "cumulative"
    assert t_cum.time_start is None
    assert t_cum.time_end is None

    # As-of exact date
    t_date = TemporalNormalizer.normalize_time("March 31, 2024")
    assert t_date.time_type == "as_of"
    assert t_date.time_start == date(2024, 3, 31)
    assert t_date.time_end == date(2024, 3, 31)


def test_entity_canonicalizer():
    assert EntityCanonicalizer.canonicalize("Delhivery Ltd.") == ("Delhivery Limited", "organization")
    assert EntityCanonicalizer.canonicalize("delhivery") == ("Delhivery Limited", "organization")
    assert EntityCanonicalizer.canonicalize("RBI") == ("Reserve Bank of India", "central_bank")
    assert EntityCanonicalizer.canonicalize("Indian Economy") == ("Republic of India", "country")
    assert EntityCanonicalizer.canonicalize("IMF") == ("International Monetary Fund", "multilateral_institution")


def test_fingerprint_generator_determinism_and_blocking():
    fp1 = FactFingerprintGenerator.generate_fingerprint(
        subject_canonical="Delhivery Limited",
        predicate_canonical="revenue from services",
        scope="annual_period",
        time_start=date(2023, 4, 1),
        time_end=date(2024, 3, 31),
        unit_canonical="INR",
        measurement_basis="Standard_Reported"
    )

    fp2 = FactFingerprintGenerator.generate_fingerprint(
        subject_canonical="Delhivery Limited",
        predicate_canonical="revenue from services",
        scope="annual_period",
        time_start=date(2023, 4, 1),
        time_end=date(2024, 3, 31),
        unit_canonical="INR",
        measurement_basis="Standard_Reported"
    )

    # Deterministic matching
    assert fp1 == fp2
    assert len(fp1) == 64

    # Different time produces distinct fingerprint
    fp_diff_time = FactFingerprintGenerator.generate_fingerprint(
        subject_canonical="Delhivery Limited",
        predicate_canonical="revenue from services",
        scope="annual_period",
        time_start=date(2024, 4, 1),
        time_end=date(2025, 3, 31),
        unit_canonical="INR",
        measurement_basis="Standard_Reported"
    )
    assert fp1 != fp_diff_time

    # Blocking keys group related claims
    bk1 = FactFingerprintGenerator.generate_blocking_key("Delhivery Limited", "revenue from services", "annual_period")
    bk2 = FactFingerprintGenerator.generate_blocking_key("delhivery limited", "revenue from services", "annual_period")
    assert bk1 == bk2


def test_fact_normalization_service_end_to_end():
    service = FactNormalizationService()

    raw_fact = FactBase(
        subject=EntityInfo(canonical="Delhivery"),
        predicate=PredicateInfo(canonical="revenue from services", type="financial_metric"),
        value=ValueInfo(raw="₹8,142 Cr", unit="cr"),
        context=FactContextSchema(
            time=TimeContext(raw="FY24"),
            scope="annual_period",
            measurement_basis="Standard_Reported"
        ),
        evidence_id="evidence-123"
    )

    normalized_fact = service.normalize_fact_base(raw_fact)

    assert normalized_fact.subject.canonical == "Delhivery Limited"
    assert normalized_fact.value.unit == "INR"
    assert normalized_fact.value.normalized == 81_420_000_000.0
    assert normalized_fact.context.time.start == "2023-04-01"
    assert normalized_fact.context.time.end == "2024-03-31"
    assert normalized_fact.context.time.raw == "FY2023-24"
