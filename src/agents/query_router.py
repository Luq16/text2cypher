"""
Main query router agent that orchestrates between predefined templates and text2cypher
"""
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
import logging
import json

from config import get_settings
from src.agents.intent_classifier import get_intent_classifier
from src.agents.text2cypher_agent import get_text2cypher_agent
from src.templates import get_all_template_libraries, ParameterExtractor
from src.utils import (
    get_neo4j_connector,
    get_result_synthesizer,
    get_query_validator,
)

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Main router that decides between predefined templates and text2cypher
    Implements the hybrid approach recommended by experts
    """

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize query router

        Args:
            llm: Language model to use
        """
        settings = get_settings()

        if llm is None:
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=settings.openai_temperature,
                openai_api_key=settings.openai_api_key,
            )
        else:
            self.llm = llm

        # Initialize components
        self.intent_classifier = get_intent_classifier()
        self.text2cypher_agent = get_text2cypher_agent()
        self.neo4j = get_neo4j_connector()
        self.synthesizer = get_result_synthesizer()
        self.validator = get_query_validator()
        self.template_libraries = get_all_template_libraries()
        self.param_extractor = ParameterExtractor()

    def query(self, question: str, force_text2cypher: bool = False) -> Dict[str, Any]:
        """
        Process a natural language query

        Args:
            question: User's natural language question
            force_text2cypher: Force use of text2cypher instead of templates

        Returns:
            Query response with results and metadata
        """
        logger.info(f"Processing query: {question}")

        # Step 1: Classify intent
        intent = self.intent_classifier.classify(question)
        logger.info(f"Classified intent: {intent}")

        # Step 2: Decide routing strategy
        if force_text2cypher:
            logger.info("Forcing text2cypher route")
            return self._execute_text2cypher(question, intent)

        # Try predefined templates first
        matching_templates = self.intent_classifier.find_matching_templates(
            question, intent
        )

        if matching_templates:
            logger.info(
                f"Found {len(matching_templates)} matching template(s), attempting template-based query"
            )
            # Try the best matching template
            template_result = self._execute_template(question, matching_templates[0])

            if template_result["success"]:
                return template_result
            else:
                logger.warning(
                    "Template execution failed, falling back to text2cypher"
                )

        # Fallback to text2cypher
        logger.info("Using text2cypher fallback")
        return self._execute_text2cypher(question, intent)

    def _execute_template(
        self, question: str, template
    ) -> Dict[str, Any]:
        """
        Execute a predefined query template

        Args:
            question: User's question
            template: QueryTemplate to execute

        Returns:
            Query response
        """
        try:
            logger.info(f"Executing template: {template.name}")

            # Extract parameters from question using LLM
            parameters = self._extract_template_parameters(
                question, template.parameters
            )

            if not parameters:
                logger.warning("Failed to extract template parameters")
                return {"success": False, "error": "Parameter extraction failed"}

            # Format the template with parameters
            cypher_query = template.format(**parameters)
            logger.info(f"Template Cypher: {cypher_query}")

            # Validate query
            is_valid, validation_errors = self.validator.validate_query(cypher_query)
            if not is_valid:
                error_msg = "; ".join(validation_errors)
                logger.error(f"Template query validation failed: {error_msg}")
                return {"success": False, "error": error_msg}

            # Execute query
            results = self.neo4j.execute_query(cypher_query, parameters)

            # Synthesize response
            natural_response = self.synthesizer.synthesize(
                question, cypher_query, results
            )

            return {
                "success": True,
                "question": question,
                "intent": template.intent,
                "query_type": "template",
                "template_name": template.name,
                "cypher_query": cypher_query,
                "parameters": parameters,
                "results": results,
                "result_count": len(results),
                "answer": natural_response,
            }

        except Exception as e:
            logger.error(f"Template execution failed: {e}")
            return {"success": False, "error": str(e), "query_type": "template"}

    def _execute_text2cypher(
        self, question: str, intent: str
    ) -> Dict[str, Any]:
        """
        Execute query using text2cypher

        Args:
            question: User's question
            intent: Classified intent

        Returns:
            Query response
        """
        try:
            logger.info("Executing text2cypher query")

            # Use text2cypher agent
            result = self.text2cypher_agent.query(question, refine_on_error=True)

            if result["success"]:
                # Add intent and query type
                result["intent"] = intent
                result["query_type"] = "text2cypher"
                result["result_count"] = len(result.get("results", []))

            return result

        except Exception as e:
            logger.error(f"Text2cypher execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query_type": "text2cypher",
                "question": question,
            }

    def _extract_template_parameters(
        self, question: str, template_params: Dict[str, type]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract parameters for a template using LLM

        Args:
            question: User's question
            template_params: Required parameters and their types

        Returns:
            Dictionary of extracted parameters or None if failed
        """
        try:
            from src.prompts import SystemPrompts

            # Build extraction prompt
            prompt = SystemPrompts.get_parameter_extraction_prompt(
                question, template_params
            )

            # Get LLM response
            response = self.llm.invoke(prompt).content.strip()

            # Parse JSON response
            # Clean up markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            parameters = json.loads(response)

            # Set defaults for common parameters
            if "limit" not in parameters and "limit" in template_params:
                parameters["limit"] = self.param_extractor.extract_limit(question)

            logger.info(f"Extracted parameters: {parameters}")
            return parameters

        except Exception as e:
            logger.error(f"Parameter extraction failed: {e}")
            return None

    def batch_query(self, questions: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple questions in batch

        Args:
            questions: List of questions to process

        Returns:
            List of query responses
        """
        results = []
        for i, question in enumerate(questions, 1):
            logger.info(f"Processing batch query {i}/{len(questions)}")
            result = self.query(question)
            results.append(result)

        return results

    def get_template_suggestions(self, question: str) -> List[Dict[str, str]]:
        """
        Get template suggestions for a question without executing

        Args:
            question: User's question

        Returns:
            List of suggested templates with descriptions
        """
        intent = self.intent_classifier.classify(question)
        matching_templates = self.intent_classifier.find_matching_templates(
            question, intent
        )

        suggestions = []
        for template in matching_templates:
            suggestions.append(
                {
                    "name": template.name,
                    "description": template.description,
                    "intent": template.intent,
                    "example_question": template.example_question,
                }
            )

        return suggestions


# Singleton instance
_router = None


def get_query_router() -> QueryRouter:
    """Get or create global query router instance"""
    global _router
    if _router is None:
        _router = QueryRouter()
    return _router
