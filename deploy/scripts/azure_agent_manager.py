"""
Azure AI Agent Manager

This module provides functionality to create and manage Azure AI Agents
using container images.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional

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


# Example usage
if __name__ == "__main__":
    # Example 1: Direct configuration
    project_config = ProjectConfig(
        endpoint="https://petermessina-8930-resource.services.ai.azure.com/api/projects/petermessina-8930"
    )

    agent_config = AgentConfig(
        agent_name="my-agent",
        image="acrdemocontent001.azurecr.io/my-agent:v6",
        cpu="1",
        memory="2Gi",
        protocol_version="v6",
    )

    with AzureAgentManager(project_config) as manager:
        agent = manager.create_agent_version(agent_config)
        print(f"Created agent: {agent}")

    # Example 2: Using environment variables
    # agent = create_agent_from_env()
