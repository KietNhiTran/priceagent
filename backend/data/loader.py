"""
CSV data access layer.

Loads and caches product catalogue, competitor prices, RSA config,
and beat formula config from CSV files.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd

from backend.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def _data_dir() -> Path:
    return get_settings().resolved_data_dir


def load_catalogue() -> pd.DataFrame:
    """Load Dan Murphy's product catalogue."""
    path = _data_dir() / "dan_murphys_catalogue.csv"
    df = pd.read_csv(path)
    logger.info("Loaded catalogue: %d products", len(df))
    return df


def load_competitor_prices() -> pd.DataFrame:
    """Load competitor price data."""
    path = _data_dir() / "competitor_prices.csv"
    df = pd.read_csv(path)
    logger.info("Loaded competitor prices: %d rows", len(df))
    return df


def load_rsa_config() -> pd.DataFrame:
    """Load RSA floor-price configuration."""
    path = _data_dir() / "rsa_config.csv"
    df = pd.read_csv(path)
    logger.info("Loaded RSA config: %d rows", len(df))
    return df


def load_beat_formula_config() -> pd.DataFrame:
    """Load beat formula tier configuration."""
    path = _data_dir() / "beat_formula_config.csv"
    df = pd.read_csv(path)
    logger.info("Loaded beat formula config: %d rows", len(df))
    return df


# ---------------------------------------------------------------------------
# Convenience query functions
# ---------------------------------------------------------------------------

def find_product_by_sku(sku: str) -> Optional[dict]:
    """Look up a product by SKU. Returns dict or None."""
    df = load_catalogue()
    match = df[df["sku"] == sku]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def find_product_by_name(name: str, threshold: float = 0.6) -> Optional[dict]:
    """Simple fuzzy match on product name. Returns best match or None."""
    df = load_catalogue()
    name_lower = name.lower()
    # Simple containment scoring
    scores = df["product_name"].str.lower().apply(
        lambda x: _simple_similarity(name_lower, x)
    )
    best_idx = scores.idxmax()
    if scores[best_idx] >= threshold:
        return df.iloc[best_idx].to_dict()
    return None


def find_competitor_prices(
    competitor: Optional[str] = None,
    sku: Optional[str] = None,
    product_name: Optional[str] = None,
) -> list[dict]:
    """Find competitor prices by competitor name, SKU, or product name."""
    df = load_competitor_prices()

    if competitor:
        df = df[df["competitor"].str.lower() == competitor.lower()]
    if sku:
        df = df[df["matched_sku"] == sku]
    if product_name:
        name_lower = product_name.lower()
        df = df[df["competitor_product_name"].str.lower().str.contains(name_lower, na=False)]

    return df.to_dict("records")


def get_rsa_floor(category: str) -> dict:
    """Get RSA config for a product category."""
    df = load_rsa_config()
    match = df[df["category"].str.lower() == category.lower()]
    if match.empty:
        # Default to beer if category not found
        match = df[df["category"] == "beer"]
    return match.iloc[0].to_dict()


def get_beat_tier(price_diff: float, diff_pct: float) -> dict:
    """Determine the beat formula tier for a given price difference."""
    df = load_beat_formula_config()
    for _, row in df.iterrows():
        if row["beat_amount_min"] <= abs(price_diff) <= row["beat_amount_max"]:
            return row.to_dict()
    # Default to auto_reject for anything outside defined ranges
    return df.iloc[-1].to_dict()


def _simple_similarity(a: str, b: str) -> float:
    """Simple similarity based on word overlap."""
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)
