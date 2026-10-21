"""Streamlit KPI cards component for executive metrics."""

import streamlit as st
from typing import Dict, Any


def render_kpi_cards(metrics: Dict[str, Any]):
    """Render executive KPI cards in a responsive columns layout."""
    col1, col2, col3, col4, col5 = st.columns(5)

    net_rev = metrics.get("net_revenue", 0.0)
    gross_prof = metrics.get("gross_profit", 0.0)
    margin_pct = metrics.get("gross_margin_pct", 0.0)
    ebitda = metrics.get("operating_profit_ebitda", 0.0)
    yoy = metrics.get("yoy_revenue_growth_pct", 0.0)
    aov = metrics.get("average_order_value", 0.0)

    with col1:
        st.metric(
            label="Net Revenue",
            value=f"${net_rev:,.0f}" if net_rev else "$0",
            delta=f"{yoy:+.1f}% YoY" if yoy else None,
        )

    with col2:
        st.metric(
            label="Gross Profit",
            value=f"${gross_prof:,.0f}" if gross_prof else "$0",
            delta=f"{margin_pct:.1f}% Margin" if margin_pct else None,
        )

    with col3:
        st.metric(
            label="Operating EBITDA",
            value=f"${ebitda:,.0f}" if ebitda else "$0",
            delta="Profitable" if ebitda > 0 else "Operating Loss",
            delta_color="normal" if ebitda > 0 else "inverse",
        )

    with col4:
        st.metric(
            label="Average Order Value",
            value=f"${aov:,.2f}" if aov else "$0",
            delta=f"{metrics.get('total_transactions', 0):,} Orders",
            delta_color="off",
        )

    with col5:
        st.metric(
            label="Operating Margin",
            value=f"{metrics.get('operating_margin_pct', 0.0):.1f}%",
            delta="Healthy" if metrics.get("operating_margin_pct", 0) > 15.0 else "Attention",
        )
