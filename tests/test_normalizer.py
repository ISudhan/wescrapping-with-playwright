"""Tests for normalization: name normalization and price parsing."""

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.product import normalize_name, parse_price
from services.normalizer import normalize_raw_product


class TestNormalizeName:
    def test_lowercase(self):
        assert normalize_name("Tata Salt") == "tata salt"

    def test_remove_punctuation(self):
        assert normalize_name("Amul - Butter (100g)") == "amul butter 100g"

    def test_punctuation_and_whitespace(self):
        assert normalize_name("hello - world") == "hello world"

    def test_collapse_whitespace(self):
        assert normalize_name("  Tata   Salt  ") == "tata salt"

    def test_empty(self):
        assert normalize_name("") == ""

    def test_special_characters(self):
        assert normalize_name("MTR 3-Minute Poha!") == "mtr 3minute poha"

    def test_unicode_preserved(self):
        # Letters with diacritics are kept (they're \w)
        result = normalize_name("Café Latte")
        assert "caf" in result


class TestParsePrice:
    def test_simple_number(self):
        assert parse_price("250") == 250.0

    def test_with_rupee_symbol(self):
        assert parse_price("₹250") == 250.0
        assert parse_price("\u20b9250") == 250.0

    def test_with_decimal(self):
        assert parse_price("99.50") == 99.50

    def test_none(self):
        assert parse_price(None) is None

    def test_empty_string(self):
        assert parse_price("") is None

    def test_zero(self):
        assert parse_price("0") is None

    def test_with_comma(self):
        assert parse_price("1,250") == 1250.0

    def test_invalid(self):
        assert parse_price("abc") is None


class TestNormalizeRawProduct:
    def test_blinkit_product(self):
        raw = {
            "name": "Tata Salt",
            "image": "https://example.com/salt.jpg",
            "quantity": "1 kg",
            "mrp": "28",
            "price": "24",
            "discount": "14% OFF",
        }
        product = normalize_raw_product(raw, "blinkit")
        assert product is not None
        assert product.name == "Tata Salt"
        assert product.normalized_name == "tata salt"
        assert product.platform == "blinkit"
        assert product.price == 24.0
        assert product.mrp == 28.0

    def test_zepto_product_with_relative_link(self):
        raw = {
            "name": "Amul Butter",
            "image": None,
            "quantity": "100 g",
            "mrp": "60",
            "price": "57",
            "discount": None,
            "product_link": "/pn/amul-butter/pvid/123",
        }
        product = normalize_raw_product(raw, "zepto")
        assert product is not None
        assert product.product_link == "https://www.zeptonow.com/pn/amul-butter/pvid/123"

    def test_missing_name_returns_none(self):
        raw = {"name": None, "price": "100"}
        assert normalize_raw_product(raw, "blinkit") is None

    def test_empty_name_returns_none(self):
        raw = {"name": "  ", "price": "100"}
        assert normalize_raw_product(raw, "blinkit") is None
