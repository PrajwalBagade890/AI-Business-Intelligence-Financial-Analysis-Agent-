"""Deterministic financial calculation tools.

All financial formulas are executed in deterministic Python code to guarantee
mathematical accuracy and eliminate LLM calculation hallucination.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, avoiding ZeroDivisionError or NaN."""
    if denominator is None or denominator == 0 or np.isnan(denominator):
        return default
    if numerator is None or np.isnan(numerator):
        return default
    return float(numerator / denominator)


def calculate_revenue_summary(sales_data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate deterministic revenue metrics from sales transactions.

    Returns:
    - gross_revenue: float
    - total_discounts: float
    - net_revenue: float
    - total_cogs: float
    - gross_profit: float
    - gross_margin_pct: float
    - transaction_count: int
    - total_units_sold: int
    - average_order_value: float
    """
    if sales_data.empty:
        return {
            "gross_revenue": 0.0,
            "total_discounts": 0.0,
            "net_revenue": 0.0,
            "total_cogs": 0.0,
            "gross_profit": 0.0,
            "gross_margin_pct": 0.0,
            "transaction_count": 0,
            "total_units_sold": 0,
            "average_order_value": 0.0,
            "_data_type": "calculated_metric",
        }

    # Filter out refunded orders for revenue realization
    active_sales = sales_data[sales_data["payment_status"] != "Refunded"] if "payment_status" in sales_data.columns else sales_data

    gross_rev = float(active_sales["gross_amount"].sum()) if "gross_amount" in active_sales.columns else float(active_sales["net_amount"].sum())
    net_rev = float(active_sales["net_amount"].sum())
    cogs = float(active_sales["cogs_amount"].sum()) if "cogs_amount" in active_sales.columns else 0.0
    discounts = float(round(gross_rev - net_rev, 2))
    gross_profit = float(round(net_rev - cogs, 2))
    gross_margin_pct = float(round(safe_divide(gross_profit, net_rev) * 100, 2))
    tx_count = int(len(active_sales))
    units_sold = int(active_sales["quantity"].sum()) if "quantity" in active_sales.columns else tx_count
    aov = float(round(safe_divide(net_rev, tx_count), 2))

    return {
        "gross_revenue": round(gross_rev, 2),
        "total_discounts": discounts,
        "net_revenue": round(net_rev, 2),
        "total_cogs": round(cogs, 2),
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_margin_pct,
        "transaction_count": tx_count,
        "total_units_sold": units_sold,
        "average_order_value": aov,
        "_data_type": "calculated_metric",
    }


def calculate_profitability(net_revenue: float, cogs: float, operating_expenses: float) -> Dict[str, Any]:
    """Calculate full income statement margins and operating profit (EBITDA approximation)."""
    gross_profit = float(round(net_revenue - cogs, 2))
    gross_margin_pct = float(round(safe_divide(gross_profit, net_revenue) * 100, 2))
    operating_profit = float(round(gross_profit - operating_expenses, 2))
    operating_margin_pct = float(round(safe_divide(operating_profit, net_revenue) * 100, 2))

    return {
        "net_revenue": round(net_revenue, 2),
        "cogs": round(cogs, 2),
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_margin_pct,
        "operating_expenses": round(operating_expenses, 2),
        "operating_profit_ebitda": operating_profit,
        "operating_margin_pct": operating_margin_pct,
        "is_profitable": operating_profit > 0,
        "_data_type": "calculated_metric",
    }


def calculate_growth_rate(current_val: float, prior_val: float) -> Dict[str, Any]:
    """Calculate period-over-period absolute and percentage growth rates."""
    abs_change = float(round(current_val - prior_val, 2))

    if prior_val == 0:
        pct_change = 100.0 if current_val > 0 else (0.0 if current_val == 0 else -100.0)
    else:
        pct_change = float(round(((current_val - prior_val) / abs(prior_val)) * 100, 2))

    trend_direction = "upward" if pct_change > 0 else ("downward" if pct_change < 0 else "flat")

    return {
        "current_period": round(current_val, 2),
        "prior_period": round(prior_val, 2),
        "absolute_change": abs_change,
        "percentage_change": pct_change,
        "trend_direction": trend_direction,
        "_data_type": "calculated_metric",
    }


def calculate_period_comparison(
    current_df: pd.DataFrame,
    prior_df: pd.DataFrame,
    value_col: str = "net_amount",
    group_col: Optional[str] = None,
) -> Dict[str, Any]:
    """Compare performance across two distinct periods, optionally grouped by dimension (e.g., category, region)."""
    curr_total = float(current_df[value_col].sum()) if not current_df.empty else 0.0
    prior_total = float(prior_df[value_col].sum()) if not prior_df.empty else 0.0
    overall_growth = calculate_growth_rate(curr_total, prior_total)

    breakdown = []
    if group_col and not current_df.empty and group_col in current_df.columns:
        curr_grouped = current_df.groupby(group_col)[value_col].sum()
        prior_grouped = prior_df.groupby(group_col)[value_col].sum() if not prior_df.empty and group_col in prior_df.columns else pd.Series(dtype=float)

        all_keys = set(curr_grouped.index).union(set(prior_grouped.index))
        for key in sorted(all_keys):
            c_val = float(curr_grouped.get(key, 0.0))
            p_val = float(prior_grouped.get(key, 0.0))
            g_rate = calculate_growth_rate(c_val, p_val)
            breakdown.append({
                "group": str(key),
                "current_amount": round(c_val, 2),
                "prior_amount": round(p_val, 2),
                "growth_pct": g_rate["percentage_change"],
                "absolute_change": g_rate["absolute_change"],
            })

    return {
        "metric_name": value_col,
        "overall": overall_growth,
        "breakdown": breakdown,
        "_data_type": "calculated_metric",
    }


def calculate_expense_breakdown(
    expenses_df: pd.DataFrame,
    budgets_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Calculate expense distribution and variance against approved budgets."""
    if expenses_df.empty:
        return {
            "total_expenses": 0.0,
            "category_breakdown": [],
            "budget_variances": [],
            "_data_type": "calculated_metric",
        }

    total_spend = float(expenses_df["amount"].sum())
    grouped_cat = expenses_df.groupby("category")["amount"].sum().reset_index()

    categories = []
    for _, row in grouped_cat.iterrows():
        cat_amt = float(row["amount"])
        pct_of_total = float(round(safe_divide(cat_amt, total_spend) * 100, 2))
        categories.append({
            "category": str(row["category"]),
            "amount": round(cat_amt, 2),
            "pct_of_total": pct_of_total,
        })

    variances = []
    if budgets_df is not None and not budgets_df.empty:
        grouped_budget = budgets_df.groupby("category")["budgeted_amount"].sum().reset_index()
        merged = pd.merge(grouped_cat, grouped_budget, on="category", how="outer").fillna(0.0)

        for _, row in merged.iterrows():
            actual = float(row["amount"])
            budget = float(row["budgeted_amount"])
            diff = float(round(actual - budget, 2))
            pct_diff = float(round(safe_divide(diff, budget) * 100, 2))

            status = "Over Budget" if diff > 0 else ("Under Budget" if diff < 0 else "On Target")
            variances.append({
                "category": str(row["category"]),
                "actual_spend": round(actual, 2),
                "budget_allocated": round(budget, 2),
                "variance_amount": diff,
                "variance_pct": pct_diff,
                "status": status,
            })

    return {
        "total_expenses": round(total_spend, 2),
        "category_breakdown": categories,
        "budget_variances": variances,
        "_data_type": "calculated_metric",
    }


def calculate_product_profitability_ranking(sales_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Rank products by gross revenue, gross profit, and gross profit margin."""
    if sales_df.empty:
        return []

    # Requires product_name or product_id
    group_col = "product_name" if "product_name" in sales_df.columns else "product_id"

    grouped = sales_df.groupby(group_col).agg(
        total_revenue=("net_amount", "sum"),
        total_cogs=("cogs_amount", "sum"),
        total_profit=("gross_profit", "sum"),
        units_sold=("quantity", "sum"),
        order_count=("id", "count") if "id" in sales_df.columns else ("net_amount", "count"),
    ).reset_index()

    ranked = []
    for _, row in grouped.iterrows():
        rev = float(row["total_revenue"])
        profit = float(row["total_profit"])
        cogs = float(row["total_cogs"])
        margin_pct = float(round(safe_divide(profit, rev) * 100, 2))

        ranked.append({
            "product": str(row[group_col]),
            "total_revenue": round(rev, 2),
            "total_cogs": round(cogs, 2),
            "gross_profit": round(profit, 2),
            "gross_margin_pct": margin_pct,
            "units_sold": int(row["units_sold"]),
            "order_count": int(row["order_count"]),
        })

    # Sort descending by gross profit
    ranked.sort(key=lambda x: x["gross_profit"], reverse=True)
    return ranked
