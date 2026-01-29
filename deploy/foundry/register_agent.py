"""
Agent registration script for Azure AI Foundry deployment.

Registers the weather clothing advisor agent with Azure AI Foundry,
including tool definitions and instructions.

Uses the azure-ai-projects SDK v2.0.0+ (GA API with conversations/responses).

Usage:
    python register_agent.py register --agent-name WeatherClothingAdvisor
    python register_agent.py list
    python register_agent.py delete --agent-name WeatherClothingAdvisor
"""

import os
import sys
import json
import logging
from typing import Dict, Any
from pathlib import Path

# Get project root (deploy/foundry -> deploy -> project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent

try:
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import (
        PromptAgentDefinition,
        OpenApiAgentTool,
        OpenApiFunctionDefinition,
        OpenApiAnonymousAuthDetails,
    )
    from azure.identity import DefaultAzureCredential
except ImportError:
    logging.error("Azure AI Foundry SDK not installed. Please install: pip install azure-ai-projects")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FoundryAgentRegistration:
    """Handles registration of agent with Azure AI Foundry."""

    def __init__(self):
        """Initialize Foundry agent registration."""
        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        self.weather_api_url = os.getenv("WEATHER_API_URL")

        if not self.project_endpoint:
            raise ValueError("AZURE_AI_PROJECT_ENDPOINT environment variable is required")
        if not self.weather_api_url:
            raise ValueError("WEATHER_API_URL environment variable is required (external weather API endpoint)")

        # Initialize Azure AI Project Client
        credential = DefaultAzureCredential()
        self.client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=credential
        )

        logger.info(f"Initialized Foundry client for project: {self.project_endpoint}")
        logger.info(f"Weather API endpoint: {self.weather_api_url}")

    def load_agent_instructions(self) -> str:
        """
        Load agent instructions from contracts/agent-prompts.md.

        Returns:
            Agent instruction text
        """
        prompts_file = PROJECT_ROOT / 'specs' / '001-weather-clothing-advisor' / 'contracts' / 'agent-prompts.md'

        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                instructions = f.read()
            logger.info(f"Loaded agent instructions from {prompts_file}")
            return instructions
        except FileNotFoundError:
            logger.error(f"Agent prompts file not found: {prompts_file}")
            raise

    def load_openapi_spec(self) -> Dict[str, Any]:
        """
        Load OpenAPI 3.0 specification for weather API.

        Returns:
            OpenAPI spec dictionary
        """
        openapi_file = PROJECT_ROOT / 'src' / 'weather-api' / 'openapi.json'

        try:
            with open(openapi_file, 'r', encoding='utf-8') as f:
                openapi_spec = json.load(f)
            logger.info(f"Loaded OpenAPI spec from {openapi_file}")
            return openapi_spec
        except FileNotFoundError:
            logger.error(f"OpenAPI spec file not found: {openapi_file}")
            raise

    def get_tool_definition(self) -> OpenApiAgentTool:
        """
        Get the OpenAPI tool definition for Foundry.

        Returns:
            OpenApiAgentTool instance
        """
        try:
            openapi_spec = self.load_openapi_spec()

            # Create OpenAPI tool using SDK models
            tool = OpenApiAgentTool(
                openapi=OpenApiFunctionDefinition(
                    name="get_weather",
                    description="Retrieve current weather data for a US zip code including temperature, conditions, humidity, wind speed, and precipitation",
                    spec=openapi_spec,
                    auth=OpenApiAnonymousAuthDetails(),
                )
            )

            logger.info("Created OpenAPI tool definition for get_weather")
            return tool

        except Exception as e:
            logger.exception("Error creating tool definition")
            raise

    def register_agent(self, agent_name: str = "WeatherClothingAdvisor") -> str:
        """
        Register agent with Azure AI Foundry.

        Args:
            agent_name: Name for the agent

        Returns:
            Agent ID from Foundry
        """
        logger.info(f"Registering agent: {agent_name}")

        try:
            # Load instructions and tool
            instructions = self.load_agent_instructions()
            tool = self.get_tool_definition()

            # Get model deployment name
            model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
            if not model_deployment:
                raise ValueError("AZURE_AI_MODEL_DEPLOYMENT_NAME environment variable is required")

            # Create agent definition using SDK models
            definition = PromptAgentDefinition(
                model=model_deployment,
                instructions=instructions,
                tools=[tool],
            )

            # Register agent with Foundry using new SDK API
            agent = self.client.agents.create(
                name=agent_name,
                definition=definition,
                description="Weather-based clothing advisor using OpenAPI weather tool",
                metadata={
                    "deployment_type": "foundry-agent",
                    "version": "1.0.0",
                    "feature": "001-weather-clothing-advisor"
                }
            )

            agent_id = agent.id
            logger.info(f"Successfully registered agent with ID: {agent_id}")

            return agent_id

        except Exception as e:
            logger.exception(f"Error registering agent: {agent_name}")
            raise

    def update_agent(self, agent_name: str) -> None:
        """
        Update an existing agent's instructions or tools.

        Args:
            agent_name: Name of the agent to update
        """
        logger.info(f"Updating agent: {agent_name}")

        try:
            instructions = self.load_agent_instructions()
            tool = self.get_tool_definition()

            # Get model deployment name
            model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
            if not model_deployment:
                raise ValueError("AZURE_AI_MODEL_DEPLOYMENT_NAME environment variable is required")

            # Create updated definition
            definition = PromptAgentDefinition(
                model=model_deployment,
                instructions=instructions,
                tools=[tool],
            )

            self.client.agents.update(
                agent_name=agent_name,
                definition=definition,
            )

            logger.info(f"Successfully updated agent: {agent_name}")

        except Exception as e:
            logger.exception(f"Error updating agent: {agent_name}")
            raise

    def delete_agent(self, agent_name: str) -> None:
        """
        Delete an agent from Foundry.

        Args:
            agent_name: Name of the agent to delete
        """
        logger.info(f"Deleting agent: {agent_name}")

        try:
            self.client.agents.delete(agent_name)
            logger.info(f"Successfully deleted agent: {agent_name}")
        except Exception as e:
            logger.exception(f"Error deleting agent: {agent_name}")
            raise

    def list_agents(self) -> list:
        """
        List all registered agents.

        Returns:
            List of agent objects
        """
        try:
            agents_paged = self.client.agents.list()
            agents = list(agents_paged)  # Convert ItemPaged to list
            logger.info(f"Found {len(agents)} registered agents")
            return agents
        except Exception as e:
            logger.exception("Error listing agents")
            raise


def main():
    """Main entry point for agent registration."""
    import argparse

    parser = argparse.ArgumentParser(description="Register Weather Clothing Advisor agent with Azure AI Foundry")
    parser.add_argument("action", choices=["register", "update", "delete", "list"],
                       help="Action to perform")
    parser.add_argument("--agent-name", default="WeatherClothingAdvisor",
                       help="Agent name (for register/update/delete actions)")

    args = parser.parse_args()

    try:
        registration = FoundryAgentRegistration()

        if args.action == "register":
            agent_id = registration.register_agent(args.agent_name)
            print(f"✓ Agent registered successfully")
            print(f"  Agent ID: {agent_id}")
            print(f"  Agent Name: {args.agent_name}")

        elif args.action == "update":
            registration.update_agent(args.agent_name)
            print(f"✓ Agent updated successfully: {args.agent_name}")

        elif args.action == "delete":
            registration.delete_agent(args.agent_name)
            print(f"✓ Agent deleted successfully: {args.agent_name}")

        elif args.action == "list":
            agents = registration.list_agents()
            print(f"\nRegistered Agents ({len(agents)}):")
            for agent in agents:
                print(f"  - {agent.name} (ID: {agent.id})")

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
