"""
Executes cross-document relationship resolution across the entire database,
prints breakdown statistics, and audits representative cases.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.session import SessionLocal
from app.services.resolver.service import RelationshipResolverService
from app.models import Relationship, Fact


def main():
    db = SessionLocal()
    service = RelationshipResolverService()

    relationships, summary = service.resolve_cross_document_relationships(db)

    print("==================================================")
    print("CROSS-DOCUMENT RELATIONSHIP RESOLUTION ON STARTER DATASET:")
    print(f"Total Candidate Pairs Evaluated:  {summary['total_candidates_evaluated']}")
    print(f"Total Relationships Established:   {summary['total_relationships_stored']}")
    print("Breakdown of Relationship Types:")
    for rtype, cnt in summary['breakdown'].items():
        if cnt > 0:
            print(f"  • {rtype}: {cnt}")

    print("\nDetailed Audit of Representative Cross-Document Cases:")
    for rtype in ["CORROBORATES", "UNIT_EQUIVALENT", "RECONCILES", "SCOPE_DIFFERENCE", "TEMPORALLY_EVOLVES", "CONTRADICTS"]:
        matching = [r for r in relationships if r.relationship_type == rtype]
        if matching:
            sample = matching[0]
            fa = sample.fact_a
            fb = sample.fact_b
            doc_a = fa.document.filename if fa.document else "Doc A"
            doc_b = fb.document.filename if fb.document else "Doc B"
            print(f"\n--- Case: [{sample.relationship_type}] (Confidence: {sample.confidence}) ---")
            print(f"Fact A ({doc_a}): '{fa.predicate_canonical}' = {fa.value_raw} ({fa.value_normalized} {fa.unit_canonical})")
            print(f"       Scope: {fa.context.scope} | Time: {fa.context.time_raw} | Basis: {fa.context.measurement_basis}")
            print(f"Fact B ({doc_b}): '{fb.predicate_canonical}' = {fb.value_raw} ({fb.value_normalized} {fb.unit_canonical})")
            print(f"       Scope: {fb.context.scope} | Time: {fb.context.time_raw} | Basis: {fb.context.measurement_basis}")
            print(f"Explanation: {sample.explanation}")

    db.close()


if __name__ == "__main__":
    main()
