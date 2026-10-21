"""Integration tests for the LangGraph 6-stage Business Intelligence workflow."""

import pytest
from app.database.connection import init_db
from app.database.seed_data import seed_database
from app.workflows.langgraph_workflow import bi_agent_workflow


@pytest.fixture(scope="module", autouse=True)
def setup_data():
    init_db()
    seed_database(force_recreate=False)


def test_langgraph_revenue_query():
    """Test revenue query execution through LangGraph state machine."""
    initial_state = {
        "user_query": "What was our total revenue this quarter?",
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

    assert result["intent"] in ["metric_query", "trend_analysis", "executive_report"]
    assert result["generated_sql"] is not None
    assert result["sql_result"]["success"] is True
    assert result["sql_result"]["row_count"] > 0
    assert result["validation_passed"] is True
    assert len(result["execution_steps"]) == 6
    assert "Business Intelligence" in result["final_response"]


def test_langgraph_product_profitability():
    """Test product profit query through LangGraph state machine."""
    initial_state = {
        "user_query": "Which products generate the highest profit?",
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

    assert result["intent"] == "product_profitability"
    assert "products_ranking" in result["calculated_metrics"]
    assert len(result["calculated_metrics"]["products_ranking"]) > 0
    assert "Profit Engine" in "".join(result["insights"]) or len(result["insights"]) > 0
