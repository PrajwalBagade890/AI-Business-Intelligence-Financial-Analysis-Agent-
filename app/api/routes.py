"""FastAPI REST routes for Business Intelligence & Financial Analysis platform."""

import logging
from typing import Dict, Any
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.database.connection import get_db, engine
from app.database.schema_inspector import get_schema_summary
from app.tools.sql_tool import safe_sql_executor
from app.tools.financial_tools import (
    calculate_growth_rate,
    calculate_profitability,
    calculate_revenue_summary,
    calculate_expense_breakdown,
)
from app.workflows.langgraph_workflow import bi_agent_workflow
from app.workflows.crewai_workflow import generate_comprehensive_report
from app.api.schemas import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
    DirectSQLRequest,
    DirectSQLResponse,
    CalculationRequest,
    ReportGenerationRequest,
    ReportGenerationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Health check and operational diagnostics."""
    db_connected = False
    table_counts = {}

    try:
        with engine.connect() as conn:
            for table in ["customers", "products", "sales", "expenses", "budgets"]:
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    table_counts[table] = count
                except Exception:
                    table_counts[table] = 0
            db_connected = True
    except Exception as e:
        logger.error(f"Health check DB error: {e}")

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        database_connected=db_connected,
        effective_llm_provider=settings.effective_llm_provider,
        table_counts=table_counts,
    )


@router.post("/query", response_model=QueryResponse)
def query_agent(req: QueryRequest):
    """Execute natural language query via LangGraph stateful 6-stage workflow."""
    try:
        initial_state = {
            "user_query": req.query,
            "intent": "",
            "extracted_entities": {},
            "generated_sql": None,
            "sql_result": None,
            "calculated_metrics": {},
            "validation_passed": False,
            "validation_notes": [],
            "insights": [],
            "anomalies": [],
            "final_response": "",
            "execution_steps": [],
            "error": None,
        }

        result = bi_agent_workflow.invoke(initial_state)

        return QueryResponse(
            query=req.query,
            intent=result.get("intent", "general"),
            final_response=result.get("final_response", ""),
            calculated_metrics=result.get("calculated_metrics", {}),
            generated_sql=result.get("generated_sql"),
            validation_passed=result.get("validation_passed", True),
            validation_notes=result.get("validation_notes", []),
            insights=result.get("insights", []),
            anomalies=result.get("anomalies", []),
            execution_steps=result.get("execution_steps", []),
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent workflow error: {str(e)}")


@router.get("/data/schema")
def get_schema():
    """Retrieve full database schema definition and relations."""
    try:
        return get_schema_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inspect schema: {str(e)}")


@router.post("/data/query", response_model=DirectSQLResponse)
def execute_safe_sql(req: DirectSQLRequest):
    """Execute a validated, read-only SQL query with AST safety and execution limits."""
    res = safe_sql_executor.execute_query(req.sql, req.params)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return DirectSQLResponse(**res)


@router.post("/calculate")
def direct_calculation(req: CalculationRequest):
    """Execute deterministic financial calculations on provided parameters."""
    m_type = req.metric_type
    p = req.parameters

    try:
        if m_type == "growth_rate":
            curr = float(p.get("current_value", 0.0))
            prior = float(p.get("prior_value", 0.0))
            return calculate_growth_rate(curr, prior)

        elif m_type == "profitability":
            rev = float(p.get("revenue", 0.0))
            cogs = float(p.get("cogs", 0.0))
            opex = float(p.get("operating_expenses", 0.0))
            return calculate_profitability(rev, cogs, opex)

        elif m_type == "revenue_summary":
            # Expects sales data list
            sales_records = p.get("sales_records", [])
            df = pd.DataFrame(sales_records)
            return calculate_revenue_summary(df)

        elif m_type == "expense_breakdown":
            expenses_records = p.get("expense_records", [])
            df = pd.DataFrame(expenses_records)
            return calculate_expense_breakdown(df)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown calculation type '{m_type}'. Supported: growth_rate, profitability, revenue_summary, expense_breakdown."
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")


@router.post("/reports/generate", response_model=ReportGenerationResponse)
def generate_report(req: ReportGenerationRequest):
    """Generate a multi-agent board-ready financial report."""
    try:
        result = generate_comprehensive_report(target_year=req.year)
        return ReportGenerationResponse(**result)
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
