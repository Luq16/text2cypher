"""
Neo4j database connector for QIAGEN BKB
"""
from neo4j import GraphDatabase, Driver, Result
from typing import List, Dict, Any, Optional
import logging
from contextlib import contextmanager
from config import get_settings

logger = logging.getLogger(__name__)


class Neo4jConnector:
    """Manages Neo4j database connections and query execution"""

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        """
        Initialize Neo4j connector

        Args:
            uri: Neo4j URI (defaults to settings)
            username: Neo4j username (defaults to settings)
            password: Neo4j password (defaults to settings)
            database: Database name (defaults to settings)
        """
        settings = get_settings()

        self.uri = uri or settings.neo4j_uri
        self.username = username or settings.neo4j_username
        self.password = password or settings.neo4j_password
        self.database = database or settings.neo4j_database

        self._driver: Optional[Driver] = None

    @property
    def driver(self) -> Driver:
        """Get or create driver instance"""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            )
            logger.info(f"Connected to Neo4j at {self.uri}")
        return self._driver

    def close(self):
        """Close database connection"""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def verify_connectivity(self) -> bool:
        """
        Verify database connectivity

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 AS test")
                return result.single()["test"] == 1
        except Exception as e:
            logger.error(f"Connectivity check failed: {e}")
            return False

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results

        Args:
            query: Cypher query string
            parameters: Query parameters
            timeout: Query timeout in seconds

        Returns:
            List of result records as dictionaries
        """
        settings = get_settings()
        timeout = timeout or settings.query_timeout

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise

    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a write query in a transaction

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        try:
            with self.driver.session(database=self.database) as session:
                result = session.write_transaction(
                    lambda tx: list(tx.run(query, parameters or {}))
                )
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Write query execution failed: {e}")
            logger.error(f"Query: {query}")
            raise

    def get_schema(self) -> Dict[str, Any]:
        """
        Retrieve database schema information

        Returns:
            Dictionary containing node labels, relationship types, and constraints
        """
        schema = {
            "node_labels": [],
            "relationship_types": [],
            "constraints": [],
            "indexes": [],
        }

        try:
            # Get node labels
            result = self.execute_query("CALL db.labels()")
            schema["node_labels"] = [record["label"] for record in result]

            # Get relationship types
            result = self.execute_query("CALL db.relationshipTypes()")
            schema["relationship_types"] = [
                record["relationshipType"] for record in result
            ]

            # Get constraints
            result = self.execute_query("SHOW CONSTRAINTS")
            schema["constraints"] = result

            # Get indexes
            result = self.execute_query("SHOW INDEXES")
            schema["indexes"] = result

        except Exception as e:
            logger.error(f"Failed to retrieve schema: {e}")

        return schema

    def get_node_count(self, label: Optional[str] = None) -> int:
        """
        Get count of nodes, optionally filtered by label

        Args:
            label: Node label to filter by (optional)

        Returns:
            Count of nodes
        """
        if label:
            query = f"MATCH (n:{label}) RETURN count(n) AS count"
        else:
            query = "MATCH (n) RETURN count(n) AS count"

        result = self.execute_query(query)
        return result[0]["count"] if result else 0

    def get_relationship_count(self, rel_type: Optional[str] = None) -> int:
        """
        Get count of relationships, optionally filtered by type

        Args:
            rel_type: Relationship type to filter by (optional)

        Returns:
            Count of relationships
        """
        if rel_type:
            query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count"
        else:
            query = "MATCH ()-[r]->() RETURN count(r) AS count"

        result = self.execute_query(query)
        return result[0]["count"] if result else 0

    def validate_cypher_syntax(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Validate Cypher query syntax without executing

        Args:
            query: Cypher query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Use EXPLAIN to validate syntax without executing
            explain_query = f"EXPLAIN {query}"
            with self.driver.session(database=self.database) as session:
                session.run(explain_query)
            return True, None
        except Exception as e:
            return False, str(e)

    def find_node_by_name(
        self, label: str, name: str, name_property: str = "name"
    ) -> Optional[Dict[str, Any]]:
        """
        Find a node by its name/label

        Args:
            label: Node label
            name: Name to search for
            name_property: Property to search in (default: "name")

        Returns:
            Node data or None if not found
        """
        query = f"""
        MATCH (n:{label})
        WHERE toLower(n.{name_property}) = toLower($name)
        OR any(syn IN n.synonyms WHERE toLower(syn) = toLower($name))
        RETURN n
        LIMIT 1
        """
        result = self.execute_query(query, {"name": name})
        return result[0]["n"] if result else None

    def get_sample_data(self, limit: int = 10) -> Dict[str, List[Dict]]:
        """
        Get sample data from the database

        Args:
            limit: Number of samples per type

        Returns:
            Dictionary with sample nodes and relationships
        """
        samples = {"nodes": [], "relationships": []}

        try:
            # Sample nodes
            node_query = f"MATCH (n) RETURN n LIMIT {limit}"
            samples["nodes"] = self.execute_query(node_query)

            # Sample relationships
            rel_query = f"""
            MATCH (a)-[r]->(b)
            RETURN a, r, b
            LIMIT {limit}
            """
            samples["relationships"] = self.execute_query(rel_query)

        except Exception as e:
            logger.error(f"Failed to get sample data: {e}")

        return samples


# Singleton instance
_connector = None


def get_neo4j_connector() -> Neo4jConnector:
    """Get or create global Neo4j connector instance"""
    global _connector
    if _connector is None:
        _connector = Neo4jConnector()
    return _connector


def close_connector():
    """Close global connector instance"""
    global _connector
    if _connector is not None:
        _connector.close()
        _connector = None
