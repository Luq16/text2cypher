"""
Intent classifier for routing queries to appropriate handlers
"""
from typing import Optional, List, Tuple
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import logging

from config import get_settings, QueryIntent
from src.prompts import SystemPrompts
from src.templates import get_all_template_libraries

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Classifies user queries into intent categories"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize intent classifier

        Args:
            llm: Language model to use (defaults to configured model)
        """
        settings = get_settings()

        if llm is None:
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0.0,  # Deterministic for classification
                openai_api_key=settings.openai_api_key,
            )
        else:
            self.llm = llm

        self.template_libraries = get_all_template_libraries()

    def classify(self, query: str) -> str:
        """
        Classify query into an intent category

        Args:
            query: User's natural language query

        Returns:
            Intent category name
        """
        try:
            # Use LLM to classify intent
            messages = [
                SystemMessage(content=SystemPrompts.get_intent_classification_prompt()),
                HumanMessage(content=query),
            ]

            response = self.llm.invoke(messages)
            intent = response.content.strip().lower()

            # Validate intent
            valid_intents = [
                QueryIntent.DRUG_REPURPOSING,
                QueryIntent.TARGET_IDENTIFICATION,
                QueryIntent.INDICATION_EXPANSION,
                QueryIntent.PATHWAY_ANALYSIS,
                QueryIntent.DISEASE_DRUG_RELATION,
                QueryIntent.BIOMARKER_DISCOVERY,
                QueryIntent.DRUG_TARGET_INTERACTION,
                QueryIntent.GENE_DISEASE_ASSOCIATION,
                QueryIntent.COMPOUND_SIMILARITY,
                QueryIntent.GENERAL_QUERY,
            ]

            if intent in valid_intents:
                logger.info(f"Classified query intent: {intent}")
                return intent
            else:
                logger.warning(f"Unknown intent '{intent}', defaulting to general_query")
                return QueryIntent.GENERAL_QUERY

        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return QueryIntent.GENERAL_QUERY

    def find_matching_templates(
        self, query: str, intent: Optional[str] = None
    ) -> List:
        """
        Find templates that match the query

        Args:
            query: User's natural language query
            intent: Optional pre-classified intent

        Returns:
            List of matching QueryTemplate objects
        """
        if intent is None:
            intent = self.classify(query)

        matching_templates = []

        for library in self.template_libraries:
            matches = library.find_matching_templates(query, intent)
            matching_templates.extend(matches)

        logger.info(f"Found {len(matching_templates)} matching templates for query")
        return matching_templates

    def classify_with_confidence(
        self, query: str
    ) -> Tuple[str, List[Tuple[str, float]]]:
        """
        Classify query and return intent with confidence scores

        Args:
            query: User's natural language query

        Returns:
            Tuple of (primary_intent, [(intent, confidence_score)])
        """
        # For now, use keyword-based confidence scoring
        # In production, could use a more sophisticated classifier

        intent = self.classify(query)

        # Simple keyword matching for confidence
        confidence_scores = []
        query_lower = query.lower()

        keyword_map = {
            QueryIntent.DRUG_REPURPOSING: [
                "repurpose",
                "repurposing",
                "similar drugs",
                "alternative use",
            ],
            QueryIntent.TARGET_IDENTIFICATION: [
                "target",
                "gene",
                "protein",
                "identify",
            ],
            QueryIntent.INDICATION_EXPANSION: [
                "new indication",
                "expand",
                "new use",
                "additional indication",
            ],
            QueryIntent.PATHWAY_ANALYSIS: ["pathway", "signaling", "mechanism"],
            QueryIntent.DISEASE_DRUG_RELATION: ["treat", "treatment", "therapy"],
            QueryIntent.BIOMARKER_DISCOVERY: ["biomarker", "marker", "diagnostic"],
            QueryIntent.DRUG_TARGET_INTERACTION: [
                "target",
                "interact",
                "bind",
                "inhibit",
            ],
            QueryIntent.GENE_DISEASE_ASSOCIATION: [
                "associated with",
                "cause",
                "linked to",
            ],
            QueryIntent.COMPOUND_SIMILARITY: [
                "similar compound",
                "similar to",
                "chemical similarity",
            ],
        }

        for intent_type, keywords in keyword_map.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            if matches > 0:
                confidence = min(matches / len(keywords), 1.0)
                confidence_scores.append((intent_type, confidence))

        # Sort by confidence
        confidence_scores.sort(key=lambda x: x[1], reverse=True)

        return intent, confidence_scores

    def should_use_template(self, query: str, intent: str) -> bool:
        """
        Determine if query should use predefined template or text2cypher

        Args:
            query: User's natural language query
            intent: Classified intent

        Returns:
            True if should use template, False for text2cypher
        """
        # Use template if we have matching templates and it's not a general query
        if intent == QueryIntent.GENERAL_QUERY:
            return False

        matching_templates = self.find_matching_templates(query, intent)
        return len(matching_templates) > 0


# Singleton instance
_classifier = None


def get_intent_classifier() -> IntentClassifier:
    """Get or create global intent classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier
