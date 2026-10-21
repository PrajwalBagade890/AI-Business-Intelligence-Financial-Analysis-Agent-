"""Model Context Protocol (MCP) Server for Business Intelligence & Financial Analysis.

Exposes analytical tools over standard JSON-RPC 2.0 (stdio) for Google Antigravity,
Claude Desktop, and other MCP clients.
"""

import sys
import json
import logging
from typing import Dict, Any, List
import pandas as pd
from app.database.schema_inspector import get_schema_summary
from app.tools.sql_tool import safe_sql_executor
from app.tools.financial_tools import (
    calculate_growth_rate,
    calculate_profitability,
    calculate_revenue_summary,
    calculate_expense_breakdown,
)
from app.tools.anomaly_tools import detect_expense_spikes
from app.workflows.crewai_workflow import generate_comprehensive_report

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("mcp_server")

# Define MCP Tools Catalog
TOOLS = [
    {
        "name": "get_database_schema",
        "description": "Inspect the business database schema, including all tables, columns, data types, and foreign key relationships.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "execute_safe_sql",
        "description": "Execute a read-only SQL query against the business intelligence database. Enforces strict AST validation and maximum row limits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The SQL SELECT query to execute.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "calculate_growth_rate",
        "description": "Calculate exact period-over-period absolute and percentage growth rates using deterministic financial mathematics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "current_value": {"type": "number", "description": "Metric value in current period."},
                "prior_value": {"type": "number", "description": "Metric value in prior comparison period."},
            },
            "required": ["current_value", "prior_value"],
        },
    },
    {
        "name": "calculate_profitability",
        "description": "Calculate gross profit, gross margin %, operating profit (EBITDA), and operating margin %.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "revenue": {"type": "number", "description": "Total net revenue."},
                "cogs": {"type": "number", "description": "Cost of Goods Sold (COGS)."},
                "operating_expenses": {"type": "number", "description": "Total operating expenses (OPEX)."},
            },
            "required": ["revenue", "cogs", "operating_expenses"],
        },
    },
    {
        "name": "detect_expense_anomalies",
        "description": "Identify statistically anomalous expense transactions exceeding Z-score threshold.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "z_threshold": {"type": "number", "description": "Z-score threshold (default: 2.0).", "default": 2.0},
            },
        },
    },
    {
        "name": "generate_executive_report",
        "description": "Execute the full multi-agent collaborative pipeline to generate an executive board-ready financial report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer", "description": "Fiscal year to analyze (default: 2025).", "default": 2025},
            },
        },
    },
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Any:
    """Route tool call to appropriate deterministic function."""
    if name == "get_database_schema":
        return get_schema_summary()

    elif name == "execute_safe_sql":
        query = arguments.get("query", "")
        return safe_sql_executor.execute_query(query)

    elif name == "calculate_growth_rate":
        curr = float(arguments.get("current_value", 0))
        prior = float(arguments.get("prior_value", 0))
        return calculate_growth_rate(curr, prior)

    elif name == "calculate_profitability":
        rev = float(arguments.get("revenue", 0))
        cogs = float(arguments.get("cogs", 0))
        opex = float(arguments.get("operating_expenses", 0))
        return calculate_profitability(rev, cogs, opex)

    elif name == "detect_expense_anomalies":
        z_th = float(arguments.get("z_threshold", 2.0))
        res = safe_sql_executor.execute_query("SELECT * FROM expenses ORDER BY expense_date DESC LIMIT 500;")
        df = pd.DataFrame(res["data"]) if res["success"] else pd.DataFrame()
        return detect_expense_spikes(df, z_threshold=z_th)

    elif name == "generate_executive_report":
        yr = int(arguments.get("year", 2025))
        return generate_comprehensive_report(target_year=yr)

    else:
        raise ValueError(f"Unknown tool: {name}")


def run_stdio_server():
    """Main JSON-RPC stdio event loop."""
    logger.info("BI MCP Server started on stdio.")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            req_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "business-intelligence-mcp",
                            "version": "1.0.0",
                        },
                    },
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS},
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                try:
                    tool_output = handle_tool_call(tool_name, tool_args)
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(tool_output, indent=2, default=str),
                                }
                            ]
                        },
                    }
                except Exception as ex:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32000,
                            "message": str(ex),
                        },
                    }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found",
                    },
                }

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")


if __name__ == "__main__":
    run_stdio_server()
