"""Pydantic request and response models for FastAPI endpoints."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    database_connected: bool
    effective_llm_provider: str
    table_counts: Dict[str, int]


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language business or financial question", min_length=2)
    session_id: Optional[str] = Field("default_session", description="Optional session identifier")


class QueryResponse(BaseModel):
    query: str
    intent: str
    final_response: str
    calculated_metrics: Dict[str, Any]
    generated_sql: Optional[str] = None
    validation_passed: bool
    validation_notes: List[str]
    insights: List[str]
    anomalies: List[Dict[str, Any]]
    execution_steps: List[str]


class DirectSQLRequest(BaseModel):
    sql: str = Field(..., description="Safe read-only SQL SELECT query")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DirectSQLResponse(BaseModel):
    success: bool
    row_count: int
    columns: List[str]
    data: List[Dict[str, Any]]
    execution_time_ms: float
    executed_sql: str
    error: Optional[str] = None


class CalculationRequest(BaseModel):
    metric_type: str = Field(
        ...,
        description="Type of calculation: 'growth_rate', 'profitability', 'revenue_summary', 'expense_breakdown'"
    )
    parameters: Dict[str, Any] = Field(..., description="Key-value arguments matching the selected metric formula")


class ReportGenerationRequest(BaseModel):
    year: int = Field(2025, description="Fiscal year for the comprehensive report")


class ReportGenerationResponse(BaseModel):
    status: str
    report: Dict[str, Any]
    product_ranking: List[Dict[str, Any]]
    expense_breakdown: Dict[str, Any]
    key_metrics: Dict[str, Any]
