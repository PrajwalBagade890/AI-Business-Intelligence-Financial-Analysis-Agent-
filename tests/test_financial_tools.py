"""Unit tests for deterministic financial calculation tools."""

import pytest
import pandas as pd
import numpy as np
from app.tools.financial_tools import (
    safe_divide,
    calculate_revenue_summary,
    calculate_profitability,
    calculate_growth_rate,
    calculate_expense_breakdown,
    calculate_product_profitability_ranking,
)


def test_safe_divide():
    """Verify division by zero and null handling."""
    assert safe_divide(100, 2) == 50.0
    assert safe_divide(100, 0) == 0.0
    assert safe_divide(100, None) == 0.0
    assert safe_divide(None, 10) == 0.0
    assert safe_divide(100, 0, default=999.0) == 999.0


def test_calculate_revenue_summary():
    """Verify revenue metrics aggregation and discounts."""
    data = {
        "id": [1, 2, 3],
        "gross_amount": [1000.0, 2000.0, 500.0],
        "net_amount": [900.0, 1800.0, 500.0],
        "cogs_amount": [300.0, 600.0, 150.0],
        "quantity": [2, 4, 1],
        "payment_status": ["Completed", "Completed", "Refunded"],
    }
    df = pd.DataFrame(data)
    summary = calculate_revenue_summary(df)

    # Excludes refunded order (id 3)
    assert summary["gross_revenue"] == 3000.0
    assert summary["net_revenue"] == 2700.0
    assert summary["total_discounts"] == 300.0
    assert summary["total_cogs"] == 900.0
    assert summary["gross_profit"] == 1800.0
    assert summary["gross_margin_pct"] == 66.67
    assert summary["transaction_count"] == 2
    assert summary["total_units_sold"] == 6
    assert summary["average_order_value"] == 1350.0


def test_calculate_revenue_summary_empty():
    """Verify empty dataframe handling."""
    empty_df = pd.DataFrame()
    summary = calculate_revenue_summary(empty_df)
    assert summary["net_revenue"] == 0.0
    assert summary["transaction_count"] == 0
    assert summary["gross_margin_pct"] == 0.0


def test_calculate_profitability():
    """Verify income statement profitability and margin metrics."""
    res = calculate_profitability(net_revenue=100000.0, cogs=30000.0, operating_expenses=40000.0)
    assert res["gross_profit"] == 70000.0
    assert res["gross_margin_pct"] == 70.0
    assert res["operating_profit_ebitda"] == 30000.0
    assert res["operating_margin_pct"] == 30.0
    assert res["is_profitable"] is True


def test_calculate_profitability_loss():
    """Verify operating loss detection."""
    res = calculate_profitability(net_revenue=50000.0, cogs=35000.0, operating_expenses=25000.0)
    assert res["gross_profit"] == 15000.0
    assert res["operating_profit_ebitda"] == -10000.0
    assert res["is_profitable"] is False


def test_calculate_growth_rate():
    """Verify period-over-period growth calculation."""
    # Positive growth
    g1 = calculate_growth_rate(current_val=150.0, prior_val=100.0)
    assert g1["absolute_change"] == 50.0
    assert g1["percentage_change"] == 50.0
    assert g1["trend_direction"] == "upward"

    # Decline
    g2 = calculate_growth_rate(current_val=80.0, prior_val=100.0)
    assert g2["absolute_change"] == -20.0
    assert g2["percentage_change"] == -20.0
    assert g2["trend_direction"] == "downward"

    # Prior is zero
    g3 = calculate_growth_rate(current_val=50.0, prior_val=0.0)
    assert g3["percentage_change"] == 100.0


def test_calculate_expense_breakdown_with_budgets():
    """Verify OPEX aggregation and budget variance."""
    expenses_df = pd.DataFrame({
        "category": ["R&D", "R&D", "Marketing"],
        "amount": [20000.0, 25000.0, 30000.0],
    })
    budgets_df = pd.DataFrame({
        "category": ["R&D", "Marketing"],
        "budgeted_amount": [40000.0, 35000.0],
    })

    res = calculate_expense_breakdown(expenses_df, budgets_df)
    assert res["total_expenses"] == 75000.0

    variances = {v["category"]: v for v in res["budget_variances"]}
    # R&D spent 45k vs 40k budget -> Over Budget
    assert variances["R&D"]["actual_spend"] == 45000.0
    assert variances["R&D"]["variance_amount"] == 5000.0
    assert variances["R&D"]["status"] == "Over Budget"

    # Marketing spent 30k vs 35k budget -> Under Budget
    assert variances["Marketing"]["actual_spend"] == 30000.0
    assert variances["Marketing"]["variance_amount"] == -5000.0
    assert variances["Marketing"]["status"] == "Under Budget"


def test_product_profitability_ranking():
    """Verify ranking products by gross profit."""
    sales_df = pd.DataFrame({
        "product_name": ["Product A", "Product B", "Product A"],
        "net_amount": [1000.0, 5000.0, 2000.0],
        "cogs_amount": [200.0, 3500.0, 400.0],
        "gross_profit": [800.0, 1500.0, 1600.0],
        "quantity": [1, 2, 2],
    })
    ranked = calculate_product_profitability_ranking(sales_df)
    assert len(ranked) == 2
    # Product A total profit = 2400, Product B = 1500
    assert ranked[0]["product"] == "Product A"
    assert ranked[0]["gross_profit"] == 2400.0
    assert ranked[1]["product"] == "Product B"
    assert ranked[1]["gross_profit"] == 1500.0
