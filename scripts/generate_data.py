"""
Generate MVP demo data for the LLPG Reactive Price Beat Agent.

Creates:
  - data/dan_murphys_catalogue.csv  (50 products)
  - data/competitor_prices.csv      (~100 rows)
  - data/rsa_config.csv             (floor prices per category)
  - data/beat_formula_config.csv    (auto/review/reject thresholds)
  - data/screenshots/               (placeholder directory)
"""

import csv
import os
import random
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SCREENSHOTS_DIR = os.path.join(DATA_DIR, "screenshots")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
COMPETITORS = ["liquorland", "liquorland_warehouse", "boozebud"]
COMPETITOR_DOMAINS = {
    "liquorland": "https://www.liquorland.com.au/",
    "liquorland_warehouse": "https://www.liquorland.com.au/warehouse/",
    "boozebud": "https://www.boozebud.com/",
}

DAN_MURPHYS_BASE_URL = "https://www.danmurphys.com.au/product/"
DAN_MURPHYS_IMG_BASE = "https://media.danmurphys.com.au/dmo/product/"

random.seed(42)  # reproducible


def _std_drinks(volume_ml: int, pack_size: int, abv: float) -> float:
    """Calculate standard drinks. 1 std drink = 10g pure ethanol ≈ 12.67mL."""
    total_ml = volume_ml * pack_size
    pure_alcohol_ml = total_ml * (abv / 100.0)
    return round(pure_alcohol_ml / 12.67, 1)


def _rsa_floor(cost_price: float) -> float:
    """RSA floor = cost + 5% margin."""
    return round(cost_price * 1.05, 2)


