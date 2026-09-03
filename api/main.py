"""FastAPI application for the Grocery Price Comparison System."""

import subprocess
import sys
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from db.mongodb import (
    get_all_products,
    get_comparison,
    get_products_by_name,
    save_comparisons,
    save_products,
)
from models.product import PriceComparison
from services.comparator import compare_single_group
from services.matcher import find_exact_matches, find_fuzzy_matches
from services.normalizer import load_all_platforms

app = FastAPI(
    title="Grocery Price Comparison API",
    description="Compare grocery prices across Blinkit, Swiggy Instamart, and Zepto",
    version="1.0.0",
)


# ─── Response Models ──────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    message: str


class ScrapeResponse(BaseModel):
    status: str
    message: str


class ProductListResponse(BaseModel):
    count: int
    products: list[dict]


# ─── Background Task ─────────────────────────────────────────────


def run_scrape_pipeline():
    """Background task: run scrapers, normalize, save to MongoDB."""
    platforms = ["blinkit", "swiggy", "zepto"]

    # Run each scraper as a subprocess (same approach as scheduler.py)
    for platform in platforms:
        script = f"{platform}.py"
        print(f"Running {script}...")
        try:
            subprocess.run(
                [sys.executable, script],
                timeout=300,  # 5 min timeout per scraper
                check=False,
            )
        except subprocess.TimeoutExpired:
            print(f"Timeout: {script} took too long, skipping")
        except Exception as e:
            print(f"Error running {script}: {e}")

    # Load and normalize all scraped data
    print("Normalizing scraped data...")
    products = load_all_platforms()

    if products:
        # Save to MongoDB
        count = save_products(products)
        print(f"Saved {count} products to MongoDB")

        # Generate and save comparisons
        groups = find_exact_matches(products)
        from services.comparator import compare_all

        comparisons = compare_all(groups)
        comp_count = save_comparisons(comparisons)
        print(f"Saved {comp_count} comparisons to MongoDB")
    else:
        print("No products to save")


# ─── Endpoints ────────────────────────────────────────────────────


@app.get("/", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", message="Grocery Price Comparison API is running")


@app.get("/products", response_model=ProductListResponse)
def list_products(platform: Optional[str] = None):
    """List all products, optionally filtered by platform.

    Query params:
        platform: Filter by platform (blinkit, swiggy, zepto)
    """
    products = get_all_products(platform)
    return ProductListResponse(count=len(products), products=products)


@app.get("/products/{product_name}")
def search_products(product_name: str):
    """Search products by name (case-insensitive substring match)."""
    products = get_products_by_name(product_name)
    if not products:
        raise HTTPException(status_code=404, detail=f"No products found matching '{product_name}'")
    return {"count": len(products), "products": products}


@app.get("/compare/{product_name}", response_model=PriceComparison)
def compare_product(product_name: str):
    """Compare prices for a product across platforms.

    First checks for a stored comparison, then computes live from DB data.
    """
    # Try stored comparison first
    stored = get_comparison(product_name)
    if stored:
        return PriceComparison(**stored)

    # Compute from current DB data
    products_raw = get_products_by_name(product_name)
    if not products_raw:
        raise HTTPException(
            status_code=404,
            detail=f"No products found matching '{product_name}'. Run /scrape first.",
        )

    # Convert back to Product objects for the comparator
    from models.product import Product

    products = []
    for p in products_raw:
        try:
            products.append(Product(**p))
        except Exception:
            continue

    if not products:
        raise HTTPException(status_code=404, detail="Could not parse product data")

    # Use the search term as the canonical name
    comparison = compare_single_group(product_name, products)

    # Save for future lookups
    save_comparisons([comparison])

    return comparison


@app.post("/scrape", response_model=ScrapeResponse)
def trigger_scrape(background_tasks: BackgroundTasks):
    """Trigger the scraping pipeline in the background.

    Runs all platform scrapers, normalizes data, and saves to MongoDB.
    Returns immediately — scraping happens asynchronously.
    """
    background_tasks.add_task(run_scrape_pipeline)
    return ScrapeResponse(
        status="started",
        message="Scraping pipeline started in background. Check /products after a few minutes.",
    )
