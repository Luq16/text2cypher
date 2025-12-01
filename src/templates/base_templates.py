"""
Base classes for predefined Cypher query templates
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import re


@dataclass
class QueryTemplate:
    """Represents a predefined Cypher query template"""

    name: str
    description: str
    cypher: str
    parameters: Dict[str, type]
    intent: str
    example_question: str
    tags: List[str]

    def format(self, **kwargs) -> str:
        """
        Format the Cypher query with provided parameters

        Args:
            **kwargs: Parameter values

        Returns:
            Formatted Cypher query
        """
        # Validate all required parameters are provided
        missing_params = set(self.parameters.keys()) - set(kwargs.keys())
        if missing_params:
            raise ValueError(
                f"Missing required parameters: {', '.join(missing_params)}"
            )

        # Format the query
        return self.cypher.format(**kwargs)

    def matches_keywords(self, query: str, keywords: List[str]) -> bool:
        """
        Check if query contains any of the keywords

        Args:
            query: User query
            keywords: List of keywords to check

        Returns:
            True if any keyword matches
        """
        query_lower = query.lower()
        return any(keyword.lower() in query_lower for keyword in keywords)


class BaseTemplateLibrary(ABC):
    """Base class for template libraries"""

    def __init__(self):
        self.templates: List[QueryTemplate] = []
        self._build_templates()

    @abstractmethod
    def _build_templates(self):
        """Build the template library - to be implemented by subclasses"""
        pass

    def get_all_templates(self) -> List[QueryTemplate]:
        """Get all templates in this library"""
        return self.templates

    def get_template_by_name(self, name: str) -> Optional[QueryTemplate]:
        """Get template by exact name"""
        for template in self.templates:
            if template.name == name:
                return template
        return None

    def find_matching_templates(
        self, query: str, intent: Optional[str] = None
    ) -> List[QueryTemplate]:
        """
        Find templates that match the query

        Args:
            query: User query
            intent: Optional intent filter

        Returns:
            List of matching templates
        """
        matches = []

        for template in self.templates:
            # Filter by intent if provided
            if intent and template.intent != intent:
                continue

            # Check if template tags match query keywords
            if template.matches_keywords(query, template.tags):
                matches.append(template)

        return matches

    def get_templates_by_intent(self, intent: str) -> List[QueryTemplate]:
        """Get all templates for a specific intent"""
        return [t for t in self.templates if t.intent == intent]


class ParameterExtractor:
    """Extracts parameters from natural language queries"""

    @staticmethod
    def extract_entity_name(query: str, entity_type: str) -> Optional[str]:
        """
        Extract entity name from query

        Args:
            query: User query
            entity_type: Type of entity (drug, disease, gene, etc.)

        Returns:
            Extracted entity name or None
        """
        # Common patterns for entity extraction
        patterns = [
            rf"{entity_type}\s+['\"]?([^'\"]+?)['\"]?(?:\s|$|\?)",  # "drug Aspirin"
            rf"for\s+['\"]?([^'\"]+?)['\"]?(?:\s|$|\?)",  # "for cancer"
            rf"called\s+['\"]?([^'\"]+?)['\"]?(?:\s|$|\?)",  # "called Imatinib"
            rf"named\s+['\"]?([^'\"]+?)['\"]?(?:\s|$|\?)",  # "named EGFR"
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    @staticmethod
    def extract_limit(query: str, default: int = 10) -> int:
        """
        Extract result limit from query

        Args:
            query: User query
            default: Default limit if not found

        Returns:
            Limit value
        """
        # Look for "top N", "first N", "N results", etc.
        patterns = [
            r"top\s+(\d+)",
            r"first\s+(\d+)",
            r"(\d+)\s+results?",
            r"limit\s+(\d+)",
            r"show\s+(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return default

    @staticmethod
    def extract_threshold(query: str, default: float = 0.7) -> float:
        """
        Extract similarity/confidence threshold from query

        Args:
            query: User query
            default: Default threshold if not found

        Returns:
            Threshold value
        """
        patterns = [
            r"confidence\s+(?:of\s+)?(\d+\.?\d*)%?",
            r"threshold\s+(?:of\s+)?(\d+\.?\d*)",
            r"similarity\s+(?:of\s+)?(\d+\.?\d*)%?",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                # Convert percentage to decimal if needed
                if value > 1:
                    value = value / 100
                return value

        return default
