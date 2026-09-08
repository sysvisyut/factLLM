"""
Entity Canonicalizer mapping raw entity references and aliases to authoritative canonical names.
"""

from typing import Tuple, Optional


class EntityCanonicalizer:
    KNOWN_ENTITIES = {
        "Delhivery Limited": {
            "type": "organization",
            "aliases": ["delhivery", "delhivery limited", "delhivery ltd.", "delhivery ltd", "the company", "company"]
        },
        "Spoton Logistics": {
            "type": "subsidiary",
            "aliases": ["spoton", "spoton logistics", "spoton logistics private limited", "spoton logistics pvt ltd"]
        },
        "Reserve Bank of India": {
            "type": "central_bank",
            "aliases": ["reserve bank of india", "rbi", "reserve bank", "central bank"]
        },
        "Republic of India": {
            "type": "country",
            "aliases": ["republic of india", "india", "indian economy", "government of india", "mof", "ministry of finance"]
        },
        "International Monetary Fund": {
            "type": "multilateral_institution",
            "aliases": ["international monetary fund", "imf", "fund"]
        }
    }

    @classmethod
    def canonicalize(cls, raw_name: Optional[str]) -> Tuple[str, str]:
        """
        Resolves a raw entity string to (canonical_name, entity_type).
        If unknown, returns (title_cased_name, "organization").
        """
        if not raw_name or not raw_name.strip():
            return "Unknown Entity", "unknown"

        clean = raw_name.strip().lower()

        # Check exact alias match
        for canonical, data in cls.KNOWN_ENTITIES.items():
            if clean == canonical.lower() or clean in data["aliases"]:
                return canonical, data["type"]

        # Check substring match
        for canonical, data in cls.KNOWN_ENTITIES.items():
            for alias in data["aliases"]:
                if len(alias) >= 3 and alias in clean:
                    return canonical, data["type"]

        return raw_name.strip().title(), "organization"
