"""
SK Plugin: Check RSA compliance.

Ensures the proposed beat price does not fall below
the RSA floor price (cost + 5% margin, or per-category floor).
"""

from __future__ import annotations

from typing import Any

from backend.data.loader import get_rsa_floor


def check_rsa_compliance(
    category: str,
    proposed_price: float,
    cost_price: float,
    standard_drinks: float = 0.0,
) -> dict[str, Any]:
    """
    Check RSA compliance for a proposed sell price.

    Two checks:
      1. Cost + 5% margin floor
      2. Per-category floor per standard drink (if std drinks > 0)

    Returns dict with: compliant, cost_floor, category_floor, effective_floor, reasoning.
    """
    # Check 1: Cost + 5% margin
    cost_floor = round(cost_price * 1.05, 2)

    # Check 2: Per-category floor per standard drink
    rsa_config = get_rsa_floor(category)
    floor_per_std = rsa_config.get("floor_per_std_drink", 0)

    if standard_drinks > 0 and floor_per_std > 0:
        category_floor = round(floor_per_std * standard_drinks, 2)
    else:
        category_floor = 0.0

    # Effective floor is the higher of the two
    effective_floor = max(cost_floor, category_floor)

    compliant = proposed_price >= effective_floor

    if compliant:
        reasoning = (
            f"Proposed price ${proposed_price:.2f} is above the RSA floor "
            f"${effective_floor:.2f} (cost floor: ${cost_floor:.2f}, "
            f"category floor: ${category_floor:.2f}). Compliant."
        )
    else:
        reasoning = (
            f"Proposed price ${proposed_price:.2f} is BELOW the RSA floor "
            f"${effective_floor:.2f} (cost floor: ${cost_floor:.2f}, "
            f"category floor: ${category_floor:.2f}). NOT compliant."
        )

    return {
        "compliant": compliant,
        "cost_floor": cost_floor,
        "category_floor": category_floor,
        "effective_floor": effective_floor,
        "proposed_price": proposed_price,
        "cost_price": cost_price,
        "category": category,
        "reasoning": reasoning,
    }