# ---------------------------------------------------------------------------
# Product Definitions (50 products)
# ---------------------------------------------------------------------------
PRODUCTS = [
    # ── BEERS (15) ──────────────────────────────────────────────────────────
    {"sku": "DM-001001", "barcode": "9300650001011", "product_name": "Victoria Bitter 24 x 375mL Bottles", "brand": "Victoria Bitter", "category": "beer", "subcategory": "Lager", "volume_ml": 375, "pack_size": 24, "alcohol_pct": 4.9, "current_price": 52.00, "cost_price": 38.00, "region": "Victoria", "country": "Australia"},
    {"sku": "DM-001002", "barcode": "9300650001028", "product_name": "Carlton Draught 24 x 375mL Bottles", "brand": "Carlton Draught", "category": "beer", "subcategory": "Lager", "volume_ml": 375, "pack_size": 24, "alcohol_pct": 4.6, "current_price": 51.00, "cost_price": 37.50, "region": "Victoria", "country": "Australia"},
    {"sku": "DM-001003", "barcode": "9300650001035", "product_name": "James Boag's Premium Lager 6 x 375mL Bottles", "brand": "James Boag's", "category": "beer", "subcategory": "Premium Lager", "volume_ml": 375, "pack_size": 6, "alcohol_pct": 5.0, "current_price": 18.00, "cost_price": 13.00, "region": "Tasmania", "country": "Australia"},
    {"sku": "DM-001004", "barcode": "9300650001042", "product_name": "Coopers Pale Ale 6 x 375mL Bottles", "brand": "Coopers", "category": "beer", "subcategory": "Pale Ale", "volume_ml": 375, "pack_size": 6, "alcohol_pct": 4.5, "current_price": 17.50, "cost_price": 12.80, "region": "South Australia", "country": "Australia"},
    {"sku": "DM-001005", "barcode": "9300650001059", "product_name": "Great Northern Original 24 x 330mL Bottles", "brand": "Great Northern", "category": "beer", "subcategory": "Lager", "volume_ml": 330, "pack_size": 24, "alcohol_pct": 4.2, "current_price": 49.00, "cost_price": 36.00, "region": "Queensland", "country": "Australia"},
    {"sku": "DM-001006", "barcode": "9300650001066", "product_name": "XXXX Gold 24 x 375mL Cans", "brand": "XXXX", "category": "beer", "subcategory": "Mid-Strength Lager", "volume_ml": 375, "pack_size": 24, "alcohol_pct": 3.5, "current_price": 46.00, "cost_price": 33.50, "region": "Queensland", "country": "Australia"},
    {"sku": "DM-001007", "barcode": "9300650001073", "product_name": "Tooheys New 24 x 375mL Bottles", "brand": "Tooheys", "category": "beer", "subcategory": "Lager", "volume_ml": 375, "pack_size": 24, "alcohol_pct": 4.6, "current_price": 50.00, "cost_price": 36.50, "region": "New South Wales", "country": "Australia"},
    {"sku": "DM-001008", "barcode": "9300650001080", "product_name": "Crown Lager 6 x 375mL Bottles", "brand": "Crown Lager", "category": "beer", "subcategory": "Premium Lager", "volume_ml": 375, "pack_size": 6, "alcohol_pct": 4.9, "current_price": 19.00, "cost_price": 14.00, "region": "Victoria", "country": "Australia"},
    {"sku": "DM-001009", "barcode": "9300650001097", "product_name": "Hahn SuperDry 24 x 330mL Bottles", "brand": "Hahn", "category": "beer", "subcategory": "Low Carb Lager", "volume_ml": 330, "pack_size": 24, "alcohol_pct": 4.6, "current_price": 48.00, "cost_price": 35.00, "region": "New South Wales", "country": "Australia"},
    {"sku": "DM-001010", "barcode": "9300650001104", "product_name": "Heineken 24 x 330mL Bottles", "brand": "Heineken", "category": "beer", "subcategory": "Import Lager", "volume_ml": 330, "pack_size": 24, "alcohol_pct": 5.0, "current_price": 55.00, "cost_price": 40.00, "region": "", "country": "Netherlands"},
    {"sku": "DM-001011", "barcode": "9300650001111", "product_name": "Corona Extra 24 x 355mL Bottles", "brand": "Corona", "category": "beer", "subcategory": "Import Lager", "volume_ml": 355, "pack_size": 24, "alcohol_pct": 4.5, "current_price": 56.00, "cost_price": 41.00, "region": "", "country": "Mexico"},
    {"sku": "DM-001012", "barcode": "9300650001128", "product_name": "Peroni Nastro Azzurro 6 x 330mL Bottles", "brand": "Peroni", "category": "beer", "subcategory": "Import Lager", "volume_ml": 330, "pack_size": 6, "alcohol_pct": 5.1, "current_price": 16.00, "cost_price": 11.50, "region": "", "country": "Italy"},
    {"sku": "DM-001013", "barcode": "9300650001135", "product_name": "Balter XPA 6 x 375mL Cans", "brand": "Balter", "category": "beer", "subcategory": "XPA", "volume_ml": 375, "pack_size": 6, "alcohol_pct": 5.0, "current_price": 22.00, "cost_price": 16.00, "region": "Queensland", "country": "Australia"},
    {"sku": "DM-001014", "barcode": "9300650001142", "product_name": "Stone & Wood Pacific Ale 6 x 330mL Cans", "brand": "Stone & Wood", "category": "beer", "subcategory": "Pacific Ale", "volume_ml": 330, "pack_size": 6, "alcohol_pct": 4.4, "current_price": 21.00, "cost_price": 15.50, "region": "New South Wales", "country": "Australia"},
    {"sku": "DM-001015", "barcode": "9300650001159", "product_name": "Young Henrys Newtowner 6 x 375mL Cans", "brand": "Young Henrys", "category": "beer", "subcategory": "Pale Ale", "volume_ml": 375, "pack_size": 6, "alcohol_pct": 4.8, "current_price": 20.00, "cost_price": 14.50, "region": "New South Wales", "country": "Australia"},

    # ── WINES (15) ──────────────────────────────────────────────────────────
    {"sku": "DM-002001", "barcode": "9310004002011", "product_name": "Penfolds Bin 389 Cabernet Shiraz 750mL", "brand": "Penfolds", "category": "wine", "subcategory": "Cabernet Shiraz", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 14.5, "current_price": 45.00, "cost_price": 32.00, "region": "South Australia", "country": "Australia"},
    {"sku": "DM-002002", "barcode": "9310004002028", "product_name": "Yellow Tail Shiraz 750mL", "brand": "Yellow Tail", "category": "wine", "subcategory": "Shiraz", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 13.5, "current_price": 9.00, "cost_price": 5.50, "region": "New South Wales", "country": "Australia"},
    {"sku": "DM-002003", "barcode": "9310004002035", "product_name": "Jacob's Creek Classic Chardonnay 750mL", "brand": "Jacob's Creek", "category": "wine", "subcategory": "Chardonnay", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 12.5, "current_price": 10.00, "cost_price": 6.00, "region": "South Australia", "country": "Australia"},
    {"sku": "DM-002004", "barcode": "9310004002042", "product_name": "Oyster Bay Sauvignon Blanc 750mL", "brand": "Oyster Bay", "category": "wine", "subcategory": "Sauvignon Blanc", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 13.0, "current_price": 14.00, "cost_price": 9.50, "region": "Marlborough", "country": "New Zealand"},
    {"sku": "DM-002005", "barcode": "9310004002059", "product_name": "Penfolds Koonunga Hill Shiraz Cabernet 750mL", "brand": "Penfolds", "category": "wine", "subcategory": "Shiraz Cabernet", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 14.0, "current_price": 13.00, "cost_price": 8.50, "region": "South Australia", "country": "Australia"},
    {"sku": "DM-002006", "barcode": "9310004002066", "product_name": "19 Crimes Red Blend 750mL", "brand": "19 Crimes", "category": "wine", "subcategory": "Red Blend", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 13.5, "current_price": 12.00, "cost_price": 7.50, "region": "South Australia", "country": "Australia"},
    {"sku": "DM-002007", "barcode": "9310004002073", "product_name": "De Bortoli Sacred Hill Cabernet Merlot 750mL", "brand": "De Bortoli", "category": "wine", "subcategory": "Cabernet Merlot", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 13.0, "current_price": 8.00, "cost_price": 4.80, "region": "New South Wales", "country": "Australia"},
    {"sku": "DM-002008", "barcode": "9310004002080", "product_name": "Wolf Blass Yellow Label Cabernet Sauvignon 750mL", "brand": "Wolf Blass", "category": "wine", "subcategory": "Cabernet Sauvignon", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 14.0, "current_price": 12.50, "cost_price": 8.00, "region": "South Australia", "country": "Australia"},
    {"sku": "DM-002009", "barcode": "9310004002097", "product_name": "Kim Crawford Sauvignon Blanc 750mL", "brand": "Kim Crawford", "category": "wine", "subcategory": "Sauvignon Blanc", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 13.0, "current_price": 16.00, "cost_price": 11.00, "region": "Marlborough", "country": "New Zealand"},
    {"sku": "DM-002010", "barcode": "9310004002104", "product_name": "Lindeman's Bin 65 Chardonnay 750mL", "brand": "Lindeman's", "category": "wine", "subcategory": "Chardonnay", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 12.5, "current_price": 8.50, "cost_price": 5.00, "region": "South Eastern Australia", "country": "Australia"},
    {"sku": "DM-002011", "barcode": "9310004002111", "product_name": "Hardys Stamp Shiraz 750mL", "brand": "Hardys", "category": "wine", "subcategory": "Shiraz", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 13.5, "current_price": 8.00, "cost_price": 4.50, "region": "South Eastern Australia", "country": "Australia"},
    {"sku": "DM-002012", "barcode": "9310004002128", "product_name": "Treasury Estate T'Gallant Prosecco 750mL", "brand": "T'Gallant", "category": "wine", "subcategory": "Prosecco", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 11.0, "current_price": 15.00, "cost_price": 10.00, "region": "Victoria", "country": "Australia"},
    {"sku": "DM-002013", "barcode": "9310004002135", "product_name": "Brown Brothers Moscato 750mL", "brand": "Brown Brothers", "category": "wine", "subcategory": "Moscato", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 5.5, "current_price": 10.00, "cost_price": 6.50, "region": "Victoria", "country": "Australia"},
    {"sku": "DM-002014", "barcode": "9310004002142", "product_name": "Grant Burge Barossa Ink Shiraz 750mL", "brand": "Grant Burge", "category": "wine", "subcategory": "Shiraz", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 14.5, "current_price": 18.00, "cost_price": 12.00, "region": "Barossa Valley", "country": "Australia"},
    {"sku": "DM-002015", "barcode": "9310004002159", "product_name": "Moët & Chandon Impérial Brut 750mL", "brand": "Moët & Chandon", "category": "wine", "subcategory": "Champagne", "volume_ml": 750, "pack_size": 1, "alcohol_pct": 12.0, "current_price": 62.00, "cost_price": 45.00, "region": "Champagne", "country": "France"},

    # ── SPIRITS (10) ────────────────────────────────────────────────────────
    {"sku": "DM-003001", "barcode": "9320003003011", "product_name": "Johnnie Walker Red Label 700mL", "brand": "Johnnie Walker", "category": "spirits", "subcategory": "Scotch Whisky", "volume_ml": 700, "pack_size": 1, "alcohol_pct": 40.0, "current_price": 40.00, "cost_price": 28.00, "region": "Scotland", "country": "United Kingdom"},
    {"sku": "DM-003002", "barcode": "9320003003028", "product_name": "Smirnoff Red Vodka 700mL", "brand": "Smirnoff", "category": "spirits", "subcategory": "Vodka", "volume_ml": 700, "pack_size": 1, "alcohol_pct": 37.5, "current_price": 36.00, "cost_price": 25.00, "region": "", "country": "Australia"},
    {"sku": "DM-003003", "barcode": "9320003003035", "product_name": "Tanqueray London Dry Gin 700mL", "brand": "Tanqueray", "category": "spirits", "subcategory": "Gin", "volume_ml": 700, "pack_size": 1, "alcohol_pct": 43.1, "current_price": 46.00, "cost_price": 33.00, "region": "", "country": "United Kingdom"},
    {"sku": "DM-003004", "barcode": "9320003003042", "product_name": "Bundaberg Rum UP 700mL", "brand": "Bundaberg", "category": "spirits", "subcategory": "Rum", "volume_ml": 700, "pack_size": 1, "alcohol_pct": 37.0, "current_price": 42.00, "cost_price": 30.00, "region": "Queensland", "country": "Australia"},
    {"sku": "DM-003005", "barcode": "9320003003059", "product_name": "Jack Daniel's Old No.7 700mL", "brand": "Jack Daniel's", "category": "spirits", "subcategory": "Tennessee Whiskey", "volume_ml": 700, "pack_size": 1, "alcohol_pct": 40.0, "current_price": 48.00, "cost_price": 34.00, "region": "Tennessee", "country": "United States"},
    {"sku": "DM-003006", "barcode": "9320003003066", "product_name": "Captain Morgan Spiced Gold 700mL", "brand": "Captain Morgan", "category": "spirits", "subcategory": "Spiced Rum", "volume_ml": 700, "pack_size": 1, "alcohol_pct": 35.0, "current_price": 38.00, "cost_price": 26.50, "region": "", "country": "Jamaica"},
    {"sku": "DM-003007", "barcode": "9320003003073", "product_name": "Absolut Vodka 700mL", "brand": "Absolut", "category": "spirits", "subcategory": "Vodka", "volume_ml": 700, "pack_size": 1, "alcohol_pct": 40.0, "current_price": 42.00, "cost_price": 30.00, "region": "", "country": "Sweden"},
    {"sku": "DM-003008", "barcode": "9320003003080", "product_name": "Hendrick's Gin 700mL", "brand": "Hendrick's", "category": "spirits", "subcategory": "Gin", "volume_ml": 700, "pack_size": 1, "alcohol_pct": 41.4, "current_price": 65.00, "cost_price": 47.00, "region": "Scotland", "country": "United Kingdom"},
    {"sku": "DM-003009", "barcode": "9320003003097", "product_name": "Jameson Irish Whiskey 700mL", "brand": "Jameson", "category": "spirits", "subcategory": "Irish Whiskey", "volume_ml": 700, "pack_size": 1, "alcohol_pct": 40.0, "current_price": 44.00, "cost_price": 31.00, "region": "", "country": "Ireland"},
    {"sku": "DM-003010", "barcode": "9320003003104", "product_name": "Canadian Club 1858 Whisky 700mL", "brand": "Canadian Club", "category": "spirits", "subcategory": "Canadian Whisky", "volume_ml": 700, "pack_size": 1, "alcohol_pct": 40.0, "current_price": 38.00, "cost_price": 27.00, "region": "", "country": "Canada"},

    # ── RTDs (5) ────────────────────────────────────────────────────────────
    {"sku": "DM-004001", "barcode": "9330004004011", "product_name": "Canadian Club & Dry 10 x 375mL Cans", "brand": "Canadian Club", "category": "rtd", "subcategory": "Whisky & Dry", "volume_ml": 375, "pack_size": 10, "alcohol_pct": 4.8, "current_price": 39.00, "cost_price": 28.00, "region": "", "country": "Australia"},
    {"sku": "DM-004002", "barcode": "9330004004028", "product_name": "Jim Beam & Cola 10 x 375mL Cans", "brand": "Jim Beam", "category": "rtd", "subcategory": "Bourbon & Cola", "volume_ml": 375, "pack_size": 10, "alcohol_pct": 4.8, "current_price": 38.00, "cost_price": 27.50, "region": "", "country": "Australia"},
    {"sku": "DM-004003", "barcode": "9330004004035", "product_name": "Smirnoff Ice Double Black 10 x 375mL Cans", "brand": "Smirnoff", "category": "rtd", "subcategory": "Vodka RTD", "volume_ml": 375, "pack_size": 10, "alcohol_pct": 6.5, "current_price": 42.00, "cost_price": 30.00, "region": "", "country": "Australia"},
    {"sku": "DM-004004", "barcode": "9330004004042", "product_name": "Cruiser Vodka Mixed 10 x 275mL Bottles", "brand": "Vodka Cruiser", "category": "rtd", "subcategory": "Vodka RTD", "volume_ml": 275, "pack_size": 10, "alcohol_pct": 4.6, "current_price": 32.00, "cost_price": 23.00, "region": "", "country": "Australia"},
    {"sku": "DM-004005", "barcode": "9330004004059", "product_name": "Jack Daniel's & Cola 10 x 375mL Cans", "brand": "Jack Daniel's", "category": "rtd", "subcategory": "Whiskey & Cola", "volume_ml": 375, "pack_size": 10, "alcohol_pct": 4.8, "current_price": 44.00, "cost_price": 32.00, "region": "", "country": "Australia"},

    # ── CIDER & NON-ALC (5) ────────────────────────────────────────────────
    {"sku": "DM-005001", "barcode": "9340005005011", "product_name": "Somersby Apple Cider 10 x 375mL Cans", "brand": "Somersby", "category": "cider", "subcategory": "Apple Cider", "volume_ml": 375, "pack_size": 10, "alcohol_pct": 4.5, "current_price": 28.00, "cost_price": 20.00, "region": "", "country": "Australia"},
    {"sku": "DM-005002", "barcode": "9340005005028", "product_name": "Bulmers Original Cider 10 x 330mL Bottles", "brand": "Bulmers", "category": "cider", "subcategory": "Apple Cider", "volume_ml": 330, "pack_size": 10, "alcohol_pct": 4.5, "current_price": 30.00, "cost_price": 21.50, "region": "", "country": "Ireland"},
    {"sku": "DM-005003", "barcode": "9340005005035", "product_name": "Strongbow Original Cider 10 x 375mL Cans", "brand": "Strongbow", "category": "cider", "subcategory": "Dry Cider", "volume_ml": 375, "pack_size": 10, "alcohol_pct": 5.0, "current_price": 29.00, "cost_price": 20.50, "region": "", "country": "Australia"},
    {"sku": "DM-005004", "barcode": "9340005005042", "product_name": "Heaps Normal Quiet XPA 4 x 375mL Cans", "brand": "Heaps Normal", "category": "non_alc", "subcategory": "Non-Alc XPA", "volume_ml": 375, "pack_size": 4, "alcohol_pct": 0.5, "current_price": 16.00, "cost_price": 11.00, "region": "New South Wales", "country": "Australia"},
    {"sku": "DM-005005", "barcode": "9340005005059", "product_name": "Athletic Brewing Run Wild IPA 6 x 355mL Cans", "brand": "Athletic Brewing", "category": "non_alc", "subcategory": "Non-Alc IPA", "volume_ml": 355, "pack_size": 6, "alcohol_pct": 0.5, "current_price": 20.00, "cost_price": 14.00, "region": "", "country": "United States"},
]


