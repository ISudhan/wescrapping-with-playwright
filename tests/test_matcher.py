"""Tests for product matching logic."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.product import Product
from services.matcher import find_exact_matches, find_fuzzy_matches, find_cross_platform_matches


def _make_product(name: str, platform: str, price: float = 100.0) -> Product:
    """Helper to create a Product for testing."""
    return Product(name=name, platform=platform, price=price)


class TestExactMatch:
    def test_same_name_grouped(self):
        products = [
            _make_product("Tata Salt", "blinkit"),
            _make_product("Tata Salt", "swiggy"),
        ]
        groups = find_exact_matches(products)
        assert "tata salt" in groups
        assert len(groups["tata salt"]) == 2

    def test_different_names_separate(self):
        products = [
            _make_product("Tata Salt", "blinkit"),
            _make_product("Amul Butter", "swiggy"),
        ]
        groups = find_exact_matches(products)
        assert len(groups) == 2

    def test_case_insensitive(self):
        products = [
            _make_product("tata salt", "blinkit"),
            _make_product("TATA SALT", "swiggy"),
        ]
        groups = find_exact_matches(products)
        assert "tata salt" in groups
        assert len(groups["tata salt"]) == 2


class TestFuzzyMatch:
    def test_similar_names_merged(self):
        products = [
            _make_product("Tata Salt", "blinkit"),
            _make_product("Tata Salts", "swiggy"),
        ]
        groups = find_fuzzy_matches(products, threshold=0.8)
        # Should be merged into one group
        assert len(groups) == 1

    def test_dissimilar_names_separate(self):
        products = [
            _make_product("Tata Salt", "blinkit"),
            _make_product("Amul Butter", "swiggy"),
        ]
        groups = find_fuzzy_matches(products, threshold=0.8)
        assert len(groups) == 2


class TestCrossPlatformMatches:
    def test_cross_platform_only(self):
        products = [
            _make_product("Tata Salt", "blinkit"),
            _make_product("Tata Salt", "swiggy"),
            _make_product("Unique Blinkit Item", "blinkit"),
        ]
        matches = find_cross_platform_matches(products)
        # Only "tata salt" appears on 2+ platforms
        assert "tata salt" in matches
        assert "unique blinkit item" not in matches
