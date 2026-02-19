"""
URLValidationAgent — Validate competitor URL against allow-list.

Rule-based (no LLM needed). Checks URL domain against known competitors.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Allowed competitor domains
ALLOWED_DOMAINS = {
    "liquorland.com.au": "liquorland",
    "www.liquorland.com.au": "liquorland",
    "boozebud.com": "boozebud",
    "www.boozebud.com": "boozebud",
    "boozebud.com.au": "boozebud",
    "www.boozebud.com.au": "boozebud",
}


async def run_url_validation_agent(
    url: Optional[str],
) -> tuple[dict[str, Any], str]:
    """
    Validate a competitor URL against the allow-list.

    Returns (result_dict, inference_mode).
    inference_mode is always "real" since this is rule-based.
    """
    if not url:
        return {
            "url": None,
            "is_valid": True,
            "competitor": None,
            "domain_match": False,
            "reason": "No URL provided — will use CSV fallback for competitor data.",
        }, "real"

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Strip port if present
        if ":" in domain:
            domain = domain.split(":")[0]

        competitor = ALLOWED_DOMAINS.get(domain)

        if competitor:
            # Detect warehouse variant
            if competitor == "liquorland" and "/warehouse" in parsed.path.lower():
                competitor = "liquorland_warehouse"

            return {
                "url": url,
                "is_valid": True,
                "competitor": competitor,
                "domain_match": True,
                "reason": f"URL matches allowed competitor domain: {domain}",
            }, "real"
        else:
            return {
                "url": url,
                "is_valid": False,
                "competitor": None,
                "domain_match": False,
                "reason": f"Domain '{domain}' is not in our allowed competitor list. "
                          f"We currently support: liquorland.com.au, boozebud.com",
            }, "real"

    except Exception as e:
        return {
            "url": url,
            "is_valid": False,
            "competitor": None,
            "domain_match": False,
            "reason": f"Invalid URL format: {e}",
        }, "real"
