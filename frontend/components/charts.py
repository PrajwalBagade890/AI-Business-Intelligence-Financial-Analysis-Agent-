"""Interactive Plotly financial visualizations for Streamlit dashboard."""

from typing import List, Dict, Any
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def plot_revenue_trajectory(monthly_data: List[Dict[str, Any]]) -> go.Figure:
    """Create dual-axis interactive chart: Monthly Revenue (Bar) and Gross Profit (Line)."""
    df = pd.DataFrame(monthly_data)
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No Monthly Data Available")
        return fig

    fig = go.Figure()

    # Revenue Bars
    fig.add_trace(go.Bar(
        x=df["month"],
        y=df["monthly_revenue"],
        name="Net Revenue ($)",
        marker_color="#2563EB",
        opacity=0.85,
    ))

    # Gross Profit Line
    if "monthly_gross_profit" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["month"],
            y=df["monthly_gross_profit"],
            name="Gross Profit ($)",
            mode="lines+markers",
            line=dict(color="#10B981", width=3),
            marker=dict(size=7),
        ))

    fig.update_layout(
        title="<b>Monthly Revenue & Gross Profit Trajectory</b>",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def plot_product_profitability(products_data: List[Dict[str, Any]]) -> go.Figure:
    """Horizontal bar chart ranking products by Gross Profit and Revenue."""
    df = pd.DataFrame(products_data)
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No Product Data Available")
        return fig

    prod_col = "product_name" if "product_name" in df.columns else "product"
    df = df.sort_values(by="gross_profit", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df[prod_col],
        x=df["gross_profit"],
        orientation="h",
        name="Gross Profit ($)",
        marker=dict(
            color=df["gross_margin_pct"],
            colorscale="Viridis",
            colorbar=dict(title="Margin %"),
            showscale=True,
        ),
        text=[f"${v:,.0f} ({m}%)" for v, m in zip(df["gross_profit"], df["gross_margin_pct"])],
        textposition="auto",
    ))

    fig.update_layout(
        title="<b>Product Gross Profit Ranking (Colored by Margin %)</b>",
        xaxis_title="Gross Profit ($)",
        yaxis_title="",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def plot_expense_breakdown(expense_data: Dict[str, Any]) -> go.Figure:
    """Donut chart showing operational expense distribution across categories."""
    categories = expense_data.get("category_breakdown", [])
    df = pd.DataFrame(categories)
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No Expense Data Available")
        return fig

    fig = px.pie(
        df,
        values="amount",
        names="category",
        title="<b>Operating Expense (OPEX) Distribution</b>",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig
