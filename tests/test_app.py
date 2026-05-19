# ============================================================
# Tests — Checking your chef's work before the inspector arrives
# ============================================================
# pytest is a testing tool. Run with: pytest tests/ -v
# Each function starting with "test_" is one test.
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from app import app


# Create a test version of the app — no real server needed
@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_route(client):
    """Home page should return 200 and service name"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["service"] == "Trinayops"
    assert "version" in data
    print("  ✅ Home route works")


def test_health_route(client):
    """Health check should return 200 and memory/cpu stats"""
    response = client.get("/health")
    # Accept 200 (healthy) or 503 (degraded) — both are valid responses
    assert response.status_code in [200, 503]
    data = response.get_json()
    assert "status" in data
    assert "memory_used_pct" in data
    print(f"  ✅ Health route works — status: {data['status']}")


def test_info_route(client):
    """Info route should return deployment metadata"""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.get_json()
    assert "version" in data
    assert "environment" in data
    print("  ✅ Info route works")


def test_simulate_failure_memory(client):
    """Simulate memory failure should return 200"""
    response = client.get("/simulate-failure?type=memory")
    assert response.status_code == 200
    data = response.get_json()
    assert data["simulated"] == "memory_spike"
    print("  ✅ Failure simulation works")


def test_simulate_failure_unknown(client):
    """Unknown failure type should return 400"""
    response = client.get("/simulate-failure?type=unknown")
    assert response.status_code == 400
    print("  ✅ Unknown failure type correctly rejected")

