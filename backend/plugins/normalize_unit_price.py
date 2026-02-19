"""
SK Plugin: Normalize unit price.

Converts prices to per-litre for fair comparison across
different pack sizes and volumes.
"""

from __future__ import annotations

from typing import Any


def normalize_unit_price(
    price: float,
    volume_ml: int,
    pack_size: int,
) -> dict[str, Any]:
    """
    Normalize a price to per-litre.

    Returns dict with: price_per_litre, total_volume_ml, total_volume_l.
    """
    total_ml = volume_ml * pack_size
    total_l = total_ml / 1000.0
    price_per_litre = round(price / total_l, 2) if total_l > 0 else 0.0

    return {
        "price_per_litre": price_per_litre,
        "total_volume_ml": total_ml,
        "total_volume_l": round(total_l, 3),
        "price": price,
    }
