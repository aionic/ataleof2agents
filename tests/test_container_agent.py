#!/usr/bin/env python3
"""
Test Container Apps Agent Deployment

Tests the self-hosted agent running on Azure Container Apps.
Works with both legacy (agent-container) and unified (agent) packages.

Requires: Agent deployed and AGENT_URL environment variable set.
"""

import os
import requests
import time
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# Configuration
AGENT_URL = os.getenv("AGENT_URL", "https://ca-weather-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io")

# Determine which endpoint to use based on deployment mode
# Legacy mode uses /chat, unified mode can use /responses
USE_RESPONSES_API = os.getenv("USE_RESPONSES_API", "false").lower() == "true"

# Test cases
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
    {
        "name": "Invalid zip code",
        "message": "What should I wear in 00000?",
        "expected_error": True,
    },
]


def test_health_check() -> bool:
    """Test agent health endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Health Check")
    print("=" * 60)

    try:
        response = requests.get(f"{AGENT_URL}/health", timeout=10)

        if response.status_code == 200:
            print("✓ Agent is healthy")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {str(e)}")
        return False


def test_agent_response(test_case: Dict) -> Dict:
    """Test agent with a specific message."""
    print("\n" + "=" * 60)
    print(f"TEST: {test_case['name']}")
    print("=" * 60)
    print(f"Message: {test_case['message']}")

    start_time = time.time()

    try:
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": test_case["message"]},
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        duration = time.time() - start_time

        if response.status_code != 200:
            if test_case.get("expected_error"):
                print(f"✓ Error handling working (status: {response.status_code})")
                print(f"  Duration: {duration:.2f}s")
                return {"success": True, "duration": duration}
            else:
                print(f"✗ Request failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return {"success": False, "duration": duration}

        data = response.json()
        agent_response = data.get("response", "")

        print(f"\nResponse ({duration:.2f}s):")
        print(f"  {agent_response[:200]}...")

        # Check for expected keywords
        if "expected_keywords" in test_case:
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
        else:
            success = len(agent_response) > 0

        if success:
            print(f"\n✓ Test passed")
        else:
            print(f"\n✗ Test failed")

        return {
            "success": success,
            "duration": duration,
            "response": agent_response,
            "metadata": data.get("metadata", {})
        }

    except Exception as e:
        duration = time.time() - start_time
        print(f"\n✗ Test error: {str(e)}")
        print(f"  Duration: {duration:.2f}s")
        return {"success": False, "duration": duration, "error": str(e)}


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CONTAINER APPS AGENT TESTING")
    print("=" * 60)
    print(f"Agent URL: {AGENT_URL}")

    # Health check
    if not test_health_check():
        print("\n✗ Health check failed. Aborting tests.")
        return 1

    # Run test cases
    results = []
    for test_case in TEST_CASES:
        result = test_agent_response(test_case)
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
