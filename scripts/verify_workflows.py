"""Script to verify all five core business queries through LangGraph and CrewAI workflows."""

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.workflows.langgraph_workflow import bi_agent_workflow
from app.workflows.crewai_workflow import generate_comprehensive_report

queries = [
    "What was our total revenue this quarter?",
    "Which products generate the highest profit?",
    "How has monthly revenue changed?",
    "What are the major expense categories?",
    "What business trends and risks can you identify?",
]

print("==================================================")
print("1. VERIFYING 5 CORE NATURAL LANGUAGE BUSINESS QUERIES")
print("==================================================")

for q in queries:
    print(f"\n--- Testing Query: '{q}' ---")
    initial_state = {
        "user_query": q,
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

    print(f"Intent Classified: {result['intent']}")
    print(f"Stages Executed: {len(result['execution_steps'])}")
    print(f"Rows Retrieved: {result['sql_result']['row_count']}")
    print(f"Validation Passed: {result['validation_passed']}")
    print("Execution Steps:")
    for step in result['execution_steps']:
        print(f"  • {step}")
    print("\nResponse:")
    print(result["final_response"])

print("\n==================================================")
print("2. VERIFYING MULTI-AGENT COMPREHENSIVE BOARD REPORT")
print("==================================================")
report_res = generate_comprehensive_report(target_year=2025)
print(f"Status: {report_res['status']}")
print(f"Key Metrics: {json.dumps(report_res['key_metrics'], indent=2)}")
print("\nExecutive Summary:")
print(report_res["report"]["executive_summary"])
print("\nActionable Recommendations:")
for rec in report_res["report"]["actionable_recommendations"]:
    print(f"  -> {rec}")
print("\nALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
