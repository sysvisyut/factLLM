"""
Unified Fact Normalization Service coordinating number scaling, unit canonicalization,
temporal ISO-8601 bounding, entity alias resolution, and deterministic fingerprinting.
"""

from typing import Optional, Dict, Any
from app.schemas.fact import FactBase, FactContextSchema, TimeContext
from app.services.normalization.number_normalizer import NumberNormalizer
from app.services.normalization.unit_normalizer import UnitNormalizer
from app.services.normalization.temporal_normalizer import TemporalNormalizer, NormalizedTime
from app.services.normalization.entity_canonicalizer import EntityCanonicalizer
from app.services.normalization.fingerprint import FactFingerprintGenerator


class FactNormalizationService:
    def __init__(self):
        self.number_normalizer = NumberNormalizer()
        self.unit_normalizer = UnitNormalizer()
        self.temporal_normalizer = TemporalNormalizer()
        self.entity_canonicalizer = EntityCanonicalizer()
        self.fingerprint_generator = FactFingerprintGenerator()

    def normalize_fact_base(self, fact: FactBase) -> FactBase:
        """
        Takes an extracted FactBase schema and applies full normalization in-place or returns updated copy.
        """
        # 1. Entity canonicalization
        raw_subj = fact.subject.canonical or fact.subject.raw or ""
        canonical_subj, entity_type = self.entity_canonicalizer.canonicalize(raw_subj)
        fact.subject.canonical = canonical_subj
        if not fact.subject.type or fact.subject.type == "unknown":
            fact.subject.type = entity_type

        # 2. Unit canonicalization
        raw_unit = fact.value.unit
        canonical_unit = self.unit_normalizer.normalize_unit(
            raw_unit=raw_unit,
            predicate_hint=fact.predicate.canonical
        )
        fact.value.unit = canonical_unit

        # 3. Value normalization and scaling
        raw_val_str = fact.value.raw
        norm_val, multiplier, detected_scale = self.number_normalizer.normalize_number(
            raw_text=raw_val_str,
            unit_hint=raw_unit
        )
        if norm_val is not None:
            fact.value.normalized = norm_val

        # 4. Temporal normalization
        raw_time = fact.context.time.raw if fact.context and fact.context.time else None
        norm_time: NormalizedTime = self.temporal_normalizer.normalize_time(raw_time)
        
        if fact.context:
            fact.context.time.type = norm_time.time_type
            fact.context.time.start = norm_time.time_start.isoformat() if norm_time.time_start else None
            fact.context.time.end = norm_time.time_end.isoformat() if norm_time.time_end else None
            if norm_time.canonical_str and norm_time.canonical_str != "unspecified":
                fact.context.time.raw = norm_time.canonical_str

        # 5. Deterministic fingerprint generation
        time_start = norm_time.time_start
        time_end = norm_time.time_end
        scope = fact.context.scope if fact.context else None
        basis = fact.context.measurement_basis if fact.context else None

        fingerprint = self.fingerprint_generator.generate_fingerprint(
            subject_canonical=canonical_subj,
            predicate_canonical=fact.predicate.canonical,
            scope=scope,
            time_start=time_start,
            time_end=time_end,
            unit_canonical=canonical_unit,
            measurement_basis=basis
        )

        return fact

    def compute_fingerprint_and_blocking(
        self,
        subject_canonical: str,
        predicate_canonical: str,
        scope: Optional[str] = None,
        time_start: Optional[Any] = None,
        time_end: Optional[Any] = None,
        unit_canonical: Optional[str] = None,
        measurement_basis: Optional[str] = None
    ) -> Dict[str, str]:
        """Utility method to get both the exact fingerprint and candidate blocking key."""
        fp = self.fingerprint_generator.generate_fingerprint(
            subject_canonical=subject_canonical,
            predicate_canonical=predicate_canonical,
            scope=scope,
            time_start=time_start,
            time_end=time_end,
            unit_canonical=unit_canonical,
            measurement_basis=measurement_basis
        )
        bk = self.fingerprint_generator.generate_blocking_key(
            subject_canonical=subject_canonical,
            predicate_canonical=predicate_canonical,
            scope=scope
        )
        return {"fingerprint": fp, "blocking_key": bk}
