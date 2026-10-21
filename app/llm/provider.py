"""Configurable LLM provider factory with multi-provider support and deterministic fallback."""

import logging
import json
import re
from typing import Optional, Any, List, Dict
from app.config import settings

logger = logging.getLogger(__name__)


class MockDeterministicLLM:
    """Intelligent deterministic fallback LLM.

    Handles natural language business queries, converts them into safe SQL queries,
    and formats analytical outputs without requiring an external paid API key.
    """

    def __init__(self, model_name: str = "mock-deterministic-v1"):
        self.model_name = model_name

    def invoke(self, prompt: Any) -> Any:
        """Process prompt deterministically and return simulated message response."""
        prompt_text = str(prompt)
        text_lower = prompt_text.lower()

        # Classify query intent and generate SQL
        if "revenue" in text_lower and ("quarter" in text_lower or "q3" in text_lower or "q4" in text_lower or "q1" in text_lower):
            sql = "SELECT strftime('%Y-Q' || ((strftime('%m', order_date) - 1) / 3 + 1), order_date) as quarter, SUM(net_amount) as total_revenue, COUNT(id) as transactions FROM sales WHERE payment_status = 'Completed' GROUP BY quarter ORDER BY quarter DESC LIMIT 4;"
            explanation = "Calculates total net revenue and transaction volume for recent quarters."
        elif "product" in text_lower and ("profit" in text_lower or "highest" in text_lower or "margin" in text_lower):
            sql = "SELECT p.product_name, p.category, SUM(s.net_amount) as total_revenue, SUM(s.gross_profit) as total_profit, ROUND((SUM(s.gross_profit) * 100.0 / SUM(s.net_amount)), 2) as margin_pct FROM sales s JOIN products p ON s.product_id = p.id WHERE s.payment_status = 'Completed' GROUP BY p.id, p.product_name ORDER BY total_profit DESC LIMIT 10;"
            explanation = "Aggregates revenue and gross profit by product to identify highest profit generators."
        elif "monthly" in text_lower and ("revenue" in text_lower or "trend" in text_lower or "change" in text_lower):
            sql = "SELECT strftime('%Y-%m', order_date) as month, SUM(net_amount) as monthly_revenue, COUNT(id) as order_count, ROUND(AVG(net_amount), 2) as avg_order_value FROM sales WHERE payment_status = 'Completed' GROUP BY month ORDER BY month ASC LIMIT 24;"
            explanation = "Monthly revenue trajectory, order volume, and average order value trends."
        elif "expense" in text_lower or "opex" in text_lower or "cost" in text_lower:
            sql = "SELECT category, department, SUM(amount) as total_spent, COUNT(id) as transaction_count FROM expenses GROUP BY category, department ORDER BY total_spent DESC;"
            explanation = "Breakdown of operating expenses grouped by strategic category and department."
        elif "trend" in text_lower or "risk" in text_lower or "anomal" in text_lower:
            sql = "SELECT e.category, strftime('%Y-%m', e.expense_date) as month, SUM(e.amount) as actual_spend, b.budgeted_amount as budget FROM expenses e LEFT JOIN budgets b ON e.category = b.category AND strftime('%Y', e.expense_date) = cast(b.year as text) AND strftime('%m', e.expense_date) = printf('%02d', b.month) GROUP BY e.category, month ORDER BY month DESC LIMIT 20;"
            explanation = "Compares actual monthly expense outlays against budgeted targets to detect budget overruns and operational risks."
        elif "customer" in text_lower or "client" in text_lower:
            sql = "SELECT c.customer_name, c.tier, c.industry, c.region, SUM(s.net_amount) as total_spend, COUNT(s.id) as orders FROM customers c JOIN sales s ON c.id = s.customer_id GROUP BY c.id ORDER BY total_spend DESC LIMIT 10;"
            explanation = "Top 10 enterprise accounts ranked by cumulative net spend."
        else:
            sql = "SELECT strftime('%Y', order_date) as year, SUM(net_amount) as total_revenue, SUM(gross_profit) as total_profit, COUNT(id) as total_orders FROM sales WHERE payment_status = 'Completed' GROUP BY year ORDER BY year DESC LIMIT 5;"
            explanation = "Annual high-level revenue and profitability summary."

        class MockAIMessage:
            def __init__(self, content: str):
                self.content = content

        content_dict = {
            "query_type": "sql_data_retrieval",
            "sql_query": sql,
            "explanation": explanation,
            "is_fallback": True,
        }
        return MockAIMessage(json.dumps(content_dict))


def get_llm(temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Any:
    """Initialize and return configured LLM instance based on environment settings.

    Supports:
    - 'gemini' (ChatGoogleGenerativeAI)
    - 'openai' (ChatOpenAI)
    - 'mock' (Deterministic fallback)
    """
    provider = settings.effective_llm_provider
    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
    tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

    logger.info(f"Initializing LLM with effective provider: {provider}")

    if provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
            return ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL_NAME if "gemini" in settings.LLM_MODEL_NAME else "gemini-1.5-flash",
                google_api_key=api_key,
                temperature=temp,
                max_output_tokens=tokens,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini LLM: {e}. Falling back to deterministic engine.")
            return MockDeterministicLLM()

    elif provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model_name=settings.LLM_MODEL_NAME,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=temp,
                max_tokens=tokens,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI LLM: {e}. Falling back to deterministic engine.")
            return MockDeterministicLLM()

    # Default fallback
    return MockDeterministicLLM()
