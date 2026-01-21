#!/usr/bin/env python3
"""
Test script for Azure AI Foundry agent.
Tests the WeatherClothingAdvisor agent via API calls.
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

    def test_agent(self, agent_id: str, test_message: str = "What should I wear in 10001?") -> Dict[str, Any]:
        """
        Test agent with a message.

        Args:
            agent_id: ID of the agent to test
            test_message: Message to send to the agent

        Returns:
            Test results dictionary
        """
        logger.info(f"Testing agent: {agent_id}")
        logger.info(f"Test message: {test_message}")

        start_time = time.time()

        try:
            # Create thread
            logger.info("Creating conversation thread...")
            thread = self.client.agents.threads.create()
            thread_id = thread.id
            logger.info(f"Created thread: {thread_id}")

            # Send message
            logger.info("Sending user message...")
            message = self.client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=test_message
            )
            logger.info(f"Created message: {message.id}")

            # Create and process run (this handles polling automatically)
            logger.info("Starting agent run and processing...")
            run = self.client.agents.runs.create_and_process(
                thread_id=thread_id,
                agent_id=agent_id
            )
            run_id = run.id
            logger.info(f"Run completed with status: {run.status}")

            # Check if run failed
            if run.status == "failed":
                raise RuntimeError(f"Run failed: {run.last_error}")

            # Get response messages
            logger.info("Retrieving response...")
            messages = self.client.agents.messages.list(thread_id=thread_id)

            # Extract assistant's response
            response_text = ""
            for message in messages:
                if message.role == "assistant" and hasattr(message, 'text_messages') and message.text_messages:
                    response_text = message.text_messages[-1].text.value
                    break

            if not response_text:
                raise RuntimeError("No assistant response found")

            end_time = time.time()
            duration = end_time - start_time

            # Clean up
            logger.info("Cleaning up thread...")
            self.client.agents.threads.delete(thread_id)

            result = {
                "success": True,
                "agent_id": agent_id,
                "thread_id": thread_id,
                "run_id": run_id,
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

            logger.exception("Test failed")
            return {
                "success": False,
                "agent_id": agent_id,
                "test_message": test_message,
                "error": str(e),
                "duration_seconds": round(duration, 2),
                "status": "failed"
            }


def main():
    """Main entry point for agent testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Weather Clothing Advisor agent in Azure AI Foundry")
    parser.add_argument("agent_id", help="Agent ID to test")
    parser.add_argument("--message", default="What should I wear in 10001?",
                       help="Test message to send to agent")

    args = parser.parse_args()

    try:
        tester = FoundryAgentTester()
        result = tester.test_agent(args.agent_id, args.message)

        print("\n" + "="*80)
        print("FOUNDRY AGENT TEST RESULTS")
        print("="*80)
        print(f"Agent ID: {result['agent_id']}")
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
            print(f"  {'✓' if result['duration_seconds'] < 5 else '✗'} Response time < 5s (SC-001): {result['duration_seconds']}s")
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