# ---------------------------------------------------------------------------
# Generate product catalogue CSV
# ---------------------------------------------------------------------------
def generate_catalogue():
    headers = [
        "sku", "barcode", "product_name", "brand", "category", "subcategory",
        "volume_ml", "pack_size", "alcohol_pct", "standard_drinks",
        "current_price", "cost_price", "rsa_floor_price", "region", "country",
        "active", "product_url", "image_url", "thumbnail_url",
    ]
    rows = []
    for p in PRODUCTS:
        std = _std_drinks(p["volume_ml"], p["pack_size"], p["alcohol_pct"])
        floor = _rsa_floor(p["cost_price"])
        slug = p["product_name"].lower().replace(" ", "-").replace("'", "").replace("&", "and")[:60]
        rows.append({
            "sku": p["sku"],
            "barcode": p["barcode"],
            "product_name": p["product_name"],
            "brand": p["brand"],
            "category": p["category"],
            "subcategory": p["subcategory"],
            "volume_ml": p["volume_ml"],
            "pack_size": p["pack_size"],
            "alcohol_pct": p["alcohol_pct"],
            "standard_drinks": std,
            "current_price": p["current_price"],
            "cost_price": p["cost_price"],
            "rsa_floor_price": floor,
            "region": p["region"],
            "country": p["country"],
            "active": True,
            "product_url": f"{DAN_MURPHYS_BASE_URL}{slug}-{p['sku'].lower()}",
            "image_url": f"{DAN_MURPHYS_IMG_BASE}{p['sku']}-1.png",
            "thumbnail_url": f"{DAN_MURPHYS_IMG_BASE}{p['sku']}-thumb.png",
        })

    path = os.path.join(DATA_DIR, "dan_murphys_catalogue.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓ Catalogue: {len(rows)} products → {path}")
    return rows


