"""Pydantic models for product data and price comparison."""

import re
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, model_validator


def normalize_name(name: str) -> str:
    """Normalize a product name: lowercase, remove punctuation, collapse whitespace."""
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r"[^\w\s]", "", name)  # remove punctuation
    name = re.sub(r"\s+", " ", name).strip()  # collapse whitespace
    return name


def parse_price(value: Optional[str]) -> Optional[float]:
    """Parse a price string into a float. Handles ₹ symbol, whitespace, None."""
    if value is None:
        return None
    # Remove currency symbols and whitespace
    cleaned = re.sub(r"[₹\u20b9,\s]", "", str(value))
    if not cleaned:
        return None
    try:
        price = float(cleaned)
        return price if price > 0 else None
    except (ValueError, TypeError):
        return None


class Product(BaseModel):
    """Common product schema across all platforms."""

    name: str
    normalized_name: str = ""
    image: Optional[str] = None
    quantity: Optional[str] = None
    mrp: Optional[float] = None
    price: Optional[float] = None
    discount: Optional[str] = None
    platform: str
    product_link: Optional[str] = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def set_normalized_name(self):
        """Auto-compute normalized_name from name if not already set."""
        if not self.normalized_name and self.name:
            self.normalized_name = normalize_name(self.name)
        return self


class PriceComparison(BaseModel):
    """Price comparison result across platforms."""

    product_name: str
    prices: dict[str, Optional[float]]  # {platform: price}
    lowest_price: Optional[float] = None
    lowest_platform: Optional[str] = None
