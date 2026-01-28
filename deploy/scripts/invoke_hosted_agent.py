"""
Invoke Azure AI Hosted Agent

This script invokes a hosted agent deployed in Azure AI Foundry using the
Responses API. The agent must be STARTED before invoking.

IMPORTANT: Before invoking, start the agent using one of these methods:
1. Azure CLI: az cognitiveservices agent start --account-name <account> --project-name <project> --name <agent> --agent-version <version>
2. Foundry Portal: Start from Agent Builder UI
3. Azure Developer CLI: azd up (handles start automatically)

Usage:
    # Basic invocation
    python invoke_hosted_agent.py --endpoint <PROJECT_ENDPOINT> --agent <AGENT_NAME> --message "Hello"

    # Using environment variables
    export AZURE_AI_PROJECT_ENDPOINT="https://your-account.services.ai.azure.com/api/projects/your-project"
    export AGENT_NAME="weather-advisor"
    python invoke_hosted_agent.py --message "What should I wear in Seattle today?"
"""

import argparse
import os
import logging
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentReference
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
    Invoke a hosted agent using the Responses API (validated MS docs pattern).

    Args:
        endpoint: Azure AI Project endpoint
        agent_name: Name of the agent to invoke
        agent_version: Version of the agent (e.g., "1")
        message: User message to send to the agent
        use_conversation: Whether to use conversation tracking

    Returns:
        The agent's response text
    """
    credential = DefaultAzureCredential()

    with AIProjectClient(endpoint=endpoint, credential=credential) as project_client:
        # First, retrieve the agent using the SDK
        try:
            agent = project_client.agents.get(agent_name)
            logger.info(f"Found agent: {agent.name} (version: {getattr(agent, 'version', 'N/A')})")
        except Exception as e:
            logger.error(f"Failed to get agent '{agent_name}': {e}")
            raise

        # Get the OpenAI client for responses API
        openai_client = project_client.get_openai_client()

        # Use AgentReference model from the SDK (validated pattern from MS docs)
        agent_ref = AgentReference(name=agent.name, version=agent_version)

        if use_conversation:
            # Create a conversation for multi-turn interactions
            conversation = openai_client.conversations.create(
                items=[{"type": "message", "role": "user", "content": message}],
            )
            logger.info(f"Created conversation (id: {conversation.id})")

            # Get response using conversation
            response = openai_client.responses.create(
                conversation=conversation.id,
                extra_body={"agent": agent_ref.as_dict()},
                input="",
            )

            # Clean up conversation
            openai_client.conversations.delete(conversation_id=conversation.id)
            logger.info("Conversation deleted")
        else:
            # Single-turn invocation using validated AgentReference pattern
            response = openai_client.responses.create(
                input=[{"role": "user", "content": message}],
                extra_body={"agent": agent_ref.as_dict()}
            )

        output_text = response.output_text if hasattr(response, 'output_text') else str(response)
        logger.info(f"Agent response received")
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
        default=os.environ.get("AGENT_NAME", "weather-advisor"),
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
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
