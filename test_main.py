"""
Test Suite for Production-Ready API
Includes unit tests and integration tests.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio

from main import app, ItemService, ItemCreate, db_pool


# ============================================================================
# Test Client Setup
# ============================================================================

@pytest.fixture
def client():
    """Synchronous test client"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client():
    """Async test client for integration tests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def reset_state():
    """Reset application state between tests"""
    ItemService._items = {}
    ItemService._id_counter = 0
    yield


# ============================================================================
# Unit Tests - Health Endpoints
# ============================================================================

class TestHealthEndpoints:
    """Tests for health check endpoints"""

    def test_health_check(self, client):
        """Test main health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "checks" in data

    def test_liveness_probe(self, client):
        """Test Kubernetes liveness probe"""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_readiness_probe(self, client):
        """Test Kubernetes readiness probe"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


# ============================================================================
# Unit Tests - Item CRUD
# ============================================================================

class TestItemCRUD:
    """Tests for item CRUD operations"""

    def test_create_item(self, client):
        """Test item creation"""
        response = client.post(
            "/api/v1/items",
            json={"name": "Test Item", "description": "A test", "price": 29.99}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Item"
        assert data["price"] == 29.99
        assert "id" in data
        assert "created_at" in data

    def test_create_item_validation_error(self, client):
        """Test item creation with invalid data"""
        # Missing required field
        response = client.post("/api/v1/items", json={"description": "No name"})
        assert response.status_code == 422

        # Invalid price
        response = client.post(
            "/api/v1/items",
            json={"name": "Test", "price": -10}
        )
        assert response.status_code == 422

    def test_get_item(self, client):
        """Test getting an item by ID"""
        # Create item first
        create_response = client.post(
            "/api/v1/items",
            json={"name": "Test", "price": 10.00}
        )
        item_id = create_response.json()["id"]

        # Get item
        response = client.get(f"/api/v1/items/{item_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test"

    def test_get_item_not_found(self, client):
        """Test getting non-existent item"""
        response = client.get("/api/v1/items/99999")
        assert response.status_code == 404

    def test_delete_item(self, client):
        """Test deleting an item"""
        # Create item first
        create_response = client.post(
            "/api/v1/items",
            json={"name": "Test", "price": 10.00}
        )
        item_id = create_response.json()["id"]

        # Delete item
        response = client.delete(f"/api/v1/items/{item_id}")
        assert response.status_code == 204

        # Verify deleted
        response = client.get(f"/api/v1/items/{item_id}")
        assert response.status_code == 404

    def test_delete_item_not_found(self, client):
        """Test deleting non-existent item"""
        response = client.delete("/api/v1/items/99999")
        assert response.status_code == 404


# ============================================================================
# Unit Tests - Pagination
# ============================================================================

class TestPagination:
    """Tests for pagination functionality"""

    def test_list_items_empty(self, client):
        """Test listing items when empty"""
        response = client.get("/api/v1/items")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["has_more"] is False

    def test_list_items_pagination(self, client):
        """Test pagination works correctly"""
        # Create 25 items
        for i in range(25):
            client.post(
                "/api/v1/items",
                json={"name": f"Item {i}", "price": 10.00}
            )

        # First page
        response = client.get("/api/v1/items?page=1&page_size=10")
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["has_more"] is True
        assert data["page"] == 1

        # Second page
        response = client.get("/api/v1/items?page=2&page_size=10")
        data = response.json()
        assert len(data["items"]) == 10
        assert data["has_more"] is True

        # Third page
        response = client.get("/api/v1/items?page=3&page_size=10")
        data = response.json()
        assert len(data["items"]) == 5
        assert data["has_more"] is False

    def test_pagination_limits(self, client):
        """Test pagination limits are enforced"""
        # Page size too large
        response = client.get("/api/v1/items?page_size=200")
        assert response.status_code == 422

        # Invalid page number
        response = client.get("/api/v1/items?page=0")
        assert response.status_code == 422


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows"""

    def test_full_item_lifecycle(self, client):
        """Test complete item lifecycle: create, read, update, delete"""
        # Create
        create_response = client.post(
            "/api/v1/items",
            json={"name": "Lifecycle Test", "price": 99.99}
        )
        assert create_response.status_code == 201
        item_id = create_response.json()["id"]

        # Read
        read_response = client.get(f"/api/v1/items/{item_id}")
        assert read_response.status_code == 200
        assert read_response.json()["name"] == "Lifecycle Test"

        # List (verify in list)
        list_response = client.get("/api/v1/items")
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1

        # Delete
        delete_response = client.delete(f"/api/v1/items/{item_id}")
        assert delete_response.status_code == 204

        # Verify deleted
        verify_response = client.get(f"/api/v1/items/{item_id}")
        assert verify_response.status_code == 404

    def test_rate_limiting_headers(self, client):
        """Test rate limiting headers are present"""
        response = client.get("/health")
        assert "X-RateLimit-Remaining" in response.headers

    def test_response_time_header(self, client):
        """Test response time header is present"""
        response = client.get("/health")
        assert "X-Response-Time" in response.headers


# ============================================================================
# Unit Tests - Service Layer
# ============================================================================

class TestItemService:
    """Unit tests for ItemService"""

    @pytest.mark.asyncio
    async def test_create_item_service(self):
        """Test ItemService.create_item"""
        item = ItemCreate(name="Service Test", price=50.00)
        result = await ItemService.create_item(item)
        assert result.name == "Service Test"
        assert result.price == 50.00
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_list_items_service_pagination(self):
        """Test ItemService pagination logic"""
        # Create items
        for i in range(15):
            await ItemService.create_item(
                ItemCreate(name=f"Item {i}", price=10.00)
            )

        # Test pagination
        result = await ItemService.list_items(page=1, page_size=10)
        assert len(result.items) == 10
        assert result.total == 15
        assert result.has_more is True

        result = await ItemService.list_items(page=2, page_size=10)
        assert len(result.items) == 5
        assert result.has_more is False


# ============================================================================
# Metrics Tests
# ============================================================================

class TestMetrics:
    """Tests for metrics endpoint"""

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint returns data"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "requests_total" in data
        assert "items_total" in data
        assert "db_pool_status" in data
