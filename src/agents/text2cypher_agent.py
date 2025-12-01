"""
Text2Cypher agent using LangChain GraphCypherQAChain
"""
from typing import Dict, List, Optional, Any
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import logging

from config import get_settings
from src.utils import get_query_validator, get_schema_loader
from src.prompts import FewShotExamples, SystemPrompts

logger = logging.getLogger(__name__)


class Text2CypherAgent:
    """Agent for generating and executing Cypher queries from natural language"""

    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        graph: Optional[Neo4jGraph] = None,
    ):
        """
        Initialize Text2Cypher agent

        Args:
            llm: Language model to use
            graph: Neo4j graph instance
        """
        settings = get_settings()

        # Initialize LLM
        if llm is None:
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=settings.openai_temperature,
                openai_api_key=settings.openai_api_key,
            )
        else:
            self.llm = llm

        # Initialize Neo4j graph
        if graph is None:
            self.graph = Neo4jGraph(
                url=settings.neo4j_uri,
                username=settings.neo4j_username,
                password=settings.neo4j_password,
                database=settings.neo4j_database,
            )
        else:
            self.graph = graph

        self.validator = get_query_validator()
        self.schema_loader = get_schema_loader()

        # Build the cypher generation chain
        self.cypher_chain = self._build_cypher_chain()

    def _build_cypher_chain(self) -> GraphCypherQAChain:
        """
        Build the GraphCypherQAChain with custom prompts

        Returns:
            Configured GraphCypherQAChain
        """
        settings = get_settings()

        # Get schema context
        schema_context = self.schema_loader.get_cypher_schema_context()

        # Get few-shot examples
        examples = FewShotExamples.get_drug_discovery_examples()
        few_shot_prompt = FewShotExamples.format_for_prompt(
            examples, max_examples=settings.max_few_shot_examples
        )

        # Build custom cypher generation prompt
        cypher_generation_template = f"""{SystemPrompts.get_text2cypher_prompt(schema_context)}

{few_shot_prompt if settings.use_few_shot_examples else ""}

User Question: {{question}}

Generate the Cypher query:"""

        cypher_prompt = PromptTemplate(
            template=cypher_generation_template,
            input_variables=["question"],
        )

        # Create the chain
        return GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            cypher_prompt=cypher_prompt,
            verbose=True,
            validate_cypher=settings.enable_query_validation,
            return_intermediate_steps=True,
        )

    def generate_cypher(self, question: str) -> str:
        """
        Generate Cypher query from natural language question

        Args:
            question: User's natural language question

        Returns:
            Generated Cypher query
        """
        try:
            # Use the chain to generate cypher
            result = self.cypher_chain.invoke({"query": question})

            # Extract the generated cypher from intermediate steps
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if "query" in step:
                        cypher_query = step["query"]
                        logger.info(f"Generated Cypher: {cypher_query}")
                        return cypher_query

            # Fallback: try to extract from result
            logger.warning("Could not find generated Cypher in intermediate steps")
            return ""

        except Exception as e:
            logger.error(f"Cypher generation failed: {e}")
            raise

    def query(
        self, question: str, refine_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a natural language query

        Args:
            question: User's natural language question
            refine_on_error: Whether to attempt query refinement on errors

        Returns:
            Dictionary with query results and metadata
        """
        settings = get_settings()
        max_iterations = settings.max_iterations if refine_on_error else 1

        for iteration in range(max_iterations):
            try:
                logger.info(
                    f"Text2Cypher query attempt {iteration + 1}/{max_iterations}"
                )

                # Execute the chain
                result = self.cypher_chain.invoke({"query": question})

                # Extract components
                cypher_query = ""
                query_results = []

                if "intermediate_steps" in result:
                    for step in result["intermediate_steps"]:
                        if "query" in step:
                            cypher_query = step["query"]
                        if "context" in step:
                            query_results = step["context"]

                response = {
                    "success": True,
                    "question": question,
                    "cypher_query": cypher_query,
                    "results": query_results,
                    "answer": result.get("result", ""),
                    "iterations": iteration + 1,
                }

                logger.info(f"Query succeeded on iteration {iteration + 1}")
                return response

            except Exception as e:
                logger.warning(f"Query attempt {iteration + 1} failed: {e}")

                if iteration < max_iterations - 1 and refine_on_error:
                    # Attempt to refine the query
                    logger.info("Attempting query refinement...")
                    continue
                else:
                    # Return error response
                    return {
                        "success": False,
                        "question": question,
                        "error": str(e),
                        "iterations": iteration + 1,
                    }

        return {
            "success": False,
            "question": question,
            "error": "Max iterations reached",
            "iterations": max_iterations,
        }

    def validate_and_execute(
        self, cypher_query: str
    ) -> tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Validate and execute a Cypher query

        Args:
            cypher_query: Cypher query to execute

        Returns:
            Tuple of (success, results, error_message)
        """
        # Validate query
        is_valid, errors = self.validator.validate_query(cypher_query)

        if not is_valid:
            error_msg = "; ".join(errors)
            logger.error(f"Query validation failed: {error_msg}")
            return False, None, error_msg

        # Log warnings
        warnings = [e for e in errors if e.startswith("WARNING")]
        if warnings:
            logger.warning(f"Query warnings: {'; '.join(warnings)}")

        # Execute query
        try:
            results = self.graph.query(cypher_query)
            return True, results, None
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return False, None, str(e)

    def refine_query(
        self, cypher_query: str, error_message: str
    ) -> Optional[str]:
        """
        Attempt to refine a failed query

        Args:
            cypher_query: Original Cypher query
            error_message: Error message from execution

        Returns:
            Refined query or None if refinement failed
        """
        try:
            # Use LLM to refine the query
            refinement_prompt = SystemPrompts.get_query_refinement_prompt(
                cypher_query, error_message
            )

            refined_query = self.llm.invoke(refinement_prompt).content

            logger.info(f"Refined query: {refined_query}")
            return refined_query

        except Exception as e:
            logger.error(f"Query refinement failed: {e}")
            return None

    def get_schema_info(self) -> str:
        """Get formatted schema information"""
        return self.schema_loader.get_detailed_schema()


# Singleton instance
_text2cypher_agent = None


def get_text2cypher_agent() -> Text2CypherAgent:
    """Get or create global text2cypher agent instance"""
    global _text2cypher_agent
    if _text2cypher_agent is None:
        _text2cypher_agent = Text2CypherAgent()
    return _text2cypher_agent
