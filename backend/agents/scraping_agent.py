"""
ScrapingAgent — Two-mode scraping for competitor prices.

Primary (real scrape): When customer provides a URL, use Playwright to
navigate, extract product name + price + promo text, capture screenshot.
Fallback (CSV lookup): When no URL or scraping fails, look up from
competitor_prices.csv by competitor name + product name match.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from backend.config import get_settings
from backend.data.loader import find_competitor_prices

logger = logging.getLogger(__name__)


async def _real_scrape(url: str, competitor: str) -> dict[str, Any]:
    """
    Use Playwright to scrape a competitor product page.
    Extracts product name, price, promo text, and captures screenshot.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright not installed — cannot real-scrape")
        raise RuntimeError("Playwright not available")

    settings = get_settings()
    screenshots_dir = settings.resolved_data_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow()
    date_str = timestamp.strftime("%Y%m%d_%H%M%S")
    screenshot_filename = f"{competitor}_{date_str}.png"
    screenshot_path = screenshots_dir / screenshot_filename

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)  # Allow JS to render

            # Capture screenshot
            await page.screenshot(path=str(screenshot_path), full_page=False)

            # Try to extract product info from page
            title = await page.title()

            # Generic price extraction — look for dollar amounts
            page_text = await page.inner_text("body")
            price_matches = re.findall(r'\$(\d+\.?\d{0,2})', page_text)
            extracted_price = float(price_matches[0]) if price_matches else None

            # Try to get product name from heading
            product_name = title
            try:
                h1 = await page.query_selector("h1")
                if h1:
                    product_name = await h1.inner_text()
            except Exception:
                pass

            # Check for promo text
            promo = ""
            promo_selectors = [".promo", ".promotion", ".sale-badge", ".special-offer"]
            for sel in promo_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        promo = await el.inner_text()
                        break
                except Exception:
                    continue

            await browser.close()

            return {
                "competitor": competitor,
                "competitor_product_name": product_name.strip(),
                "competitor_price": extracted_price,
                "competitor_url": url,
                "in_stock": True,
                "promotion": promo.strip(),
                "screenshot_path": f"data/screenshots/{screenshot_filename}",
                "scrape_mode": "real",
                "scrape_timestamp": timestamp.isoformat(),
            }

        except Exception as e:
            await browser.close()
            raise RuntimeError(f"Scraping failed: {e}")


async def _csv_fallback(
    competitor: Optional[str],
    product_name: Optional[str],
    competitor_price: Optional[float] = None,
) -> dict[str, Any]:
    """
    Look up competitor price from CSV data.
    """
    results = find_competitor_prices(
        competitor=competitor,
        product_name=product_name,
    )

    if not results:
        # Try broader search if no match
        results = find_competitor_prices(competitor=competitor)

    if results:
        # Pick best match — prefer one closest to stated price if given
        if competitor_price and len(results) > 1:
            results.sort(key=lambda r: abs(r.get("competitor_price", 0) - competitor_price))

        best = results[0]
        return {
            "competitor": best.get("competitor", competitor or "unknown"),
            "competitor_product_name": best.get("competitor_product_name", ""),
            "competitor_price": best.get("competitor_price"),
            "competitor_url": best.get("competitor_url", ""),
            "in_stock": best.get("in_stock", True),
            "promotion": best.get("promotion", ""),
            "screenshot_path": best.get("screenshot_path", ""),
            "scrape_mode": "csv_fallback",
            "scrape_timestamp": best.get("scrape_timestamp", datetime.utcnow().isoformat()),
            "matched_sku": best.get("matched_sku"),
        }
    else:
        return {
            "competitor": competitor or "unknown",
            "competitor_product_name": product_name or "",
            "competitor_price": competitor_price,
            "competitor_url": "",
            "in_stock": False,
            "promotion": "",
            "screenshot_path": "",
            "scrape_mode": "csv_fallback",
            "scrape_timestamp": datetime.utcnow().isoformat(),
            "error": "No matching competitor data found in CSV",
        }


async def run_scraping_agent(
    url: Optional[str] = None,
    competitor: Optional[str] = None,
    product_name: Optional[str] = None,
    competitor_price: Optional[float] = None,
) -> tuple[dict[str, Any], str]:
    """
    Two-mode scraping agent.

    If URL provided: attempt real Playwright scrape, fall back to CSV on failure.
    If no URL: use CSV fallback directly.

    Returns (result_dict, inference_mode).
    """
    scrape_result = None
    fallback_reason = None

    # Mode 1: Real scrape when URL is available
    if url and competitor:
        try:
            scrape_result = await _real_scrape(url, competitor)
            return scrape_result, "real"
        except Exception as e:
            fallback_reason = f"Real scrape failed: {e}"
            logger.warning("[ScrapingAgent] %s — falling back to CSV", fallback_reason)

    # Mode 2: CSV fallback
    csv_result = await _csv_fallback(competitor, product_name, competitor_price)
    if fallback_reason:
        csv_result["fallback_reason"] = fallback_reason

    return csv_result, "fallback" if url else "real"  # CSV lookup for no-URL is "real" behaviour
