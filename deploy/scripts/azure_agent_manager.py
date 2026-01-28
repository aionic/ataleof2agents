"""
Azure AI Agent Manager

This module provides functionality to create and manage Azure AI Agents
using container images. Supports the unified agent package for deployment
to Azure AI Foundry Hosted Agents.

Uses REST API directly since SDK models are not yet available.

Usage:
    # Interactive mode
    python azure_agent_manager.py

    # From environment variables
    python azure_agent_manager.py --from-env

    # List agents
    python azure_agent_manager.py --list

    # Delete agent
    python azure_agent_manager.py --delete <agent_name>

    # Start agent
    python azure_agent_manager.py --start <agent_name>
"""

import argparse
import os
import logging
import json
import requests
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Version for Foundry Hosted Agents
API_VERSION = "2025-05-15-preview"


@dataclass
class AgentConfig:
    """Configuration for creating an Azure AI Agent."""

    agent_name: str
    image: str
    cpu: str = "1"
    memory: str = "2Gi"
    protocol: str = "responses"
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

    def to_request_body(self) -> Dict[str, Any]:
        """Convert to REST API request body."""
        return {
            "properties": {
                "definition": {
                    "type": "ImageBased",
                    "image": self.image,
                    "cpu": self.cpu,
                    "memory": self.memory,
                },
                "protocolVersion": {
                    "name": self.protocol_version,
                    "protocol": self.protocol,
                },
            }
        }


@dataclass
class ProjectConfig:
    """Configuration for Azure AI Project connection."""

    endpoint: str
    credential: Optional[DefaultAzureCredential] = None
    _token_provider: Optional[Any] = field(default=None, repr=False)

    def __post_init__(self):
        if self.credential is None:
            self.credential = DefaultAzureCredential()
        self._token_provider = get_bearer_token_provider(
            self.credential, "https://ai.azure.com/.default"
        )

    def validate(self) -> None:
        """Validate the project configuration."""
        if not self.endpoint:
            raise ValueError("endpoint is required")

    def get_access_token(self) -> str:
        """Get an access token for the Azure Cognitive Services scope."""
        return self._token_provider()

    @property
    def base_url(self) -> str:
        """Get the base URL for API calls."""
        return self.endpoint.rstrip("/")


