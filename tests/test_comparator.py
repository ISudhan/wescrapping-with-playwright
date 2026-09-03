"""Tests for price comparison logic."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.product import Product
from services.comparator import compare_single_group, compare_all


def _make_product(name: str, platform: str, price: float = None) -> Product:
    return Product(name=name, platform=platform, price=price)


class TestCompareSingleGroup:
    def test_basic_comparison(self):
        products = [
            _make_product("Tata Salt", "blinkit", 24.0),
            _make_product("Tata Salt", "swiggy", 26.0),
            _make_product("Tata Salt", "zepto", 22.0),
        ]
        result = compare_single_group("tata salt", products)
        assert result.lowest_price == 22.0
        assert result.lowest_platform == "zepto"
        assert result.prices["blinkit"] == 24.0
        assert result.prices["swiggy"] == 26.0
        assert result.prices["zepto"] == 22.0

    def test_missing_price(self):
        products = [
            _make_product("Tata Salt", "blinkit", 24.0),
            _make_product("Tata Salt", "swiggy", None),
        ]
        result = compare_single_group("tata salt", products)
        assert result.lowest_price == 24.0
        assert result.lowest_platform == "blinkit"
        assert result.prices["swiggy"] is None

    def test_all_prices_none(self):
        products = [
            _make_product("Tata Salt", "blinkit", None),
            _make_product("Tata Salt", "swiggy", None),
        ]
        result = compare_single_group("tata salt", products)
        assert result.lowest_price is None
        assert result.lowest_platform is None

    def test_same_platform_keeps_lowest(self):
        products = [
            _make_product("Tata Salt", "blinkit", 30.0),
            _make_product("Tata Salt", "blinkit", 24.0),
        ]
        result = compare_single_group("tata salt", products)
        assert result.prices["blinkit"] == 24.0


class TestCompareAll:
    def test_multiple_groups(self):
        groups = {
            "tata salt": [
                _make_product("Tata Salt", "blinkit", 24.0),
                _make_product("Tata Salt", "swiggy", 26.0),
            ],
            "amul butter": [
                _make_product("Amul Butter", "blinkit", 57.0),
                _make_product("Amul Butter", "zepto", 55.0),
            ],
        }
        results = compare_all(groups)
        assert len(results) == 2

        by_name = {r.product_name: r for r in results}
        assert by_name["tata salt"].lowest_price == 24.0
        assert by_name["amul butter"].lowest_platform == "zepto"
