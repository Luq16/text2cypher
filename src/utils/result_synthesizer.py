"""
Result synthesizer for converting query results to natural language
"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import json
import logging

from config import get_settings
from src.prompts import SystemPrompts

logger = logging.getLogger(__name__)


class ResultSynthesizer:
    """Synthesizes natural language responses from query results"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize result synthesizer

        Args:
            llm: Language model to use
        """
        settings = get_settings()

        if llm is None:
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0.3,  # Slightly creative for synthesis
                openai_api_key=settings.openai_api_key,
            )
        else:
            self.llm = llm

    def synthesize(
        self,
        question: str,
        cypher_query: str,
        results: List[Dict[str, Any]],
        max_results_in_context: int = 50,
    ) -> str:
        """
        Synthesize natural language response from query results

        Args:
            question: Original user question
            cypher_query: Cypher query that was executed
            results: Query results
            max_results_in_context: Maximum results to include in LLM context

        Returns:
            Natural language response
        """
        try:
            # Format results for LLM context
            formatted_results = self._format_results(
                results, max_results=max_results_in_context
            )

            # Generate synthesis prompt
            prompt = SystemPrompts.get_result_synthesis_prompt(
                question, cypher_query, formatted_results
            )

            # Get LLM response
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)

            return response.content.strip()

        except Exception as e:
            logger.error(f"Result synthesis failed: {e}")
            # Fallback to simple formatting
            return self._simple_format(question, results)

    def _format_results(
        self, results: List[Dict[str, Any]], max_results: int = 50
    ) -> str:
        """
        Format query results for inclusion in prompt

        Args:
            results: Query results
            max_results: Maximum number of results to format

        Returns:
            Formatted string
        """
        if not results:
            return "No results found."

        # Limit results to prevent token overflow
        limited_results = results[:max_results]
        result_count = len(results)

        # Format as JSON for clarity
        formatted = json.dumps(limited_results, indent=2, default=str)

        if result_count > max_results:
            formatted += f"\n\n(Showing {max_results} of {result_count} total results)"

        return formatted

    def _simple_format(
        self, question: str, results: List[Dict[str, Any]]
    ) -> str:
        """
        Simple fallback formatting without LLM

        Args:
            question: User question
            results: Query results

        Returns:
            Formatted response
        """
        if not results:
            return f"No results found for: {question}"

        response = [f"Found {len(results)} result(s):\n"]

        for i, result in enumerate(results[:10], 1):
            response.append(f"\n{i}. ")
            # Format key-value pairs
            for key, value in result.items():
                response.append(f"{key}: {value}, ")
            response[-1] = response[-1].rstrip(", ")  # Remove trailing comma

        if len(results) > 10:
            response.append(f"\n\n... and {len(results) - 10} more results")

        return "".join(response)

    def format_tabular(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results as a simple table

        Args:
            results: Query results

        Returns:
            Tabular string representation
        """
        if not results:
            return "No results."

        # Get column headers from first result
        headers = list(results[0].keys())

        # Calculate column widths
        col_widths = {h: len(h) for h in headers}
        for result in results:
            for header in headers:
                value_len = len(str(result.get(header, "")))
                col_widths[header] = max(col_widths[header], value_len)

        # Build table
        lines = []

        # Header row
        header_row = " | ".join(
            [h.ljust(col_widths[h]) for h in headers]
        )
        lines.append(header_row)

        # Separator
        separator = "-+-".join(["-" * col_widths[h] for h in headers])
        lines.append(separator)

        # Data rows
        for result in results[:50]:  # Limit to 50 rows
            row = " | ".join(
                [str(result.get(h, "")).ljust(col_widths[h]) for h in headers]
            )
            lines.append(row)

        if len(results) > 50:
            lines.append(f"\n... and {len(results) - 50} more rows")

        return "\n".join(lines)

    def create_summary_stats(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create summary statistics for results

        Args:
            results: Query results

        Returns:
            Dictionary of summary statistics
        """
        if not results:
            return {"total_results": 0}

        stats = {
            "total_results": len(results),
            "fields": list(results[0].keys()) if results else [],
        }

        # Add field-specific stats
        for field in stats["fields"]:
            values = [r.get(field) for r in results if r.get(field) is not None]

            if values:
                stats[f"{field}_count"] = len(values)

                # If numeric, add min/max/avg
                if isinstance(values[0], (int, float)):
                    stats[f"{field}_min"] = min(values)
                    stats[f"{field}_max"] = max(values)
                    stats[f"{field}_avg"] = sum(values) / len(values)

                # If string, add unique count
                elif isinstance(values[0], str):
                    stats[f"{field}_unique"] = len(set(values))

        return stats


# Singleton instance
_synthesizer = None


def get_result_synthesizer() -> ResultSynthesizer:
    """Get or create global result synthesizer instance"""
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = ResultSynthesizer()
    return _synthesizer
