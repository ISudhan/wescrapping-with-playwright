"""Normalize raw scraper output into the common Product schema."""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from models.product import Product, normalize_name, parse_price


# Platform URL prefixes for building full product links
PLATFORM_BASE_URLS = {
    "zepto": "https://www.zeptonow.com",
}


def normalize_raw_product(raw: dict, platform: str) -> Optional[Product]:
    """Convert a single raw scraper dict into a Product.

    Args:
        raw: Raw product dict from scraper output JSON.
        platform: One of 'blinkit', 'swiggy', 'zepto'.

    Returns:
        Product instance, or None if the raw data is unusable (no name).
    """
    name = raw.get("name")
    if not name or not name.strip():
        return None

    # Build full product link for platforms with relative URLs
    product_link = raw.get("product_link")
    if product_link and not product_link.startswith("http"):
        base = PLATFORM_BASE_URLS.get(platform, "")
        product_link = f"{base}{product_link}" if base else product_link

    return Product(
        name=name.strip(),
        normalized_name=normalize_name(name),
        image=raw.get("image"),
        quantity=raw.get("quantity"),
        mrp=parse_price(raw.get("mrp")),
        price=parse_price(raw.get("price")),
        discount=raw.get("discount"),
        platform=platform,
        product_link=product_link,
        scraped_at=datetime.now(timezone.utc),
    )


def load_and_normalize(platform: str) -> list[Product]:
    """Load a platform's output JSON and normalize all products.

    Args:
        platform: One of 'blinkit', 'swiggy', 'zepto'.

    Returns:
        List of normalized Product instances.
    """
    filename = f"output_{platform}.json"

    if not os.path.exists(filename):
        print(f"Warning: {filename} not found, skipping {platform}")
        return []

    with open(filename, "r") as f:
        raw_products = json.load(f)

    products = []
    for raw in raw_products:
        product = normalize_raw_product(raw, platform)
        if product:
            products.append(product)

    print(f"Normalized {len(products)} products from {platform}")
    return products


def load_all_platforms() -> list[Product]:
    """Load and normalize products from all platforms."""
    all_products = []
    for platform in ["blinkit", "swiggy", "zepto"]:
        all_products.extend(load_and_normalize(platform))
    return all_products
