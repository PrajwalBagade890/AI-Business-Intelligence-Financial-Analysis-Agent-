"""Safe, sandboxed SQL query validator and executor for analytical business queries."""

import re
import time
import sqlite3
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy import text
from app.config import settings
from app.database.connection import engine

logger = logging.getLogger(__name__)

# Disallowed SQL commands that mutate or breach safety
FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "REPLACE",
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "ATTACH", "DETACH",
    "PRAGMA", "VACUUM", "LOAD_EXTENSION", "REINDEX", "MERGE"
}

# Regex to detect semicolon-separated multiple statements (excluding strings)
MULTIPLE_STATEMENTS_REGEX = re.compile(r";\s*(\S+)")


class SQLValidationError(Exception):
    """Raised when an SQL query fails safety validation."""
    pass


class SafeSQLExecutor:
    """Validates and executes read-only SQL queries against the analytical database."""

    def __init__(self, max_rows: int = 1000, timeout_seconds: float = 5.0):
        self.max_rows = max_rows
        self.timeout_seconds = timeout_seconds

    def validate_sql(self, sql_query: str) -> str:
        """Validate that the SQL query is strictly read-only, safe, and single-statement.

        Returns cleaned, normalized SQL query.
        Raises SQLValidationError if query violates safety constraints.
        """
        if not sql_query or not sql_query.strip():
            raise SQLValidationError("SQL query cannot be empty.")

        query = sql_query.strip()

        # Remove markdown code fences if LLM produced them
        if query.startswith("```"):
            lines = query.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            query = "\n".join(lines).strip()

        # Remove trailing semicolon
        if query.endswith(";"):
            query = query[:-1].strip()

        # Block multiple statements
        # Check for semicolons outside of quotes
        in_single_quote = False
        in_double_quote = False
        for i, char in enumerate(query):
            if char == "'" and (i == 0 or query[i - 1] != "\\"):
                in_single_quote = not in_single_quote
            elif char == '"' and (i == 0 or query[i - 1] != "\\"):
                in_double_quote = not in_double_quote
            elif char == ";" and not in_single_quote and not in_double_quote:
                remaining = query[i + 1:].strip()
                if remaining:
                    raise SQLValidationError(
                        "Multiple SQL statements detected. Only a single SELECT query is permitted."
                    )

        # Normalize whitespace for keyword token checking
        tokens = re.findall(r"\b[A-Za-z_]+\b", query.upper())
        if not tokens:
            raise SQLValidationError("Invalid SQL syntax: no recognizable tokens.")

        # Ensure starting with SELECT or WITH (for CTEs)
        first_token = tokens[0]
        if first_token not in ("SELECT", "WITH", "EXPLAIN"):
            raise SQLValidationError(
                f"Prohibited query start '{first_token}'. Only 'SELECT' or 'WITH' (CTE) queries are allowed."
            )

        # Verify no forbidden DDL/DML keywords appear anywhere in token stream
        forbidden_found = set(tokens).intersection(FORBIDDEN_KEYWORDS)
        if forbidden_found:
            raise SQLValidationError(
                f"Prohibited SQL command(s) detected: {', '.join(forbidden_found)}. "
                "Only read-only analytical queries are authorized."
            )

        # Enforce or inject LIMIT clause
        has_limit = "LIMIT" in tokens
        if not has_limit:
            query = f"{query} LIMIT {self.max_rows}"
        else:
            # Check if existing limit exceeds maximum allowed
            limit_match = re.search(r"\bLIMIT\s+(\d+)", query, re.IGNORECASE)
            if limit_match:
                limit_val = int(limit_match.group(1))
                if limit_val > self.max_rows:
                    query = re.sub(
                        r"\bLIMIT\s+\d+",
                        f"LIMIT {self.max_rows}",
                        query,
                        flags=re.IGNORECASE,
                    )

        return query

    def execute_query(self, sql_query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate and execute a read-only query safely.

        Returns a dictionary with:
        - success: bool
        - row_count: int
        - columns: List[str]
        - data: List[Dict[str, Any]]
        - execution_time_ms: float
        - executed_sql: str
        - error: Optional[str]
        """
        start_time = time.perf_counter()
        params = params or {}

        try:
            validated_query = self.validate_sql(sql_query)

            # Execute via SQLAlchemy read-only session
            with engine.connect() as connection:
                # Set transaction isolation / read only if available
                result = connection.execute(text(validated_query), params)
                columns = list(result.keys())
                rows = result.fetchall()

                # Convert to dict records
                data = [dict(zip(columns, row)) for row in rows]
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

                return {
                    "success": True,
                    "row_count": len(data),
                    "columns": columns,
                    "data": data,
                    "execution_time_ms": elapsed_ms,
                    "executed_sql": validated_query,
                    "error": None,
                }

        except SQLValidationError as ve:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning(f"SQL Validation Error: {ve}")
            return {
                "success": False,
                "row_count": 0,
                "columns": [],
                "data": [],
                "execution_time_ms": elapsed_ms,
                "executed_sql": sql_query,
                "error": f"Security Validation Failed: {str(ve)}",
            }
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"SQL Execution Error: {e}")
            return {
                "success": False,
                "row_count": 0,
                "columns": [],
                "data": [],
                "execution_time_ms": elapsed_ms,
                "executed_sql": sql_query,
                "error": f"Database Execution Error: {str(e)}",
            }

    def execute_to_dataframe(self, sql_query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute query safely and return results as a Pandas DataFrame."""
        res = self.execute_query(sql_query, params)
        if not res["success"]:
            raise RuntimeError(res["error"])
        return pd.DataFrame(res["data"])


# Global singleton instance
safe_sql_executor = SafeSQLExecutor(
    max_rows=settings.SQL_MAX_ROWS,
    timeout_seconds=settings.SQL_EXECUTION_TIMEOUT_SECONDS,
)
