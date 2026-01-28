"""
Azure AI Agent Manager

This module provides functionality to create and manage Azure AI Agents
using container images. Supports the unified agent package for deployment
to Azure AI Foundry Hosted Agents.

Usage:
    # Interactive mode
    python azure_agent_manager.py

    # From environment variables
    python azure_agent_manager.py --from-env

    # List agents
    python azure_agent_manager.py --list

    # Delete agent
    python azure_agent_manager.py --delete <agent_name>
"""

import argparse
import os
import logging
from dataclasses import dataclass, field
from typing import Optional, List

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    ImageBasedHostedAgentDefinition,
    ProtocolVersionRecord,
    AgentProtocol,
)
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError, ClientAuthenticationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for creating an Azure AI Agent."""

    agent_name: str
    image: str
    cpu: str = "1"
    memory: str = "2Gi"
    protocol: AgentProtocol = field(default=AgentProtocol.RESPONSES)
    protocol_version: str = "v6"

    def validate(self) -> None:
        """Validate the agent configuration."""
        if not self.agent_name:
            raise ValueError("agent_name is required")
        if not self.image:
            raise ValueError("image is required")
        if not self.cpu:
            raise ValueError("cpu is required")
        if not self.memory:
            raise ValueError("memory is required")


@dataclass
class ProjectConfig:
    """Configuration for Azure AI Project connection."""

    endpoint: str
    credential: Optional[DefaultAzureCredential] = None

    def __post_init__(self):
        if self.credential is None:
            self.credential = DefaultAzureCredential()

    def validate(self) -> None:
        """Validate the project configuration."""
        if not self.endpoint:
            raise ValueError("endpoint is required")


class AzureAgentManager:
    """
    Manages Azure AI Agents lifecycle including creation, versioning, and deployment.
    """

    def __init__(self, project_config: ProjectConfig):
        """
        Initialize the Azure Agent Manager.

        Args:
            project_config: Configuration for connecting to the Azure AI Project.
        """
        project_config.validate()
        self._project_config = project_config
        self._client: Optional[AIProjectClient] = None

    @property
    def client(self) -> AIProjectClient:
        """Lazily initialize and return the AI Project client."""
        if self._client is None:
            try:
                self._client = AIProjectClient(
                    endpoint=self._project_config.endpoint,
                    credential=self._project_config.credential,
                )
                logger.info("Successfully initialized AIProjectClient")
            except ClientAuthenticationError as e:
                logger.error(f"Authentication failed: {e}")
                raise
            except AzureError as e:
                logger.error(f"Failed to initialize AIProjectClient: {e}")
                raise
        return self._client

    def create_agent_version(self, agent_config: AgentConfig) -> object:
        """
        Create a new version of an agent from a container image.

        Args:
            agent_config: Configuration for the agent to create.

        Returns:
            The created agent object.

        Raises:
            ValueError: If the configuration is invalid.
            AzureError: If there's an error communicating with Azure.
        """
        agent_config.validate()

        logger.info(f"Creating agent version for '{agent_config.agent_name}'")
        logger.info(f"  Image: {agent_config.image}")
        logger.info(f"  CPU: {agent_config.cpu}, Memory: {agent_config.memory}")

        try:
            definition = ImageBasedHostedAgentDefinition(
                container_protocol_versions=[
                    ProtocolVersionRecord(
                        protocol=agent_config.protocol,
                        version=agent_config.protocol_version,
                    )
                ],
                cpu=agent_config.cpu,
                memory=agent_config.memory,
                image=agent_config.image,
            )

            agent = self.client.agents.create_version(
                agent_name=agent_config.agent_name,
                definition=definition,
            )

            logger.info(f"Successfully created agent version for '{agent_config.agent_name}'")
            return agent

        except AzureError as e:
            logger.error(f"Failed to create agent version: {e}")
            raise

    def list_agents(self) -> List[object]:
        """
        List all agents in the project.

        Returns:
            List of agent objects.
        """
        try:
            agents = self.client.agents.list()
            agent_list = list(agents)
            logger.info(f"Found {len(agent_list)} agents")
            return agent_list
        except AzureError as e:
            logger.error(f"Failed to list agents: {e}")
            raise

    def get_agent(self, agent_name: str) -> object:
        """
        Get an agent by name.

        Args:
            agent_name: The agent name.

        Returns:
            The agent object.
        """
        try:
            agent = self.client.agents.get(agent_name)
            logger.info(f"Found agent: {agent.name}")
            return agent
        except AzureError as e:
            logger.error(f"Failed to get agent {agent_name}: {e}")
            raise

    def delete_agent(self, agent_name: str) -> None:
        """
        Delete an agent.

        Args:
            agent_name: The agent name to delete.
        """
        try:
            self.client.agents.delete(agent_name)
            logger.info(f"Successfully deleted agent: {agent_name}")
        except AzureError as e:
            logger.error(f"Failed to delete agent {agent_name}: {e}")
            raise

    def close(self) -> None:
        """Close the client connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("Closed AIProjectClient connection")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def create_agent_from_env() -> object:
    """
    Create an agent using configuration from environment variables.

    Environment Variables:
        AZURE_AI_PROJECT_ENDPOINT: The Azure AI Project endpoint URL
        AGENT_NAME: Name of the agent to create
        AGENT_IMAGE: Container image for the agent
        AGENT_CPU: CPU allocation (default: "1")
        AGENT_MEMORY: Memory allocation (default: "2Gi")
        AGENT_PROTOCOL_VERSION: Protocol version (default: "v6")

    Returns:
        The created agent object.
    """
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    if not endpoint:
        raise ValueError("AZURE_AI_PROJECT_ENDPOINT environment variable is required")

    agent_name = os.environ.get("AGENT_NAME")
    if not agent_name:
        raise ValueError("AGENT_NAME environment variable is required")

    agent_image = os.environ.get("AGENT_IMAGE")
    if not agent_image:
        raise ValueError("AGENT_IMAGE environment variable is required")

    project_config = ProjectConfig(endpoint=endpoint)
    agent_config = AgentConfig(
        agent_name=agent_name,
        image=agent_image,
        cpu=os.environ.get("AGENT_CPU", "1"),
        memory=os.environ.get("AGENT_MEMORY", "2Gi"),
        protocol_version=os.environ.get("AGENT_PROTOCOL_VERSION", "v6"),
    )

    with AzureAgentManager(project_config) as manager:
        return manager.create_agent_version(agent_config)


