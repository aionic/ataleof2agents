"""
Invoke Azure AI Hosted Agent

This script invokes a hosted agent deployed in Azure AI Foundry using the
modern Responses API with the v2 SDK pattern.

The agent must be STARTED before invoking:
1. Azure CLI: az cognitiveservices agent start --account-name <account> --project-name <project> --name <agent> --agent-version <version>
2. Foundry Portal: Start from Agent Builder UI

Usage:
    # Basic invocation
    python invoke_hosted_agent.py --endpoint <PROJECT_ENDPOINT> --agent <AGENT_NAME> --message "Hello"

    # Using environment variables
    export AZURE_AI_PROJECT_ENDPOINT="https://your-account.services.ai.azure.com/api/projects/your-project"
    export AGENT_NAME="weather-clothing-advisor"
    python invoke_hosted_agent.py --message "What should I wear in Seattle today?"
"""

import argparse
import os
import logging
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def invoke_agent(
    endpoint: str,
    agent_name: str,
    agent_version: str,
    message: str,
    use_conversation: bool = False,
) -> str:
    """
    Invoke a hosted agent using the modern Responses API (v2 SDK pattern).

    Uses the agent_reference pattern in extra_body to route requests
    to hosted container agents.

    Args:
        endpoint: Azure AI Project endpoint
        agent_name: Name of the agent to invoke
        agent_version: Version of the agent (e.g., "1")
        message: User message to send to the agent
        use_conversation: Whether to use conversation tracking

    Returns:
        The agent's response text
    """
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
    ):
        # Get the OpenAI client for responses API (GA SDK: project_client.get_openai_client)
        # API version for Responses API (preview)
        openai_client = project_client.get_openai_client(
            api_version="2025-03-01-preview"
        )

        # Build agent reference (v2 SDK pattern - dictionary, not model class)
        agent_ref = {
            "name": agent_name,
            "version": agent_version,
            "type": "agent_reference",
        }

        if use_conversation:
            # Multi-turn: Create conversation with initial message
            conversation = openai_client.conversations.create(
                items=[{"type": "message", "role": "user", "content": message}],
            )
            logger.info(f"Created conversation (id: {conversation.id})")

            try:
                # Get response using conversation
                response = openai_client.responses.create(
                    conversation=conversation.id,
                    extra_body={"agent": agent_ref},
                    input="",  # Empty when using conversation
                )
            finally:
                # Clean up conversation
                openai_client.conversations.delete(conversation_id=conversation.id)
                logger.info("Conversation deleted")
        else:
            # Single-turn: Direct invocation with input
            # For hosted agents, the model parameter is the agent name
            response = openai_client.responses.create(
                model=agent_name,  # Hosted agent name as model
                input=[{"role": "user", "content": message}],
                extra_body={"agent": agent_ref},
            )

        # Extract response text
        if hasattr(response, "output_text"):
            output_text = response.output_text
        elif hasattr(response, "output") and response.output:
            # Handle structured output
            output_text = "\n".join(
                str(item.content) if hasattr(item, "content") else str(item)
                for item in response.output
            )
        else:
            output_text = str(response)

        logger.info("Agent response received")
        return output_text


def main():
    parser = argparse.ArgumentParser(description="Invoke an Azure AI Hosted Agent")
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("AZURE_AI_PROJECT_ENDPOINT"),
        help="Azure AI Project endpoint URL",
    )
    parser.add_argument(
        "--agent",
        default=os.environ.get("AGENT_NAME", "weather-clothing-advisor"),
        help="Name of the agent to invoke",
    )
    parser.add_argument(
        "--version",
        default=os.environ.get("AGENT_VERSION", "1"),
        help="Version of the agent to invoke",
    )
    parser.add_argument(
        "--message",
        "-m",
        required=True,
        help="Message to send to the agent",
    )
    parser.add_argument(
        "--conversation",
        action="store_true",
        help="Use conversation tracking for multi-turn interactions",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.endpoint:
        print("ERROR: --endpoint or AZURE_AI_PROJECT_ENDPOINT environment variable is required")
        return 1

    print(f"\n🤖 Invoking agent: {args.agent} (version {args.version})")
    print(f"📧 Message: {args.message}")
    print(f"🔗 Endpoint: {args.endpoint}")
    print("-" * 60)

    try:
        response = invoke_agent(
            endpoint=args.endpoint,
            agent_name=args.agent,
            agent_version=args.version,
            message=args.message,
            use_conversation=args.conversation,
        )
        print(f"\n📨 Agent Response:\n{response}")
        return 0
    except Exception as e:
        logger.exception("Failed to invoke agent")
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
