"""
Deterministic Fact Fingerprint & Blocking Key Generator.
Constructs cryptographically stable SHA-256 fingerprints to identify identical metric claims
across documents, and coarse blocking keys for candidate retrieval.
"""

import hashlib
from typing import Optional
from datetime import date


class FactFingerprintGenerator:
    @staticmethod
    def generate_fingerprint(
        subject_canonical: str,
        predicate_canonical: str,
        scope: Optional[str] = None,
        time_start: Optional[date] = None,
        time_end: Optional[date] = None,
        unit_canonical: Optional[str] = None,
        measurement_basis: Optional[str] = None
    ) -> str:
        """
        Generates a deterministic 64-character SHA-256 fingerprint representing
        the exact semantic coordinates of a claim.
        """
        subj = (subject_canonical or "").strip().lower()
        pred = (predicate_canonical or "").strip().lower()
        sc = (scope or "consolidated").strip().lower()
        t_start = time_start.isoformat() if time_start else "none"
        t_end = time_end.isoformat() if time_end else "none"
        unit = (unit_canonical or "none").strip().lower()
        basis = (measurement_basis or "standard").strip().lower()

        canonical_string = f"{subj}|{pred}|{sc}|{t_start}|{t_end}|{unit}|{basis}"
        return hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_blocking_key(
        subject_canonical: str,
        predicate_canonical: str,
        scope: Optional[str] = None
    ) -> str:
        """
        Generates a coarse blocking key for candidate retrieval indexing (Phase 5).
        Groups facts that measure the same metric on the same entity and scope.
        """
        subj = (subject_canonical or "").strip().lower()
        pred = (predicate_canonical or "").strip().lower()
        sc = (scope or "consolidated").strip().lower()

        return f"{subj}::{pred}::{sc}"