def interactive_create() -> None:
    """Interactive mode to create an agent with prompts."""
    print("\n" + "=" * 60)
    print("Azure AI Agent Manager - Interactive Mode")
    print("=" * 60)

    # Get endpoint
    default_endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
    endpoint = input(f"Project endpoint [{default_endpoint}]: ").strip() or default_endpoint
    if not endpoint:
        print("Error: Endpoint is required")
        return

    # Get agent name
    default_name = os.environ.get("AGENT_NAME", "weather-clothing-advisor")
    agent_name = input(f"Agent name [{default_name}]: ").strip() or default_name

    # Get container image
    default_image = os.environ.get("AGENT_IMAGE", "")
    agent_image = input(f"Container image [{default_image}]: ").strip() or default_image
    if not agent_image:
        print("Error: Container image is required")
        return

    # Get optional parameters
    cpu = input("CPU allocation [1]: ").strip() or "1"
    memory = input("Memory allocation [2Gi]: ").strip() or "2Gi"
    protocol_version = input("Protocol version [v6]: ").strip() or "v6"

    print("\n" + "-" * 60)
    print("Configuration:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Agent Name: {agent_name}")
    print(f"  Image: {agent_image}")
    print(f"  CPU: {cpu}, Memory: {memory}")
    print(f"  Protocol: {protocol_version}")
    print("-" * 60)

    confirm = input("\nCreate agent? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    project_config = ProjectConfig(endpoint=endpoint)
    agent_config = AgentConfig(
        agent_name=agent_name,
        image=agent_image,
        cpu=cpu,
        memory=memory,
        protocol_version=protocol_version,
    )

    with AzureAgentManager(project_config) as manager:
        agent = manager.create_agent_version(agent_config)
        print(f"\n✓ Agent created successfully!")
        print(f"  Agent ID: {agent.id}")
        print(f"  Name: {agent.name}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Azure AI Agent Manager - Create and manage Foundry Hosted Agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python azure_agent_manager.py

  # Create from environment variables
  python azure_agent_manager.py --from-env

  # List all agents
  python azure_agent_manager.py --list

  # Delete an agent
  python azure_agent_manager.py --delete <agent_id>

Environment Variables:
  AZURE_AI_PROJECT_ENDPOINT  - Project endpoint URL
  AGENT_NAME                 - Name for the agent
  AGENT_IMAGE                - Container image (e.g., myregistry.azurecr.io/agent:v1)
  AGENT_CPU                  - CPU allocation (default: 1)
  AGENT_MEMORY               - Memory allocation (default: 2Gi)
  AGENT_PROTOCOL_VERSION     - Protocol version (default: v6)
        """
    )

    parser.add_argument(
        "--from-env",
        action="store_true",
        help="Create agent from environment variables"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all agents in the project"
    )
    parser.add_argument(
        "--delete",
        metavar="AGENT_ID",
        help="Delete an agent by ID"
    )
    parser.add_argument(
        "--endpoint",
        help="Azure AI Project endpoint (overrides AZURE_AI_PROJECT_ENDPOINT)"
    )

    args = parser.parse_args()

    # Get endpoint
    endpoint = args.endpoint or os.environ.get("AZURE_AI_PROJECT_ENDPOINT")

    if args.list:
        if not endpoint:
            print("Error: --endpoint or AZURE_AI_PROJECT_ENDPOINT required")
            return 1
        project_config = ProjectConfig(endpoint=endpoint)
        with AzureAgentManager(project_config) as manager:
            agents = manager.list_agents()
            print(f"\nFound {len(agents)} agents:")
            for agent in agents:
                print(f"  - {agent.name} (ID: {agent.id})")
        return 0

    if args.delete:
        if not endpoint:
            print("Error: --endpoint or AZURE_AI_PROJECT_ENDPOINT required")
            return 1
        project_config = ProjectConfig(endpoint=endpoint)
        with AzureAgentManager(project_config) as manager:
            manager.delete_agent(args.delete)
            print(f"✓ Agent {args.delete} deleted")
        return 0

    if args.from_env:
        agent = create_agent_from_env()
        print(f"✓ Agent created: {agent.id}")
        return 0

    # Default: interactive mode
    interactive_create()
    return 0


# Entry point
if __name__ == "__main__":
    exit(main())
