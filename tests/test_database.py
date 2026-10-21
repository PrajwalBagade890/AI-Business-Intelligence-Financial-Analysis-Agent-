"""Integration tests for database initialization, synthetic data seeding, and integrity."""

import pytest
from app.database.connection import SessionLocal, init_db
from app.database.models import Customer, Product, Sale, Expense, Budget, FinancialTransaction
from app.database.seed_data import seed_database
from app.database.schema_inspector import get_schema_summary


@pytest.fixture(scope="module")
def seeded_db():
    """Ensure database is seeded for test module."""
    init_db()
    seed_database(force_recreate=False)
    db = SessionLocal()
    yield db
    db.close()


def test_database_record_counts(seeded_db):
    """Verify minimum required volume of synthetic records for analytical tests."""
    cust_count = seeded_db.query(Customer).count()
    prod_count = seeded_db.query(Product).count()
    sales_count = seeded_db.query(Sale).count()
    exp_count = seeded_db.query(Expense).count()
    budget_count = seeded_db.query(Budget).count()

    assert cust_count >= 100, f"Expected at least 100 customers, got {cust_count}"
    assert prod_count >= 5, f"Expected at least 5 products, got {prod_count}"
    assert sales_count >= 500, f"Expected at least 500 sales, got {sales_count}"
    assert exp_count >= 50, f"Expected at least 50 expense items, got {exp_count}"
    assert budget_count >= 20, f"Expected at least 20 budget entries, got {budget_count}"


def test_financial_integrity(seeded_db):
    """Verify sales calculations adhere to gross = qty * price and profit = net - cogs."""
    sample_sales = seeded_db.query(Sale).limit(50).all()
    for s in sample_sales:
        calculated_gross = round(s.unit_price * s.quantity, 2)
        assert abs(s.gross_amount - calculated_gross) < 0.05, f"Gross mismatch on order {s.order_number}"

        if s.payment_status != "Refunded":
            calculated_profit = round(s.net_amount - s.cogs_amount, 2)
            assert abs(s.gross_profit - calculated_profit) < 0.05, f"Profit mismatch on order {s.order_number}"


def test_schema_inspector():
    """Verify schema inspector returns expected tables and columns."""
    schema = get_schema_summary()
    expected_tables = ["customers", "products", "sales", "expenses", "budgets", "financial_transactions"]
    for t in expected_tables:
        assert t in schema, f"Missing table {t} in schema summary"
        assert len(schema[t]["columns"]) > 0
