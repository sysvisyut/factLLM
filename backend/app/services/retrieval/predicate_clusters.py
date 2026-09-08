"""
Predicate Clusters and Family Classification.
Maps fine-grained predicate variants across documents into unified conceptual metric families
for candidate blocking and cross-document reasoning.
"""

from typing import Dict, Set


class PredicateClusterRegistry:
    PREDICATE_FAMILIES: Dict[str, Set[str]] = {
        "REVENUE": {
            "revenue from services",
            "revenue",
            "total revenue",
            "turnover",
            "sales",
            "topline",
            "revenue from operations"
        },
        "EBITDA": {
            "ebitda",
            "service ebitda",
            "adjusted ebitda",
            "adj. ebitda",
            "operating profit",
            "operating ebitda"
        },
        "FREIGHT_VOLUME": {
            "ptl freight tonnage",
            "freight tonnage",
            "freight volume",
            "part-truckload tonnage",
            "part truckload volume"
        },
        "PARCEL_VOLUME": {
            "express parcel shipments volume",
            "parcel volume",
            "shipments volume",
            "express parcel volume",
            "shipments"
        },
        "NETWORK_REACH": {
            "pin codes covered",
            "pincodes covered",
            "pin codes",
            "network reach",
            "coverage"
        },
        "DELIVERY_CENTRES": {
            "last-mile delivery centres",
            "delivery centres",
            "centres",
            "delivery hubs"
        },
        "FLEET_SIZE": {
            "count of 46-ft tractors",
            "tractors",
            "fleet size",
            "vehicles",
            "tractor fleet"
        },
        "WORKFORCE": {
            "workforce strength",
            "workforce",
            "employee count",
            "headcount",
            "total workforce"
        },
        "LOGISTICS_AREA": {
            "logistics area under management",
            "logistics area",
            "warehouse area",
            "infrastructure area"
        },
        "GDP_GROWTH": {
            "real gdp growth rate",
            "gdp growth",
            "real gdp growth",
            "economic growth",
            "growth rate of gdp"
        },
        "INFLATION": {
            "headline cpi inflation",
            "cpi inflation",
            "retail inflation",
            "headline inflation",
            "inflation rate"
        },
        "FISCAL_DEFICIT": {
            "gross fiscal deficit",
            "fiscal deficit",
            "gfd",
            "central fiscal deficit"
        },
        "CURRENT_ACCOUNT_DEFICIT": {
            "current account deficit",
            "cad",
            "current account balance"
        }
    }


def get_predicate_family(predicate: str) -> str:
    """
    Returns the uppercase predicate family name for a given predicate string.
    If not in a known family, normalizes the predicate into a sanitized family identifier.
    """
    if not predicate:
        return "UNKNOWN_FAMILY"

    p_clean = predicate.strip().lower()

    for family, members in PredicateClusterRegistry.PREDICATE_FAMILIES.items():
        if p_clean in members:
            return family
        # Check if member is substring of p_clean or vice versa
        for m in members:
            if len(m) >= 4 and (m in p_clean or p_clean in m):
                return family

    return p_clean.replace(" ", "_").upper()
