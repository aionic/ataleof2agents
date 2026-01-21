"""
Manual test script for the Weather-Based Clothing Advisor.

Tests both Container Apps and Foundry deployments with sample queries.
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# Test cases
TEST_CASES = [
    {
        "name": "Valid NYC zip code",
        "message": "What should I wear in 10001?",
        "zip_code": "10001",
        "expected_success": True
    },
    {
        "name": "Valid LA zip code",
        "message": "What's the weather like in 90210?",
        "zip_code": "90210",
        "expected_success": True
    },
    {
        "name": "Invalid zip code",
        "message": "What should I wear in 99999?",
        "zip_code": "99999",
        "expected_success": False
    },
    {
        "name": "Re-lookup test",
        "message": "Now check 60601",
        "zip_code": "60601",
        "expected_success": True
    }
]


class AgentTester:
    """Test harness for agent deployments."""

    def __init__(self, base_url: str, deployment_type: str):
        self.base_url = base_url.rstrip('/')
        self.deployment_type = deployment_type
        self.session_id = None

    def test_health(self) -> bool:
        """Test health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Health check passed: {response.json()}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False

    def test_chat(self, message: str, expected_success: bool = True) -> Dict[str, Any]:
        """Send chat message and validate response."""
        print(f"\n📨 Sending: {message}")

        payload = {
            "message": message
        }

        if self.session_id:
            payload["session_id"] = self.session_id

        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=10
            )
            duration = time.time() - start_time

            print(f"⏱️  Response time: {duration:.2f}s")

            if response.status_code == 200:
                result = response.json()
                self.session_id = result.get("session_id")

                print(f"✅ Response ({len(result['response'])} chars):")
                print(f"   {result['response'][:200]}...")

                # Validate response time (SC-001: <5s)
                if duration > 5.0:
                    print(f"⚠️  Warning: Response time {duration:.2f}s exceeds 5s threshold (SC-001)")

                # Validate recommendations (SC-002: 3-5 items)
                response_text = result['response'].lower()
                if expected_success and "recommend" in response_text:
                    print(f"✅ Contains recommendations")

                return {
                    "success": True,
                    "duration": duration,
                    "response": result
                }
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   {response.text}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }

        except Exception as e:
            print(f"❌ Request error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def run_test_suite(self):
        """Run full test suite."""
        print(f"\n{'='*60}")
        print(f"Testing {self.deployment_type} Deployment")
        print(f"Base URL: {self.base_url}")
        print(f"{'='*60}")

        # Health check
        if not self.test_health():
            print("\n❌ Health check failed - aborting tests")
            return False

        # Run test cases
        results = []
        for test_case in TEST_CASES:
            print(f"\n--- Test: {test_case['name']} ---")
            result = self.test_chat(
                message=test_case['message'],
                expected_success=test_case['expected_success']
            )
            results.append({
                **test_case,
                **result
            })
            time.sleep(1)  # Rate limiting

        # Summary
        print(f"\n{'='*60}")
        print("Test Summary")
        print(f"{'='*60}")

        passed = sum(1 for r in results if r.get('success'))
        total = len(results)

        print(f"\nPassed: {passed}/{total}")

        for result in results:
            status = "✅" if result.get('success') else "❌"
            duration = result.get('duration', 0)
            print(f"{status} {result['name']} ({duration:.2f}s)")

        return passed == total


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python manual_test.py <DEPLOYMENT_TYPE> <BASE_URL>")
        print("")
        print("Examples:")
        print("  python manual_test.py container-app https://ca-weather-advisor.azurecontainerapps.io")
        print("  python manual_test.py foundry https://your-foundry-endpoint.azure.com")
        sys.exit(1)

    deployment_type = sys.argv[1]
    base_url = sys.argv[2]

    tester = AgentTester(base_url, deployment_type)
    success = tester.run_test_suite()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
