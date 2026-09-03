"""Price comparison across matched product groups."""

from models.product import PriceComparison, Product


def compare_single_group(product_name: str, products: list[Product]) -> PriceComparison:
    """Compare prices for a group of matched products.

    Args:
        product_name: Canonical product name for this group.
        products: List of Products (same product from different platforms).

    Returns:
        PriceComparison with prices per platform and the lowest.
    """
    prices: dict[str, float | None] = {}

    for product in products:
        # If multiple products from same platform, keep the lowest price
        if product.price is not None:
            existing = prices.get(product.platform)
            if existing is None or product.price < existing:
                prices[product.platform] = product.price
        elif product.platform not in prices:
            prices[product.platform] = None

    # Find lowest price, excluding None
    valid_prices = {p: v for p, v in prices.items() if v is not None}

    lowest_price = None
    lowest_platform = None
    if valid_prices:
        lowest_platform = min(valid_prices, key=valid_prices.get)
        lowest_price = valid_prices[lowest_platform]

    return PriceComparison(
        product_name=product_name,
        prices=prices,
        lowest_price=lowest_price,
        lowest_platform=lowest_platform,
    )


def compare_all(
    product_groups: dict[str, list[Product]],
) -> list[PriceComparison]:
    """Compare prices for all product groups.

    Args:
        product_groups: Dict mapping product name → list of Products.

    Returns:
        List of PriceComparison results.
    """
    comparisons = []
    for name, products in product_groups.items():
        comparison = compare_single_group(name, products)
        comparisons.append(comparison)
    return comparisons
