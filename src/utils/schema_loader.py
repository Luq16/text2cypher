"""
Schema loader for QIAGEN BKB knowledge graph
"""
import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class BKBSchemaLoader:
    """Loads and provides access to QIAGEN BKB schema information"""

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize schema loader

        Args:
            schema_path: Path to schema JSON file. If None, uses default location.
        """
        if schema_path is None:
            # Default to config/bkb_schema.json relative to project root
            project_root = Path(__file__).parent.parent.parent
            schema_path = project_root / "config" / "bkb_schema.json"

        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict:
        """Load schema from JSON file"""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with open(self.schema_path, "r") as f:
            return json.load(f)

    def get_node_types(self) -> List[str]:
        """Get list of all node type labels"""
        return [node["label"] for node in self.schema["node_types"]]

    def get_relationship_types(self) -> List[str]:
        """Get list of all relationship type names"""
        return [rel["type"] for rel in self.schema["relationship_types"]]

    def get_node_properties(self, node_label: str) -> List[str]:
        """Get properties for a specific node type"""
        for node in self.schema["node_types"]:
            if node["label"] == node_label:
                return node.get("properties", [])
        return []

    def get_relationship_properties(self, rel_type: str) -> List[str]:
        """Get properties for a specific relationship type"""
        for rel in self.schema["relationship_types"]:
            if rel["type"] == rel_type:
                return rel.get("properties", [])
        return []

    def get_common_patterns(self) -> List[Dict]:
        """Get common query patterns"""
        return self.schema.get("common_patterns", [])

    def get_pattern_by_name(self, pattern_name: str) -> Optional[Dict]:
        """Get a specific pattern by name"""
        for pattern in self.get_common_patterns():
            if pattern["name"] == pattern_name:
                return pattern
        return None

    def get_schema_summary(self) -> str:
        """
        Generate a human-readable schema summary for LLM context

        Returns:
            Formatted string describing the schema
        """
        node_types = self.get_node_types()
        rel_types = self.get_relationship_types()

        summary = f"""QIAGEN Biomedical Knowledge Base (BKB) Schema

Node Types ({len(node_types)}):
{', '.join(node_types)}

Relationship Types ({len(rel_types)}):
{', '.join(rel_types)}

Common Query Patterns:
"""
        for pattern in self.get_common_patterns():
            summary += f"- {pattern['name']}: {pattern['description']}\n"

        return summary

    def get_detailed_schema(self) -> str:
        """
        Generate detailed schema description for text2cypher context

        Returns:
            Detailed schema information including properties
        """
        output = ["QIAGEN BKB Knowledge Graph Schema\n"]
        output.append("=" * 50)

        # Node types with properties
        output.append("\n## Node Types:\n")
        for node in self.schema["node_types"]:
            output.append(f"### {node['label']}")
            output.append(f"Description: {node['description']}")
            output.append(f"Properties: {', '.join(node.get('properties', []))}")
            if "count" in node:
                output.append(f"Count: {node['count']:,}")
            output.append("")

        # Relationship types
        output.append("\n## Relationship Types:\n")
        for rel in self.schema["relationship_types"]:
            output.append(f"### {rel['type']}")
            output.append(f"Description: {rel['description']}")
            output.append(f"Source: {', '.join(rel.get('source', []))}")
            output.append(f"Target: {', '.join(rel.get('target', []))}")
            if "properties" in rel:
                output.append(f"Properties: {', '.join(rel['properties'])}")
            output.append("")

        # Common patterns
        output.append("\n## Common Patterns:\n")
        for pattern in self.get_common_patterns():
            output.append(f"### {pattern['name']}")
            output.append(f"Description: {pattern['description']}")
            output.append(f"Pattern: {pattern['pattern']}")
            output.append("")

        return "\n".join(output)

    def get_cypher_schema_context(self) -> str:
        """
        Generate concise schema context optimized for Cypher generation

        Returns:
            Schema context formatted for LLM prompts
        """
        context = [
            "# QIAGEN BKB Schema for Cypher Query Generation\n",
            "## Available Node Labels:",
            ", ".join(self.get_node_types()),
            "\n## Available Relationship Types:",
            ", ".join(self.get_relationship_types()),
            "\n## Example Patterns:"
        ]

        for pattern in self.get_common_patterns()[:5]:  # Top 5 patterns
            context.append(f"- {pattern['name']}: {pattern['pattern']}")

        return "\n".join(context)

    def validate_query_entities(
        self, node_labels: List[str], rel_types: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Validate that node labels and relationship types exist in schema

        Args:
            node_labels: List of node labels to validate
            rel_types: List of relationship types to validate

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        valid_nodes = self.get_node_types()
        valid_rels = self.get_relationship_types()

        for label in node_labels:
            if label not in valid_nodes:
                errors.append(f"Invalid node label: {label}")

        for rel in rel_types:
            if rel not in valid_rels:
                errors.append(f"Invalid relationship type: {rel}")

        return len(errors) == 0, errors


# Singleton instance
_schema_loader = None


def get_schema_loader() -> BKBSchemaLoader:
    """Get or create global schema loader instance"""
    global _schema_loader
    if _schema_loader is None:
        _schema_loader = BKBSchemaLoader()
    return _schema_loader
