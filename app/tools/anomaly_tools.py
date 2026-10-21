"""Statistical and rule-based anomaly detection tools for financial and business data."""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


def detect_expense_spikes(expenses_df: pd.DataFrame, z_threshold: float = 2.0) -> List[Dict[str, Any]]:
    """Detect anomalous expense transactions using Z-score outlier detection."""
    if expenses_df.empty or len(expenses_df) < 4:
        return []

    anomalies = []
    # Check within each category
    for category, group in expenses_df.groupby("category"):
        amounts = group["amount"].values
        mean = np.mean(amounts)
        std = np.std(amounts)

        if std == 0:
            continue

        for _, row in group.iterrows():
            z_score = (row["amount"] - mean) / std
            if abs(z_score) >= z_threshold:
                direction = "Spike" if z_score > 0 else "Drop"
                exp_date = row.get("expense_date") if "expense_date" in row else row.get("month", row.get("date", "N/A"))
                anomalies.append({
                    "date": str(exp_date),
                    "category": category,
                    "department": row.get("department", "Unknown"),
                    "vendor": row.get("vendor", "Unknown"),
                    "amount": round(float(row["amount"]), 2),
                    "mean_for_category": round(float(mean), 2),
                    "deviation_pct": round(float(((row["amount"] - mean) / mean) * 100), 2),
                    "z_score": round(float(z_score), 2),
                    "type": direction,
                    "severity": "HIGH" if abs(z_score) > 3.0 else "MEDIUM",
                })

    return anomalies


def detect_margin_compression(sales_df: pd.DataFrame, margin_threshold: float = 40.0) -> List[Dict[str, Any]]:
    """Detect products or periods where gross margin dropped significantly below target."""
    if sales_df.empty:
        return []

    group_col = "product_name" if "product_name" in sales_df.columns else "product_id"
    grouped = sales_df.groupby(group_col).agg(
        revenue=("net_amount", "sum"),
        profit=("gross_profit", "sum"),
    ).reset_index()

    alerts = []
    for _, row in grouped.iterrows():
        rev = float(row["revenue"])
        prof = float(row["profit"])
        margin = (prof / rev * 100) if rev > 0 else 0.0

        if margin < margin_threshold:
            alerts.append({
                "product": str(row[group_col]),
                "realized_margin_pct": round(margin, 2),
                "threshold_pct": margin_threshold,
                "gap_pct": round(margin_threshold - margin, 2),
                "risk_level": "HIGH" if margin < 25.0 else "MEDIUM",
                "recommendation": "Review supplier COGS, pricing tier, or discount authorizations.",
            })

    return alerts
