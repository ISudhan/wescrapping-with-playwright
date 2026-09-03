"""MongoDB connection and CRUD helpers."""

import os
from typing import Optional

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

from models.product import PriceComparison, Product

load_dotenv()

# Module-level client (lazy singleton)
_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def get_database() -> Database:
    """Get the MongoDB database instance. Creates connection on first call."""
    global _client, _db

    if _db is not None:
        return _db

    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DATABASE", "grocery_price_comparison")

    _client = MongoClient(uri)
    _db = _client[db_name]
    return _db


# ─── Products CRUD ────────────────────────────────────────────────


def save_products(products: list[Product]) -> int:
    """Upsert products into the 'products' collection.

    Uses (normalized_name, platform) as the compound key for upserts.

    Returns:
        Number of products upserted.
    """
    db = get_database()
    collection = db["products"]
    count = 0

    for product in products:
        doc = product.model_dump()
        # Convert datetime for MongoDB
        doc["scraped_at"] = product.scraped_at

        collection.update_one(
            {"normalized_name": product.normalized_name, "platform": product.platform},
            {"$set": doc},
            upsert=True,
        )
        count += 1

    return count


def get_all_products(platform: Optional[str] = None) -> list[dict]:
    """Get all products, optionally filtered by platform."""
    db = get_database()
    query = {}
    if platform:
        query["platform"] = platform.lower()

    cursor = db["products"].find(query, {"_id": 0})
    return list(cursor)


def get_products_by_name(name: str) -> list[dict]:
    """Search products by name (case-insensitive substring match)."""
    db = get_database()
    cursor = db["products"].find(
        {"name": {"$regex": name, "$options": "i"}},
        {"_id": 0},
    )
    return list(cursor)


# ─── Price Comparisons CRUD ───────────────────────────────────────


def save_comparisons(comparisons: list[PriceComparison]) -> int:
    """Save price comparisons to the 'price_comparisons' collection.

    Returns:
        Number of comparisons saved.
    """
    db = get_database()
    collection = db["price_comparisons"]
    count = 0

    for comparison in comparisons:
        doc = comparison.model_dump()
        collection.update_one(
            {"product_name": comparison.product_name},
            {"$set": doc},
            upsert=True,
        )
        count += 1

    return count


def get_comparison(product_name: str) -> Optional[dict]:
    """Get a stored price comparison by product name (case-insensitive)."""
    db = get_database()
    result = db["price_comparisons"].find_one(
        {"product_name": {"$regex": product_name, "$options": "i"}},
        {"_id": 0},
    )
    return result


def get_all_comparisons() -> list[dict]:
    """Get all stored price comparisons."""
    db = get_database()
    cursor = db["price_comparisons"].find({}, {"_id": 0})
    return list(cursor)
