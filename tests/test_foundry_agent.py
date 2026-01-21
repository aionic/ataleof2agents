#!/usr/bin/env python3
"""
Test Foundry Native Agent Deployment

Tests the agent running in Azure AI Foundry managed runtime.
Requires: AI_PROJECT_CONNECTION_STRING and FOUNDRY_AGENT_ID environment variables.
"""

import os
import time
from typing import Dict, List
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

# Configuration
PROJECT_ENDPOINT = os.getenv("AI_PROJECT_CONNECTION_STRING") or os.getenv("AZURE_AI_PROJECT_ENDPOINT")
AGENT_ID = os.getenv("FOUNDRY_AGENT_ID", "asst_52uP9hfMXCf2bKDIuSTBzZdz")

# Test cases (same as Container Apps for comparison)
TEST_CASES = [
    {
        "name": "Cold weather (NYC)",
        "message": "What should I wear in 10001?",
        "expected_keywords": ["coat", "warm", "layer"],
    },
    {
        "name": "Warm weather (LA)",
        "message": "What should I wear in 90210?",
        "expected_keywords": ["light", "short"],
    },
    {
        "name": "Rainy weather (Seattle)",
        "message": "What to wear in Seattle 98101?",
        "expected_keywords": ["umbrella", "waterproof", "rain"],
    },
]


def test_foundry_connection() -> bool:
    """Test connection to Foundry project."""
    print("\n" + "=" * 60)
    print("TEST: Foundry Connection")
    print("=" * 60)

    try:
        client = AIProjectClient(
            endpoint=PROJECT_ENDPOINT,
            credential=DefaultAzureCredential()
        )

        # Try to list agents to verify connection
        agents = client.agents.list_agents()
        agent_list = list(agents)
        print(f"✓ Connected to Foundry")
        print(f"  Available agents: {len(agent_list)}")
        return True

    except Exception as e:
        print(f"✗ Connection failed: {str(e)}")
        return False


def test_agent_exists(client: AIProjectClient) -> bool:
    """Verify agent exists."""
    print("\n" + "=" * 60)
    print("TEST: Agent Exists")
    print("=" * 60)
    print(f"Agent ID: {AGENT_ID}")

    try:
        agent = client.agents.get_agent(AGENT_ID)
        print(f"✓ Agent found: {agent.name}")
        print(f"  Model: {agent.model}")
        print(f"  Tools: {len(agent.tools)}")
        return True
    except Exception as e:
        print(f"✗ Agent not found: {str(e)}")
        return False


def test_agent_response(client: AIProjectClient, test_case: Dict) -> Dict:
    """Test agent with a specific message."""
    print("\n" + "=" * 60)
    print(f"TEST: {test_case['name']}")
    print("=" * 60)
    print(f"Message: {test_case['message']}")

    start_time = time.time()
    thread_id = None

    try:
        # Create thread
        thread = client.agents.threads.create()
        thread_id = thread.id

        # Send message
        message = client.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=test_case["message"]
        )

        # Run agent
        run = client.agents.runs.create_and_process(
            thread_id=thread_id,
            agent_id=AGENT_ID
        )

        duration = time.time() - start_time

        # Get response
        messages = client.agents.messages.list(thread_id=thread_id)
        message_list = list(messages)
        latest_message = message_list[0]
        agent_response = latest_message.content[0].text.value

        print(f"\nResponse ({duration:.2f}s):")
        print(f"  {agent_response[:200]}...")

        # Check for expected keywords
        found_keywords = []
        missing_keywords = []

        for keyword in test_case["expected_keywords"]:
            if keyword.lower() in agent_response.lower():
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)

        if found_keywords:
            print(f"\n✓ Found keywords: {', '.join(found_keywords)}")
        if missing_keywords:
            print(f"  Missing keywords: {', '.join(missing_keywords)}")

        success = len(found_keywords) >= len(test_case["expected_keywords"]) // 2

        if success:
            print(f"\n✓ Test passed")
        else:
            print(f"\n✗ Test failed")

        return {
            "success": success,
            "duration": duration,
            "response": agent_response
        }

    except Exception as e:
        duration = time.time() - start_time
        print(f"\n✗ Test error: {str(e)}")
        print(f"  Duration: {duration:.2f}s")
        return {"success": False, "duration": duration, "error": str(e)}

    finally:
        # Cleanup thread
        if thread_id:
            try:
                client.agents.threads.delete(thread_id=thread_id)
            except:
                pass


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FOUNDRY AGENT TESTING")
    print("=" * 60)

    if not PROJECT_ENDPOINT:
        print("✗ AI_PROJECT_CONNECTION_STRING or AZURE_AI_PROJECT_ENDPOINT not set")
        print("  Set environment variable with your Foundry project endpoint")
        return 1

    # Test connection
    if not test_foundry_connection():
        print("\\n✗ Connection test failed. Aborting.")
        return 1

    # Create client
    client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential()
    )

    # Verify agent exists
    if not test_agent_exists(client):
        print("\n✗ Agent verification failed. Aborting.")
        return 1

    # Run test cases
    results = []
    for test_case in TEST_CASES:
        result = test_agent_response(client, test_case)
        results.append({
            "name": test_case["name"],
            **result
        })
        time.sleep(1)  # Brief pause between tests

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r["success"])
    total = len(results)
    avg_duration = sum(r["duration"] for r in results) / total

    print(f"\nResults: {passed}/{total} passed ({passed/total*100:.0f}%)")
    print(f"Average duration: {avg_duration:.2f}s")

    print("\nDetailed Results:")
    for result in results:
        status = "✓" if result["success"] else "✗"
        print(f"  {status} {result['name']:<30} {result['duration']:>6.2f}s")

    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