# ---------------------------------------------------------------------------
# Generate competitor prices CSV (~100 rows)
# ---------------------------------------------------------------------------
def generate_competitor_prices(catalogue_rows):
    headers = [
        "competitor", "competitor_url", "competitor_product_name",
        "competitor_price", "competitor_barcode", "matched_sku",
        "match_confidence", "scrape_timestamp", "price_per_litre",
        "in_stock", "promotion", "screenshot_path", "screenshot_url",
        "competitor_image_url",
    ]

    rows = []
    base_time = datetime(2026, 2, 18, 8, 0, 0)

    for cat_row in catalogue_rows:
        # Each product gets ~2 competitor entries (some get 1 or 3 for variety)
        num_competitors = random.choice([1, 2, 2, 2, 3])
        selected = random.sample(COMPETITORS, min(num_competitors, len(COMPETITORS)))

        for comp in selected:
            # Price variance:
            #   ~30% cheaper (LLPG trigger)
            #   ~50% same or within $0.50
            #   ~20% more expensive
            roll = random.random()
            own_price = cat_row["current_price"]
            if roll < 0.30:
                # Cheaper — LLPG trigger
                discount = random.uniform(0.50, min(own_price * 0.15, 8.00))
                comp_price = round(own_price - discount, 2)
            elif roll < 0.80:
                # Same or within $0.50
                comp_price = round(own_price + random.uniform(-0.50, 0.50), 2)
            else:
                # More expensive
                comp_price = round(own_price + random.uniform(0.50, 5.00), 2)

            comp_price = max(comp_price, 1.00)  # sanity

            # Competitor product name (slight variations)
            comp_name = cat_row["product_name"]
            if comp == "boozebud":
                comp_name = comp_name.replace("mL", "ml")  # style difference

            slug = comp_name.lower().replace(" ", "-")[:40]
            comp_url = f"{COMPETITOR_DOMAINS[comp]}{slug}"

            volume_l = (cat_row["volume_ml"] * cat_row["pack_size"]) / 1000.0
            ppl = round(comp_price / volume_l, 2) if volume_l > 0 else 0

            ts = base_time + timedelta(minutes=random.randint(0, 600))
            date_str = ts.strftime("%Y%m%d")

            screenshot_filename = f"{comp}_{cat_row['sku']}_{date_str}.png"

            in_stock = random.random() > 0.05  # 95% in stock
            promo = ""
            if random.random() < 0.15:
                promos = [
                    "Members Price", "2 for $30", "10% off sitewide",
                    "Bundle Deal", "Happy Hour Special",
                ]
                promo = random.choice(promos)

            rows.append({
                "competitor": comp,
                "competitor_url": comp_url,
                "competitor_product_name": comp_name,
                "competitor_price": comp_price,
                "competitor_barcode": cat_row["barcode"],
                "matched_sku": cat_row["sku"],
                "match_confidence": round(random.uniform(0.85, 1.0), 2),
                "scrape_timestamp": ts.isoformat(),
                "price_per_litre": ppl,
                "in_stock": in_stock,
                "promotion": promo,
                "screenshot_path": f"data/screenshots/{screenshot_filename}",
                "screenshot_url": f"https://storage.blob.core.windows.net/screenshots/{screenshot_filename}",
                "competitor_image_url": f"{COMPETITOR_DOMAINS[comp]}images/{cat_row['sku'].lower()}.png",
            })

    # Shuffle for realism
    random.shuffle(rows)

    path = os.path.join(DATA_DIR, "competitor_prices.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓ Competitor prices: {len(rows)} rows → {path}")
    return rows


