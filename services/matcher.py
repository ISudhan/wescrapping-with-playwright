"""Match products across platforms using normalized names."""

from collections import defaultdict
from difflib import SequenceMatcher

from models.product import Product


def find_exact_matches(products: list[Product]) -> dict[str, list[Product]]:
    """Group products by exact normalized_name match.

    Args:
        products: List of normalized Product instances from all platforms.

    Returns:
        Dict mapping normalized_name → list of Products with that name.
    """
    groups: dict[str, list[Product]] = defaultdict(list)
    for product in products:
        if product.normalized_name:
            groups[product.normalized_name].append(product)
    return dict(groups)


def find_fuzzy_matches(
    products: list[Product], threshold: float = 0.75
) -> dict[str, list[Product]]:
    """Group products using fuzzy name matching with SequenceMatcher.

    First does exact matching, then merges groups whose canonical names
    are similar above the threshold.

    Args:
        products: List of normalized Product instances from all platforms.
        threshold: Minimum similarity ratio (0.0 to 1.0) to merge groups.

    Returns:
        Dict mapping canonical normalized_name → list of Products.
    """
    # Start with exact matches
    groups = find_exact_matches(products)

    # Try to merge similar groups
    canonical_names = list(groups.keys())
    merged: dict[str, list[Product]] = {}
    used: set[str] = set()

    for i, name_a in enumerate(canonical_names):
        if name_a in used:
            continue

        # Start a new merged group with name_a as canonical
        merged_group = list(groups[name_a])
        used.add(name_a)

        for j in range(i + 1, len(canonical_names)):
            name_b = canonical_names[j]
            if name_b in used:
                continue

            ratio = SequenceMatcher(None, name_a, name_b).ratio()
            if ratio >= threshold:
                merged_group.extend(groups[name_b])
                used.add(name_b)

        merged[name_a] = merged_group

    return merged


def find_cross_platform_matches(
    products: list[Product], fuzzy: bool = False, threshold: float = 0.75
) -> dict[str, list[Product]]:
    """Find products that appear on multiple platforms.

    Args:
        products: List of normalized Product instances from all platforms.
        fuzzy: Whether to use fuzzy matching.
        threshold: Similarity threshold for fuzzy matching.

    Returns:
        Dict with only groups that have products from 2+ platforms.
    """
    if fuzzy:
        groups = find_fuzzy_matches(products, threshold)
    else:
        groups = find_exact_matches(products)

    # Filter to only cross-platform matches
    return {
        name: prods
        for name, prods in groups.items()
        if len({p.platform for p in prods}) > 1
    }
