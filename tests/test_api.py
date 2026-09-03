"""Tests for FastAPI endpoints."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestHealthCheck:
    def test_health_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_health_response_body(self):
        response = client.get("/")
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data


class TestProductsEndpoint:
    def test_products_returns_200(self):
        response = client.get("/products")
        assert response.status_code == 200

    def test_products_has_count(self):
        response = client.get("/products")
        data = response.json()
        assert "count" in data
        assert "products" in data
        assert isinstance(data["products"], list)


class TestDocsEndpoint:
    def test_docs_accessible(self):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "/" in data["paths"]
        assert "/products" in data["paths"]
        assert "/compare/{product_name}" in data["paths"]
        assert "/scrape" in data["paths"]
