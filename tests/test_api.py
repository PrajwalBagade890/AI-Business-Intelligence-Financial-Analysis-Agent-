"""Integration tests for FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import init_db
from app.database.seed_data import seed_database


@pytest.fixture(scope="module")
def client():
    init_db()
    seed_database(force_recreate=False)
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    """Verify /api/health returns healthy status and DB table counts."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database_connected"] is True
    assert "sales" in data["table_counts"]
    assert data["table_counts"]["sales"] > 0


def test_schema_endpoint(client):
    """Verify /api/data/schema returns table structures."""
    response = client.get("/api/data/schema")
    assert response.status_code == 200
    data = response.json()
    assert "sales" in data
    assert "customers" in data
    assert "products" in data


def test_safe_sql_endpoint_success(client):
    """Verify valid safe query execution via API."""
    payload = {
        "sql": "SELECT id, product_name, unit_price FROM products LIMIT 5"
    }
    response = client.post("/api/data/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["row_count"] > 0
    assert "product_name" in data["columns"]


def test_safe_sql_endpoint_blocks_mutation(client):
    """Verify mutation attempts are blocked by API."""
    payload = {
        "sql": "DROP TABLE sales"
    }
    response = client.post("/api/data/query", json=payload)
    assert response.status_code == 400
    assert "Security Validation Failed" in response.json()["detail"]


def test_query_agent_endpoint(client):
    """Verify natural language query endpoint invoking LangGraph."""
    payload = {
        "query": "How has monthly revenue changed?"
    }
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "final_response" in data
    assert len(data["execution_steps"]) == 6
    assert data["validation_passed"] is True


def test_direct_calculation_endpoint(client):
    """Verify direct mathematical calculation endpoint."""
    payload = {
        "metric_type": "profitability",
        "parameters": {
            "revenue": 500000.0,
            "cogs": 150000.0,
            "operating_expenses": 200000.0
        }
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["gross_profit"] == 350000.0
    assert data["gross_margin_pct"] == 70.0
    assert data["operating_profit_ebitda"] == 150000.0
    assert data["operating_margin_pct"] == 30.0


def test_report_generation_endpoint(client):
    """Verify multi-agent report generation endpoint."""
    payload = {
        "year": 2025
    }
    response = client.post("/api/reports/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "report" in data
    assert "executive_summary" in data["report"]
    assert "key_metrics" in data
    assert len(data["product_ranking"]) > 0