# ---------------------------------------------------------------------------
# Generate RSA config CSV
# ---------------------------------------------------------------------------
def generate_rsa_config():
    headers = ["category", "floor_per_std_drink", "min_margin_pct", "state", "notes"]
    rows = [
        {"category": "beer", "floor_per_std_drink": 1.50, "min_margin_pct": 5.0, "state": "ALL", "notes": "Above NT min ($1.30). Covers excise + GST + margin"},
        {"category": "wine", "floor_per_std_drink": 1.20, "min_margin_pct": 5.0, "state": "ALL", "notes": "WET applies differently; lower excise"},
        {"category": "spirits", "floor_per_std_drink": 1.80, "min_margin_pct": 5.0, "state": "ALL", "notes": "Highest excise rate (~$100.16/LAL)"},
        {"category": "rtd", "floor_per_std_drink": 1.60, "min_margin_pct": 5.0, "state": "ALL", "notes": "Mid-range excise, popular category"},
        {"category": "cider", "floor_per_std_drink": 1.40, "min_margin_pct": 5.0, "state": "ALL", "notes": "Similar to beer excise"},
        {"category": "non_alc", "floor_per_std_drink": 0.00, "min_margin_pct": 5.0, "state": "ALL", "notes": "No excise; margin-only floor"},
    ]
    path = os.path.join(DATA_DIR, "rsa_config.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓ RSA config: {len(rows)} rows → {path}")


