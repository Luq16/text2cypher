"""
Main entry point for QIAGEN BKB Text2Cypher Agent
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from config import get_settings
from src.agents import get_query_router
from src.utils import get_result_synthesizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BKBQueryAgent:
    """Main interface for QIAGEN BKB Text2Cypher Agent"""

    def __init__(self):
        """Initialize the agent"""
        self.router = get_query_router()
        self.synthesizer = get_result_synthesizer()
        logger.info("BKB Text2Cypher Agent initialized")

    def query(
        self,
        question: str,
        format: str = "natural",
        force_text2cypher: bool = False,
    ) -> dict:
        """
        Execute a natural language query

        Args:
            question: Natural language question
            format: Output format ('natural', 'json', 'table')
            force_text2cypher: Force use of text2cypher instead of templates

        Returns:
            Query result dictionary
        """
        # Execute query
        result = self.router.query(question, force_text2cypher=force_text2cypher)

        # Format output based on preference
        if format == "json":
            return result
        elif format == "table" and result.get("success"):
            table = self.synthesizer.format_tabular(result.get("results", []))
            result["formatted_results"] = table
            return result
        else:  # natural language
            return result

    def batch_query(self, questions: list[str]) -> list[dict]:
        """
        Execute multiple queries in batch

        Args:
            questions: List of questions

        Returns:
            List of results
        """
        return self.router.batch_query(questions)

    def get_suggestions(self, question: str) -> list[dict]:
        """
        Get template suggestions for a question

        Args:
            question: Natural language question

        Returns:
            List of suggested templates
        """
        return self.router.get_template_suggestions(question)


def interactive_mode():
    """Run in interactive CLI mode"""
    print("=" * 60)
    print("QIAGEN BKB Text2Cypher Agent - Interactive Mode")
    print("=" * 60)
    print("\nCommands:")
    print("  - Type your question to query the database")
    print("  - 'suggest <question>' to get template suggestions")
    print("  - 'format <natural|json|table>' to change output format")
    print("  - 'force-text2cypher on|off' to toggle text2cypher")
    print("  - 'help' for this message")
    print("  - 'exit' or 'quit' to exit")
    print("=" * 60)

    agent = BKBQueryAgent()
    output_format = "natural"
    force_text2cypher = False

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye!")
                break

            elif user_input.lower() == "help":
                print("\nCommands:")
                print("  - Type your question to query the database")
                print("  - 'suggest <question>' to get template suggestions")
                print("  - 'format <natural|json|table>' to change output format")
                print("  - 'force-text2cypher on|off' to toggle text2cypher")
                print("  - 'exit' or 'quit' to exit")
                continue

            elif user_input.lower().startswith("format "):
                new_format = user_input.split("format ", 1)[1].strip().lower()
                if new_format in ["natural", "json", "table"]:
                    output_format = new_format
                    print(f"Output format set to: {output_format}")
                else:
                    print(
                        "Invalid format. Choose from: natural, json, table"
                    )
                continue

            elif user_input.lower().startswith("force-text2cypher "):
                toggle = user_input.split("force-text2cypher ", 1)[1].strip().lower()
                if toggle == "on":
                    force_text2cypher = True
                    print("Text2Cypher forced: ON")
                elif toggle == "off":
                    force_text2cypher = False
                    print("Text2Cypher forced: OFF")
                else:
                    print("Use 'force-text2cypher on' or 'force-text2cypher off'")
                continue

            elif user_input.lower().startswith("suggest "):
                question = user_input.split("suggest ", 1)[1].strip()
                suggestions = agent.get_suggestions(question)

                if suggestions:
                    print(f"\nFound {len(suggestions)} template suggestion(s):")
                    for i, sug in enumerate(suggestions, 1):
                        print(f"\n{i}. {sug['name']}")
                        print(f"   Description: {sug['description']}")
                        print(f"   Example: {sug['example_question']}")
                else:
                    print("\nNo matching templates found. Will use text2cypher.")
                continue

            # Execute query
            print("\nProcessing query...")
            result = agent.query(
                user_input, format=output_format, force_text2cypher=force_text2cypher
            )

            # Display results
            if result.get("success"):
                print(f"\n✓ Query successful!")
                print(f"  Query Type: {result.get('query_type', 'unknown')}")
                print(f"  Intent: {result.get('intent', 'unknown')}")
                print(f"  Results: {result.get('result_count', 0)}")

                if output_format == "json":
                    print(f"\nCypher Query:\n{result.get('cypher_query', 'N/A')}")
                    print(f"\nResults:\n{json.dumps(result.get('results', []), indent=2)}")
                elif output_format == "table":
                    print(f"\n{result.get('formatted_results', '')}")
                else:  # natural
                    print(f"\nAnswer:\n{result.get('answer', 'No answer generated')}")

            else:
                print(f"\n✗ Query failed: {result.get('error', 'Unknown error')}")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            print(f"\nError: {e}")


def single_query_mode(question: str, output_format: str = "natural"):
    """Execute a single query and print results"""
    agent = BKBQueryAgent()
    result = agent.query(question, format=output_format)

    if output_format == "json":
        print(json.dumps(result, indent=2))
    else:
        if result.get("success"):
            print(result.get("answer", "No answer generated"))
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="QIAGEN BKB Text2Cypher Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python -m src.main

  # Single query
  python -m src.main --query "Find drugs that target EGFR"

  # JSON output
  python -m src.main --query "What genes are associated with cancer?" --format json

  # Force text2cypher
  python -m src.main --query "Complex novel query" --force-text2cypher
        """,
    )

    parser.add_argument(
        "--query", "-q", type=str, help="Execute a single query and exit"
    )
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["natural", "json", "table"],
        default="natural",
        help="Output format (default: natural)",
    )
    parser.add_argument(
        "--force-text2cypher",
        action="store_true",
        help="Force use of text2cypher instead of templates",
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run in interactive mode"
    )

    args = parser.parse_args()

    # Execute based on arguments
    if args.query:
        single_query_mode(args.query, args.format)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
