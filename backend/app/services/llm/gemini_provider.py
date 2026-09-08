import os
import json
import httpx
from typing import List, Dict, Any, Optional
from app.services.llm.base import LLMProvider
from app.services.llm.offline_provider import OfflineHeuristicProvider
from app.schemas.fact import FactBase
from app.schemas.relationship import RelationshipCreate
from app.models.evidence import EvidenceAtom
from app.core.config import settings
from app.core.logging import logger


class GeminiLLMProvider(LLMProvider):
    """Google Gemini structured JSON provider with fallback to offline provider."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.fallback = OfflineHeuristicProvider()

    def extract_facts(
        self,
        text: str,
        page_number: int,
        evidence_atoms: List[EvidenceAtom]
    ) -> List[FactBase]:
        if not self.api_key:
            logger.debug("GEMINI_API_KEY not set. Using offline deterministic provider.")
            return self.fallback.extract_facts(text, page_number, evidence_atoms)

        # Build structured prompt for Gemini
        evidence_snippets = [
            {"id": a.id, "text": a.exact_text}
            for a in evidence_atoms[:10]
        ]
        
        prompt = f"""You are a precise fact extraction system.
Analyze the following source evidence from page {page_number} and extract structured facts.
Do NOT fabricate facts. Every fact MUST reference an exact evidence ID from the list.
Output a JSON array of FactBase objects matching this schema:
{{
  "subject": {{"canonical": "...", "type": "organization|country|person", "aliases": []}},
  "predicate": {{"canonical": "...", "type": "financial_metric|operational_metric|macroeconomic_metric"}},
  "value": {{"raw": "...", "normalized": float_or_null, "unit": "...", "value_type": "numeric|currency|ratio"}},
  "context": {{"time": {{"type": "...", "raw": "..."}}, "scope": "...", "measurement_basis": "..."}},
  "polarity": "positive|negative",
  "evidence_id": "EXACT_ID_FROM_LIST"
}}

Evidence list:
{json.dumps(evidence_snippets, indent=2)}
"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            response = httpx.post(url, json=payload, timeout=30.0)
            if response.status_code == 200:
                result_json = response.json()
                text_content = result_json["candidates"][0]["content"]["parts"][0]["text"]
                raw_facts = json.loads(text_content)
                validated_facts = [FactBase.model_validate(f) for f in raw_facts]
                return validated_facts
            else:
                logger.warning(f"Gemini API returned status {response.status_code}: {response.text}")
                return self.fallback.extract_facts(text, page_number, evidence_atoms)
        except Exception as e:
            logger.warning(f"Gemini extraction call failed: {e}. Falling back to offline provider.")
            return self.fallback.extract_facts(text, page_number, evidence_atoms)

    def resolve_relationship(
        self,
        fact_a: Dict[str, Any],
        fact_b: Dict[str, Any]
    ) -> RelationshipCreate:
        return self.fallback.resolve_relationship(fact_a, fact_b)

    def generate_explanation(
        self,
        fact_a: Dict[str, Any],
        fact_b: Dict[str, Any],
        dimensions: Dict[str, str],
        rel_type: str
    ) -> str:
        return self.fallback.generate_explanation(fact_a, fact_b, dimensions, rel_type)
