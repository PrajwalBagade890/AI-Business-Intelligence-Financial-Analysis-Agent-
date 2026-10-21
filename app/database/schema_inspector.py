"""Database schema introspection utilities for LLM reasoning and validation."""

import logging
from typing import Dict, List, Any
from sqlalchemy import inspect
from app.database.connection import engine

logger = logging.getLogger(__name__)


def get_schema_summary() -> Dict[str, Any]:
    """Retrieve full database schema metadata: table names, columns, types, primary/foreign keys."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    schema_info = {}

    for table in tables:
        columns = inspector.get_columns(table)
        fks = inspector.get_foreign_keys(table)
        pk = inspector.get_pk_constraint(table)

        col_details = []
        for col in columns:
            col_details.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "primary_key": col["name"] in pk.get("constrained_columns", []),
            })

        fk_details = []
        for fk in fks:
            fk_details.append({
                "constrained_columns": fk["constrained_columns"],
                "referred_table": fk["referred_table"],
                "referred_columns": fk["referred_columns"],
            })

        schema_info[table] = {
            "columns": col_details,
            "foreign_keys": fk_details,
            "primary_key": pk.get("constrained_columns", []),
        }

    return schema_info


def get_schema_markdown() -> str:
    """Generate a clean, structured Markdown representation of the database schema for LLM context."""
    schema = get_schema_summary()
    md_lines = ["### Database Schema Overview\n"]

    for table_name, details in schema.items():
        md_lines.append(f"#### Table: `{table_name}`")
        md_lines.append("| Column | Type | Constraints | Description |")
        md_lines.append("|---|---|---|---|")

        col_fks = {
            fk["constrained_columns"][0]: f"FK -> {fk['referred_table']}.{fk['referred_columns'][0]}"
            for fk in details["foreign_keys"]
            if fk["constrained_columns"]
        }

        for col in details["columns"]:
            constraints = []
            if col["primary_key"]:
                constraints.append("PRIMARY KEY")
            if not col["nullable"]:
                constraints.append("NOT NULL")
            if col["name"] in col_fks:
                constraints.append(col_fks[col["name"]])

            c_str = ", ".join(constraints) if constraints else "-"
            md_lines.append(f"| `{col['name']}` | `{col['type']}` | {c_str} | |")

        md_lines.append("")  # Empty line separator

    return "\n".join(md_lines)