class AzureAgentManager:
    """
    Manages Azure AI Agents lifecycle including creation, versioning, and deployment.
    Uses REST API directly since SDK models are not yet available.
    """

    def __init__(self, project_config: ProjectConfig):
        """
        Initialize the Azure Agent Manager.

        Args:
            project_config: Configuration for connecting to the Azure AI Project.
        """
        project_config.validate()
        self._project_config = project_config

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token."""
        token = self._project_config.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _api_url(self, path: str) -> str:
        """Build full API URL with version."""
        base = self._project_config.base_url
        return f"{base}{path}?api-version={API_VERSION}"

    def create_agent_version(self, agent_config: AgentConfig) -> Dict[str, Any]:
        """
        Create a new version of an agent from a container image.

        Args:
            agent_config: Configuration for the agent to create.

        Returns:
            The created agent response.

        Raises:
            ValueError: If the configuration is invalid.
            requests.HTTPError: If there's an error communicating with Azure.
        """
        agent_config.validate()

        logger.info(f"Creating agent version for '{agent_config.agent_name}'")
        logger.info(f"  Image: {agent_config.image}")
        logger.info(f"  CPU: {agent_config.cpu}, Memory: {agent_config.memory}")

        url = self._api_url(f"/hostedagents/{agent_config.agent_name}/versions/1")
        body = agent_config.to_request_body()

        logger.debug(f"PUT {url}")
        logger.debug(f"Body: {json.dumps(body, indent=2)}")

        response = requests.put(url, headers=self._get_headers(), json=body)

        if response.status_code >= 400:
            logger.error(f"Failed to create agent: {response.status_code}")
            logger.error(f"Response: {response.text}")
            response.raise_for_status()

        result = response.json()
        logger.info(f"Successfully created agent version for '{agent_config.agent_name}'")
        return result

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all agents in the project.

        Returns:
            List of agent objects.
        """
        url = self._api_url("/hostedagents")
        response = requests.get(url, headers=self._get_headers())

        if response.status_code >= 400:
            logger.error(f"Failed to list agents: {response.status_code}")
            logger.error(f"Response: {response.text}")
            response.raise_for_status()

        result = response.json()
        agents = result.get("value", [])
        logger.info(f"Found {len(agents)} agents")
        return agents

    def get_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Get an agent by name.

        Args:
            agent_name: The agent name.

        Returns:
            The agent object.
        """
        url = self._api_url(f"/hostedagents/{agent_name}")
        response = requests.get(url, headers=self._get_headers())

        if response.status_code >= 400:
            logger.error(f"Failed to get agent {agent_name}: {response.status_code}")
            response.raise_for_status()

        result = response.json()
        logger.info(f"Found agent: {agent_name}")
        return result

    def delete_agent(self, agent_name: str) -> None:
        """
        Delete an agent.

        Args:
            agent_name: The agent name to delete.
        """
        url = self._api_url(f"/hostedagents/{agent_name}")
        response = requests.delete(url, headers=self._get_headers())

        if response.status_code >= 400 and response.status_code != 404:
            logger.error(f"Failed to delete agent {agent_name}: {response.status_code}")
            response.raise_for_status()

        logger.info(f"Successfully deleted agent: {agent_name}")

    def start_agent(self, agent_name: str, version: str = "1") -> Dict[str, Any]:
        """
        Start an agent.

        Args:
            agent_name: The agent name.
            version: The agent version to start (default: "1").

        Returns:
            The operation result.
        """
        url = self._api_url(f"/hostedagents/{agent_name}/versions/{version}:start")
        response = requests.post(url, headers=self._get_headers())

        if response.status_code >= 400:
            logger.error(f"Failed to start agent {agent_name}: {response.status_code}")
            logger.error(f"Response: {response.text}")
            response.raise_for_status()

        logger.info(f"Started agent: {agent_name} (version {version})")
        return response.json() if response.text else {}

    def stop_agent(self, agent_name: str, version: str = "1") -> Dict[str, Any]:
        """
        Stop an agent.

        Args:
            agent_name: The agent name.
            version: The agent version to stop (default: "1").

        Returns:
            The operation result.
        """
        url = self._api_url(f"/hostedagents/{agent_name}/versions/{version}:stop")
        response = requests.post(url, headers=self._get_headers())

        if response.status_code >= 400:
            logger.error(f"Failed to stop agent {agent_name}: {response.status_code}")
            response.raise_for_status()

        logger.info(f"Stopped agent: {agent_name} (version {version})")
        return response.json() if response.text else {}

    def close(self) -> None:
        """Close the manager (no-op for REST API)."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def create_agent_from_env() -> Dict[str, Any]:
    """
    Create an agent using configuration from environment variables.

    Environment Variables:
        AZURE_AI_PROJECT_ENDPOINT: The Azure AI Project endpoint URL
        AGENT_NAME: Name of the agent to create (default: weather-clothing-advisor)
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

    agent_name = os.environ.get("AGENT_NAME", "weather-clothing-advisor")

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
        print(f"  Response: {json.dumps(agent, indent=2)}")


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
  python azure_agent_manager.py --delete <agent_name>

  # Start an agent
  python azure_agent_manager.py --start <agent_name>

  # Stop an agent
  python azure_agent_manager.py --stop <agent_name>

Environment Variables:
  AZURE_AI_PROJECT_ENDPOINT  - Project endpoint URL
  AGENT_NAME                 - Name for the agent (default: weather-clothing-advisor)
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
        metavar="AGENT_NAME",
        help="Delete an agent by name"
    )
    parser.add_argument(
        "--start",
        metavar="AGENT_NAME",
        help="Start an agent by name"
    )
    parser.add_argument(
        "--stop",
        metavar="AGENT_NAME",
        help="Stop an agent by name"
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
                name = agent.get("name", "unknown")
                state = agent.get("properties", {}).get("provisioningState", "unknown")
                print(f"  - {name} (state: {state})")
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

    if args.start:
        if not endpoint:
            print("Error: --endpoint or AZURE_AI_PROJECT_ENDPOINT required")
            return 1
        project_config = ProjectConfig(endpoint=endpoint)
        with AzureAgentManager(project_config) as manager:
            manager.start_agent(args.start)
            print(f"✓ Agent {args.start} started")
        return 0

    if args.stop:
        if not endpoint:
            print("Error: --endpoint or AZURE_AI_PROJECT_ENDPOINT required")
            return 1
        project_config = ProjectConfig(endpoint=endpoint)
        with AzureAgentManager(project_config) as manager:
            manager.stop_agent(args.stop)
            print(f"✓ Agent {args.stop} stopped")
        return 0

    if args.from_env:
        agent = create_agent_from_env()
        print(f"✓ Agent created!")
        print(json.dumps(agent, indent=2))
        return 0

    # Default: interactive mode
    interactive_create()
    return 0


# Entry point
if __name__ == "__main__":
    exit(main())
