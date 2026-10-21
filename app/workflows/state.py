"""LangGraph workflow state definition."""

from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """State object passed through LangGraph workflow stages."""
    user_query: str
    intent: str
    extracted_entities: Dict[str, Any]
    generated_sql: Optional[str]
    sql_result: Optional[Dict[str, Any]]
    calculated_metrics: Dict[str, Any]
    validation_passed: bool
    validation_notes: List[str]
    insights: List[str]
    anomalies: List[Dict[str, Any]]
    final_response: str
    execution_steps: List[str]
    error: Optional[str]
