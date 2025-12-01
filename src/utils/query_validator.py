"""
Cypher query validation and refinement utilities
"""
import re
from typing import List, Dict, Tuple, Optional
import logging
from .schema_loader import get_schema_loader
from .neo4j_connector import get_neo4j_connector

logger = logging.getLogger(__name__)


class CypherQueryValidator:
    """Validates and refines Cypher queries"""

    def __init__(self):
        self.schema_loader = get_schema_loader()
        self.neo4j = get_neo4j_connector()

    def validate_query(self, query: str) -> Tuple[bool, List[str]]:
        """
        Comprehensive query validation

        Args:
            query: Cypher query to validate

        Returns:
            Tuple of (is_valid, list of validation errors/warnings)
        """
        errors = []

        # 1. Syntax validation
        is_valid_syntax, syntax_error = self.neo4j.validate_cypher_syntax(query)
        if not is_valid_syntax:
            errors.append(f"Syntax error: {syntax_error}")
            return False, errors

        # 2. Schema validation
        schema_valid, schema_errors = self._validate_schema_entities(query)
        if not schema_valid:
            errors.extend(schema_errors)

        # 3. Security checks
        security_valid, security_errors = self._check_security(query)
        if not security_valid:
            errors.extend(security_errors)
            return False, errors

        # 4. Performance checks (warnings)
        perf_warnings = self._check_performance(query)
        errors.extend(perf_warnings)

        # Query is valid if only warnings remain
        is_valid = all(not e.startswith("ERROR:") for e in errors)
        return is_valid, errors

    def _validate_schema_entities(self, query: str) -> Tuple[bool, List[str]]:
        """
        Validate node labels and relationship types against schema

        Args:
            query: Cypher query

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Extract node labels using regex
        node_pattern = r':(\w+)'
        node_labels = re.findall(node_pattern, query)

        # Extract relationship types
        rel_pattern = r'\[(?:[\w]*):(\w+)(?:\*)?(?:\.\.\d+)?\]'
        rel_types = re.findall(rel_pattern, query)

        # Validate against schema
        valid_nodes = self.schema_loader.get_node_types()
        valid_rels = self.schema_loader.get_relationship_types()

        for label in set(node_labels):
            if label not in valid_nodes:
                errors.append(f"ERROR: Unknown node label '{label}'")

        for rel_type in set(rel_types):
            if rel_type not in valid_rels:
                errors.append(f"ERROR: Unknown relationship type '{rel_type}'")

        return len(errors) == 0, errors

    def _check_security(self, query: str) -> Tuple[bool, List[str]]:
        """
        Check for potentially dangerous query patterns

        Args:
            query: Cypher query

        Returns:
            Tuple of (is_safe, list of security errors)
        """
        errors = []
        query_upper = query.upper()

        # Disallow destructive operations
        destructive_keywords = [
            "DELETE",
            "DETACH DELETE",
            "REMOVE",
            "DROP",
            "CREATE INDEX",
            "DROP INDEX",
            "CREATE CONSTRAINT",
            "DROP CONSTRAINT",
        ]

        for keyword in destructive_keywords:
            if keyword in query_upper:
                errors.append(
                    f"ERROR: Destructive operation '{keyword}' not allowed"
                )

        # Warn about MERGE and CREATE (may be needed for specific use cases)
        if "CREATE " in query_upper and "CREATE" not in ["CREATE INDEX"]:
            errors.append(
                "WARNING: CREATE operation detected - ensure this is intentional"
            )

        if "MERGE" in query_upper:
            errors.append(
                "WARNING: MERGE operation detected - ensure this is intentional"
            )

        return len([e for e in errors if e.startswith("ERROR")]) == 0, errors

    def _check_performance(self, query: str) -> List[str]:
        """
        Check for potential performance issues

        Args:
            query: Cypher query

        Returns:
            List of performance warnings
        """
        warnings = []
        query_upper = query.upper()

        # Check for missing LIMIT on MATCH queries
        if "MATCH" in query_upper and "LIMIT" not in query_upper:
            if "COUNT" not in query_upper and "RETURN COUNT" not in query_upper:
                warnings.append(
                    "WARNING: Query lacks LIMIT clause - may return large result set"
                )

        # Check for cartesian products (multiple MATCH without relationship)
        match_count = query_upper.count("MATCH")
        if match_count > 1 and "WHERE" not in query_upper:
            warnings.append(
                "WARNING: Multiple MATCH clauses without WHERE - possible cartesian product"
            )

        # Check for missing WHERE on variable-length patterns
        if re.search(r'\*\d+\.\.', query):
            if "WHERE" not in query_upper:
                warnings.append(
                    "WARNING: Variable-length pattern without WHERE clause may be expensive"
                )

        return warnings

    def suggest_improvements(self, query: str) -> List[str]:
        """
        Suggest query improvements

        Args:
            query: Cypher query

        Returns:
            List of improvement suggestions
        """
        suggestions = []
        query_upper = query.upper()

        # Suggest using parameters instead of string concatenation
        if "'" in query or '"' in query:
            suggestions.append(
                "Consider using query parameters instead of hardcoded strings"
            )

        # Suggest adding ORDER BY if LIMIT is present
        if "LIMIT" in query_upper and "ORDER BY" not in query_upper:
            suggestions.append(
                "Consider adding ORDER BY for consistent results with LIMIT"
            )

        # Suggest using indexes
        if "WHERE" in query_upper:
            suggestions.append(
                "Ensure appropriate indexes exist for WHERE clause properties"
            )

        return suggestions

    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract entities (node labels, relationships) from query

        Args:
            query: Cypher query

        Returns:
            Dictionary with node_labels and relationship_types lists
        """
        # Extract node labels
        node_pattern = r':(\w+)'
        node_labels = list(set(re.findall(node_pattern, query)))

        # Extract relationship types
        rel_pattern = r'\[(?:[\w]*):(\w+)(?:\*)?(?:\.\.\d+)?\]'
        rel_types = list(set(re.findall(rel_pattern, query)))

        return {"node_labels": node_labels, "relationship_types": rel_types}

    def refine_query(
        self, query: str, error_message: Optional[str] = None
    ) -> Optional[str]:
        """
        Attempt to automatically refine a query based on validation errors

        Args:
            query: Original query
            error_message: Error message from validation or execution

        Returns:
            Refined query or None if unable to refine
        """
        refined_query = query

        # Fix common issues
        if error_message:
            # Handle unknown node labels - try to find similar valid labels
            unknown_label_match = re.search(
                r"Unknown node label '(\w+)'", error_message
            )
            if unknown_label_match:
                unknown_label = unknown_label_match.group(1)
                # Try to find similar label in schema
                valid_labels = self.schema_loader.get_node_types()
                # Simple similarity check (case-insensitive)
                for valid_label in valid_labels:
                    if unknown_label.lower() in valid_label.lower() or valid_label.lower() in unknown_label.lower():
                        refined_query = refined_query.replace(
                            f":{unknown_label}", f":{valid_label}"
                        )
                        logger.info(
                            f"Refined query: replaced '{unknown_label}' with '{valid_label}'"
                        )
                        return refined_query

        # Add LIMIT if missing
        if "MATCH" in refined_query.upper() and "LIMIT" not in refined_query.upper():
            if not refined_query.strip().endswith(";"):
                refined_query = refined_query.strip() + " LIMIT 100"
            else:
                refined_query = (
                    refined_query.strip()[:-1].strip() + " LIMIT 100;"
                )

        return refined_query if refined_query != query else None


# Singleton instance
_validator = None


def get_query_validator() -> CypherQueryValidator:
    """Get or create global query validator instance"""
    global _validator
    if _validator is None:
        _validator = CypherQueryValidator()
    return _validator
