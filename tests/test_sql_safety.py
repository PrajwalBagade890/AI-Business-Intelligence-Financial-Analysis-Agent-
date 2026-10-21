"""Unit tests for SQL query safety, token validation, and injection prevention."""

import pytest
from app.tools.sql_tool import SafeSQLExecutor, SQLValidationError


@pytest.fixture
def executor():
    return SafeSQLExecutor(max_rows=100, timeout_seconds=2.0)


def test_valid_select_queries(executor):
    """Verify safe SELECT and CTE queries are accepted and formatted with limits."""
    q1 = "SELECT id, net_amount FROM sales WHERE net_amount > 100"
    v1 = executor.validate_sql(q1)
    assert "LIMIT 100" in v1
    assert v1.startswith("SELECT")

    q2 = "WITH regional_rev AS (SELECT region, SUM(net_amount) as total FROM sales GROUP BY region) SELECT * FROM regional_rev"
    v2 = executor.validate_sql(q2)
    assert "LIMIT 100" in v2
    assert v2.startswith("WITH")


def test_reject_mutations_and_ddl(executor):
    """Verify that DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE are blocked."""
    prohibited_queries = [
        "DROP TABLE sales;",
        "DELETE FROM customers WHERE id = 1;",
        "INSERT INTO products (product_name) VALUES ('Hacked');",
        "UPDATE expenses SET amount = 0;",
        "ALTER TABLE sales DROP COLUMN net_amount;",
        "TRUNCATE TABLE financial_transactions;",
        "CREATE TABLE backdoors (id int);",
        "EXEC xp_cmdshell('dir');",
    ]

    for q in prohibited_queries:
        with pytest.raises(SQLValidationError):
            executor.validate_sql(q)


def test_reject_multiple_statements_injection(executor):
    """Verify semicolon statement chaining is strictly prohibited."""
    injections = [
        "SELECT * FROM sales; DROP TABLE sales;",
        "SELECT 1; DELETE FROM customers",
        "SELECT * FROM products; TRUNCATE TABLE expenses;",
    ]

    for inj in injections:
        with pytest.raises(SQLValidationError) as excinfo:
            executor.validate_sql(inj)
        assert "Multiple SQL statements" in str(excinfo.value) or "Prohibited" in str(excinfo.value)


def test_limit_enforcement(executor):
    """Verify user cannot bypass row limits with oversized LIMIT clauses."""
    q = "SELECT * FROM sales LIMIT 50000"
    validated = executor.validate_sql(q)
    assert "LIMIT 100" in validated
    assert "50000" not in validated


def test_reject_empty_query(executor):
    """Verify empty or blank queries are rejected."""
    with pytest.raises(SQLValidationError):
        executor.validate_sql("")

    with pytest.raises(SQLValidationError):
        executor.validate_sql("   ")
