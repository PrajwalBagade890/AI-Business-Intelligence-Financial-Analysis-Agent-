"""Pydantic schemas for AI agent tools, function calling, and structured inputs/outputs."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SQLQueryInput(BaseModel):
    query: str = Field(
        ...,
        description="Safe, read-only SQL query (SELECT or WITH statements only) to execute against SQLite database."
    )
    explanation: Optional[str] = Field(
        None,
        description="Brief human explanation of what this query aims to retrieve."
    )


class SQLQueryResult(BaseModel):
    success: bool
    row_count: int
    columns: List[str]
    data: List[Dict[str, Any]]
    execution_time_ms: float
    executed_sql: str
    error: Optional[str] = None


class RevenueMetricInput(BaseModel):
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    region: Optional[str] = Field(None, description="Filter by region (e.g., North America, EMEA, APAC, LATAM)")
    product_category: Optional[str] = Field(None, description="Filter by product category")


class GrowthCalculationInput(BaseModel):
    current_value: float = Field(..., description="Metric value for the current period")
    prior_value: float = Field(..., description="Metric value for the prior comparison period")
    metric_label: Optional[str] = Field("Revenue", description="Name of the metric being compared")


class ProfitabilityInput(BaseModel):
    revenue: float = Field(..., description="Total net revenue")
    cogs: float = Field(..., description="Total Cost of Goods Sold")
    operating_expenses: float = Field(..., description="Total operating expenses (OPEX)")


class AnomalyDetectionInput(BaseModel):
    category: Optional[str] = Field(None, description="Optional category to focus anomaly detection on")
    z_threshold: float = Field(2.0, description="Z-score threshold for outlier detection (default: 2.0)")


class BusinessReportOutput(BaseModel):
    executive_summary: str = Field(..., description="Concise synthesis of business performance")
    key_metrics: Dict[str, Any] = Field(..., description="Dictionary of computed financial figures")
    revenue_analysis: str = Field(..., description="Breakdown of revenue drivers, top products, customer tiers")
    expense_analysis: str = Field(..., description="Breakdown of OPEX and budget variances")
    trends_and_comparisons: str = Field(..., description="Period-over-period growth and trajectory")
    risks_and_anomalies: List[Dict[str, Any]] = Field(default_factory=list, description="Identified operational or financial risks")
    actionable_recommendations: List[str] = Field(..., description="Prioritized strategic guidance")
    data_sources: List[str] = Field(..., description="List of tables and calculations utilized")
