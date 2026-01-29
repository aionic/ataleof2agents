#!/usr/bin/env python3
"""
Test script for Azure AI Foundry agent.
Tests the WeatherClothingAdvisor agent via API calls.

Updated for azure-ai-projects SDK v2.0.0+ (GA API with conversations).
"""

import os
import sys
import time
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FoundryAgentTester:
    """Test Azure AI Foundry agent via API."""

    def __init__(self):
        """Initialize Foundry client."""
        load_dotenv()

        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        if not self.project_endpoint:
            raise ValueError("AZURE_AI_PROJECT_ENDPOINT environment variable is required")

        credential = DefaultAzureCredential()
        self.client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=credential
        )

        logger.info(f"Initialized Foundry client for project: {self.project_endpoint}")

    def test_agent(self, agent_name: str, test_message: str = "What should I wear in 10001?") -> Dict[str, Any]:
        """
        Test agent with a message using the new conversations API.

        Args:
            agent_name: Name of the agent to test
            test_message: Message to send to the agent

        Returns:
            Test results dictionary
        """
        logger.info(f"Testing agent: {agent_name}")
        logger.info(f"Test message: {test_message}")

        start_time = time.time()
        conversation_id = None

        try:
            # Get OpenAI client for conversations
            openai_client = self.client.get_openai_client()

            # Create conversation with initial message
            logger.info("Creating conversation with initial user message...")
            conversation = openai_client.conversations.create(
                items=[{'type': 'message', 'role': 'user', 'content': test_message}],
            )
            conversation_id = conversation.id
            logger.info(f"Created conversation: {conversation_id}")

            # Invoke the agent using agent_reference
            logger.info(f"Invoking agent '{agent_name}' via responses API...")
            response = openai_client.responses.create(
                conversation=conversation_id,
                extra_body={'agent': {'name': agent_name, 'type': 'agent_reference'}},
                input='',
            )

            # Get the response text
            response_text = response.output_text
            logger.info(f"Response received: {len(response_text)} characters")

            if not response_text:
                raise RuntimeError("No assistant response found")

            end_time = time.time()
            duration = end_time - start_time

            # Clean up conversation
            logger.info("Cleaning up conversation...")
            try:
                openai_client.conversations.delete(conversation_id=conversation_id)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup conversation: {cleanup_error}")

            result = {
                "success": True,
                "agent_name": agent_name,
                "conversation_id": conversation_id,
                "test_message": test_message,
                "response": response_text,
                "duration_seconds": round(duration, 2),
                "status": "completed"
            }

            logger.info(f"Test completed successfully in {duration:.2f}s")
            return result

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            # Try to clean up conversation on error
            if conversation_id:
                try:
                    openai_client = self.client.get_openai_client()
                    openai_client.conversations.delete(conversation_id=conversation_id)
                except Exception:
                    pass

            logger.exception("Test failed")
            return {
                "success": False,
                "agent_name": agent_name,
                "test_message": test_message,
                "error": str(e),
                "duration_seconds": round(duration, 2),
                "status": "failed"
            }


def main():
    """Main entry point for agent testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Weather Clothing Advisor agent in Azure AI Foundry")
    parser.add_argument("agent_name", help="Agent name to test (e.g., WeatherClothingAdvisor)")
    parser.add_argument("--message", default="What should I wear in 10001?",
                       help="Test message to send to agent")

    args = parser.parse_args()

    try:
        tester = FoundryAgentTester()
        result = tester.test_agent(args.agent_name, args.message)

        print("\n" + "="*80)
        print("FOUNDRY AGENT TEST RESULTS")
        print("="*80)
        print(f"Agent Name: {result['agent_name']}")
        print(f"Test Message: {result['test_message']}")
        print(f"Duration: {result['duration_seconds']}s")
        print(f"Status: {result['status']}")
        print("-"*80)

        if result['success']:
            print("\n✓ TEST PASSED\n")
            print("Agent Response:")
            print("-"*80)
            print(result['response'])
            print("-"*80)

            # Check success criteria
            print("\nSuccess Criteria:")
            print(f"  ✓ Response received")
            print(f"  {'✓' if result['duration_seconds'] < 10 else '✗'} Response time < 10s (SC-001): {result['duration_seconds']}s")
            print(f"  {'✓' if 'wear' in result['response'].lower() or 'clothing' in result['response'].lower() else '✗'} Clothing recommendation format (SC-002)")

            sys.exit(0)
        else:
            print("\n✗ TEST FAILED\n")
            print(f"Error: {result['error']}")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