# ---------------------------------------------------------------------------
# Generate beat formula config CSV
# ---------------------------------------------------------------------------
def generate_beat_formula_config():
    headers = [
        "tier", "beat_amount_min", "beat_amount_max", "price_diff_pct_min",
        "price_diff_pct_max", "action", "description",
    ]
    rows = [
        {"tier": "auto_approve", "beat_amount_min": 0.01, "beat_amount_max": 5.00, "price_diff_pct_min": 0.0, "price_diff_pct_max": 15.0, "action": "AUTO_APPROVE", "description": "Small price difference — auto-approve"},
        {"tier": "human_review", "beat_amount_min": 5.01, "beat_amount_max": 20.00, "price_diff_pct_min": 15.0, "price_diff_pct_max": 30.0, "action": "SEND_TO_REVIEW", "description": "Medium difference — route to CHUB for review"},
        {"tier": "auto_reject", "beat_amount_min": 20.01, "beat_amount_max": 9999.99, "price_diff_pct_min": 30.0, "price_diff_pct_max": 100.0, "action": "AUTO_REJECT", "description": "Large difference or below RSA floor — auto-reject"},
    ]
    path = os.path.join(DATA_DIR, "beat_formula_config.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓ Beat formula config: {len(rows)} rows → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("LLPG MVP Data Generator")
    print("=" * 60)

    catalogue = generate_catalogue()
    generate_competitor_prices(catalogue)
    generate_rsa_config()
    generate_beat_formula_config()

    print("=" * 60)
    print(f"All files generated in: {DATA_DIR}")
    print(f"Screenshots dir: {SCREENSHOTS_DIR}")
    print("=" * 60)
