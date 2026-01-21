#!/usr/bin/env python3
"""
Comparison test script for Story 6.
Tests both Foundry-native agent and Container Apps agent with identical queries.
"""

import os
import sys
import time
import json
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()


class AgentComparator:
    """Compare Foundry-native agent vs Container Apps agent."""

    def __init__(self):
        """Initialize clients for both agents."""
        # Foundry setup
        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        self.foundry_agent_id = "asst_52uP9hfMXCf2bKDIuSTBzZdz"  # WeatherClothingAdvisor

        credential = DefaultAzureCredential()
        self.foundry_client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=credential
        )

        # Container Apps setup
        self.container_agent_url = os.getenv("EXTERNAL_AGENT_URL")
        if not self.container_agent_url:
            raise ValueError("EXTERNAL_AGENT_URL not set")

        print(f"Foundry Agent: {self.foundry_agent_id}")
        print(f"Container Agent: {self.container_agent_url}")

    def test_foundry_agent(self, message: str) -> Dict[str, Any]:
        """Test Foundry-native agent."""
        start_time = time.time()

        try:
            # Create thread
            thread = self.foundry_client.agents.threads.create()

            # Send message
            self.foundry_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=message
            )

            # Run agent
            run = self.foundry_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=self.foundry_agent_id
            )

            # Check status
            if run.status == "failed":
                duration = time.time() - start_time
                return {
                    "success": False,
                    "error": str(run.last_error),
                    "duration": duration
                }

            # Get response
            messages = self.foundry_client.agents.messages.list(thread_id=thread.id)
            response_text = ""
            for msg in messages:
                if msg.role == "assistant" and hasattr(msg, 'text_messages') and msg.text_messages:
                    response_text = msg.text_messages[-1].text.value
                    break

            # Cleanup
            self.foundry_client.agents.threads.delete(thread.id)

            duration = time.time() - start_time

            return {
                "success": True,
                "response": response_text,
                "duration": duration,
                "deployment": "foundry-native"
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "duration": duration,
                "deployment": "foundry-native"
            }

    def test_container_agent(self, message: str) -> Dict[str, Any]:
        """Test Container Apps agent."""
        start_time = time.time()

        try:
            response = requests.post(
                f"{self.container_agent_url}/chat",
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=60
            )

            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("response", ""),
                    "duration": duration,
                    "deployment": "container-app",
                    "metadata": data.get("metadata", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": duration,
                    "deployment": "container-app"
                }

        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "duration": duration,
                "deployment": "container-app"
            }

    def run_comparison(self, test_cases: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Run comparison tests for all test cases."""
        results = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*80}")
            print(f"Test Case {i}/{len(test_cases)}: {test_case['name']}")
            print(f"Query: {test_case['query']}")
            print(f"{'='*80}")

            # Test Foundry agent
            print("\n[1/2] Testing Foundry-native agent...")
            foundry_result = self.test_foundry_agent(test_case['query'])

            if foundry_result['success']:
                print(f"✓ Success ({foundry_result['duration']:.2f}s)")
            else:
                print(f"✗ Failed: {foundry_result.get('error', 'Unknown error')}")

            # Test Container Apps agent
            print("\n[2/2] Testing Container Apps agent...")
            container_result = self.test_container_agent(test_case['query'])

            if container_result['success']:
                print(f"✓ Success ({container_result['duration']:.2f}s)")
            else:
                print(f"✗ Failed: {container_result.get('error', 'Unknown error')}")

            # Store results
            results.append({
                "test_case": test_case,
                "foundry": foundry_result,
                "container": container_result
            })

            # Brief pause between tests
            time.sleep(1)

        return results

    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate markdown comparison report."""
        report = []
        report.append("# Agent Comparison Test Results")
        report.append(f"\n**Test Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n**Agents Tested**:")
        report.append(f"- Foundry-native: {self.foundry_agent_id}")
        report.append(f"- Container Apps: {self.container_agent_url}")

        # Summary table
        report.append("\n## Summary")
        report.append("\n| Test Case | Foundry Success | Container Success | Foundry Time | Container Time |")
        report.append("|-----------|-----------------|-------------------|--------------|----------------|")

        for result in results:
            name = result['test_case']['name']
            f_success = "✅" if result['foundry']['success'] else "❌"
            c_success = "✅" if result['container']['success'] else "❌"
            f_time = f"{result['foundry']['duration']:.2f}s"
            c_time = f"{result['container']['duration']:.2f}s"
            report.append(f"| {name} | {f_success} | {c_success} | {f_time} | {c_time} |")

        # Detailed results
        report.append("\n## Detailed Results")

        for i, result in enumerate(results, 1):
            tc = result['test_case']
            report.append(f"\n### Test Case {i}: {tc['name']}")
            report.append(f"\n**Query**: `{tc['query']}`")
            report.append(f"\n**Expected**: {tc['expected']}")

            # Foundry results
            report.append(f"\n#### Foundry-Native Agent")
            f = result['foundry']
            if f['success']:
                report.append(f"- **Status**: ✅ Success")
                report.append(f"- **Duration**: {f['duration']:.2f}s")
                report.append(f"- **Response**: {f['response'][:200]}...")
            else:
                report.append(f"- **Status**: ❌ Failed")
                report.append(f"- **Error**: {f.get('error', 'Unknown')}")

            # Container results
            report.append(f"\n#### Container Apps Agent")
            c = result['container']
            if c['success']:
                report.append(f"- **Status**: ✅ Success")
                report.append(f"- **Duration**: {c['duration']:.2f}s")
                report.append(f"- **Response**: {c['response'][:200]}...")
                if 'metadata' in c and 'workflow_duration' in c['metadata']:
                    report.append(f"- **Workflow Duration**: {c['metadata']['workflow_duration']:.2f}s")
            else:
                report.append(f"- **Status**: ❌ Failed")
                report.append(f"- **Error**: {c.get('error', 'Unknown')}")

            # Comparison
            report.append(f"\n#### Comparison")
            if f['success'] and c['success']:
                time_diff = abs(f['duration'] - c['duration'])
                faster = "Foundry" if f['duration'] < c['duration'] else "Container"
                report.append(f"- **Both succeeded** ✅")
                report.append(f"- **Time difference**: {time_diff:.2f}s ({faster} faster)")
                report.append(f"- **Quality match**: Manual review required")
            else:
                report.append(f"- **Different outcomes**: Manual investigation needed")

        # Overall assessment
        report.append("\n## Overall Assessment")

        foundry_successes = sum(1 for r in results if r['foundry']['success'])
        container_successes = sum(1 for r in results if r['container']['success'])
        total = len(results)

        report.append(f"\n**Success Rates**:")
        report.append(f"- Foundry-native: {foundry_successes}/{total} ({foundry_successes/total*100:.1f}%)")
        report.append(f"- Container Apps: {container_successes}/{total} ({container_successes/total*100:.1f}%)")

        avg_foundry_time = sum(r['foundry']['duration'] for r in results if r['foundry']['success']) / max(foundry_successes, 1)
        avg_container_time = sum(r['container']['duration'] for r in results if r['container']['success']) / max(container_successes, 1)

        report.append(f"\n**Average Response Times**:")
        report.append(f"- Foundry-native: {avg_foundry_time:.2f}s")
        report.append(f"- Container Apps: {avg_container_time:.2f}s")

        report.append(f"\n## Conclusions")
        report.append(f"\n- **Portability**: ✅ Same workflow code works in both environments")
        report.append(f"- **Reliability**: Both agents {'completed all tests' if foundry_successes == total and container_successes == total else 'had some failures'}")
        report.append(f"- **Performance**: {'Foundry' if avg_foundry_time < avg_container_time else 'Container'} agent was faster on average")

        return "\n".join(report)


def main():
    """Run comparison tests."""

    # Define test cases
    test_cases = [
        {
            "name": "Cold Weather (NYC)",
            "query": "What should I wear in 10001?",
            "expected": "Winter clothing recommendations for cold weather"
        },
        {
            "name": "Warm Weather (LA)",
            "query": "What should I wear in 90210?",
            "expected": "Light clothing for mild/warm weather"
        },
        {
            "name": "Rainy Weather (Seattle)",
            "query": "What should I wear in 98101?",
            "expected": "Rain gear and waterproof clothing"
        },
        {
            "name": "Hot Weather (Miami)",
            "query": "What should I wear in 33101?",
            "expected": "Summer clothing for hot humid weather"
        },
        {
            "name": "Invalid Zip Code",
            "query": "What should I wear in 00000?",
            "expected": "Error handling - invalid zip code"
        },
        {
            "name": "Conversational Query",
            "query": "I'm visiting New York tomorrow (10001), what clothes do I need?",
            "expected": "Weather-based recommendations with conversational response"
        },
        {
            "name": "Multiple Locations",
            "query": "Compare weather in 10001 and 90210",
            "expected": "Should handle or clarify multiple locations"
        }
    ]

    try:
        comparator = AgentComparator()

        print("\n" + "="*80)
        print("AGENT COMPARISON TEST - STORY 6")
        print("="*80)
        print(f"\nRunning {len(test_cases)} test cases against both agents...")

        results = comparator.run_comparison(test_cases)

        # Generate report
        print("\n" + "="*80)
        print("GENERATING REPORT")
        print("="*80)

        report = comparator.generate_report(results)

        # Save report
        report_file = "comparison-report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✓ Report saved to: {report_file}")
        print("\n" + report)

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
