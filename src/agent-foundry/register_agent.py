"""
Agent registration script for Azure AI Foundry deployment.

Registers the weather clothing advisor agent with Azure AI Foundry,
including tool definitions and instructions.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from azure.ai.projects import AIProjectClient
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
        contracts_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'specs',
            '001-weather-clothing-advisor',
            'contracts'
        )
        prompts_file = os.path.join(contracts_dir, 'agent-prompts.md')

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
        openapi_file = os.path.join(
            os.path.dirname(__file__),
            '..',
            'weather-api',
            'openapi.json'
        )

        try:
            with open(openapi_file, 'r', encoding='utf-8') as f:
                openapi_spec = json.load(f)
            logger.info(f"Loaded OpenAPI spec from {openapi_file}")
            return openapi_spec
        except FileNotFoundError:
            logger.error(f"OpenAPI spec file not found: {openapi_file}")
            raise

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get the OpenAPI tool definition for Foundry.

        Returns:
            Tool definition dictionary using OpenAPI spec
        """
        try:
            openapi_spec = self.load_openapi_spec()

            # Create OpenAPI tool definition for Foundry
            # Foundry supports OpenAPI 3.0 tools for external HTTP APIs
            tool_definition = {
                "type": "openapi",
                "openapi": {
                    "name": "get_weather",
                    "description": "Retrieve current weather data for a US zip code including temperature, conditions, humidity, wind speed, and precipitation",
                    "spec": openapi_spec,
                    "operation_id": "getWeather",  # From OpenAPI spec paths./api/weather.get.operationId
                    "authentication": {
                        "type": "none"  # Weather API uses anonymous access
                    }
                }
            }

            logger.info("Created OpenAPI tool definition for get_weather")
            return tool_definition

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
            tool_definition = self.get_tool_definition()

            # Get model deployment name
            model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
            if not model_deployment:
                raise ValueError("AZURE_AI_MODEL_DEPLOYMENT_NAME environment variable is required")

            # Register agent with Foundry
            agent = self.client.agents.create_agent(
                name=agent_name,
                instructions=instructions,
                model=model_deployment,
                tools=[tool_definition],
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

    def update_agent(self, agent_id: str) -> None:
        """
        Update an existing agent's instructions or tools.

        Args:
            agent_id: ID of the agent to update
        """
        logger.info(f"Updating agent: {agent_id}")

        try:
            instructions = self.load_agent_instructions()
            tool_definition = self.get_tool_definition()

            self.client.agents.update_agent(
                agent_id=agent_id,
                instructions=instructions,
                tools=[tool_definition]
            )

            logger.info(f"Successfully updated agent: {agent_id}")

        except Exception as e:
            logger.exception(f"Error updating agent: {agent_id}")
            raise

    def delete_agent(self, agent_id: str) -> None:
        """
        Delete an agent from Foundry.

        Args:
            agent_id: ID of the agent to delete
        """
        logger.info(f"Deleting agent: {agent_id}")

        try:
            self.client.agents.delete_agent(agent_id)
            logger.info(f"Successfully deleted agent: {agent_id}")
        except Exception as e:
            logger.exception(f"Error deleting agent: {agent_id}")
            raise

    def list_agents(self) -> list:
        """
        List all registered agents.

        Returns:
            List of agent objects
        """
        try:
            agents = self.client.agents.list_agents()
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
    parser.add_argument("--agent-id", help="Agent ID (required for update/delete)")
    parser.add_argument("--agent-name", default="WeatherClothingAdvisor",
                       help="Agent name (for register action)")

    args = parser.parse_args()

    try:
        registration = FoundryAgentRegistration()

        if args.action == "register":
            agent_id = registration.register_agent(args.agent_name)
            print(f"✓ Agent registered successfully")
            print(f"  Agent ID: {agent_id}")
            print(f"  Agent Name: {args.agent_name}")

        elif args.action == "update":
            if not args.agent_id:
                print("Error: --agent-id is required for update action")
                sys.exit(1)
            registration.update_agent(args.agent_id)
            print(f"✓ Agent updated successfully: {args.agent_id}")

        elif args.action == "delete":
            if not args.agent_id:
                print("Error: --agent-id is required for delete action")
                sys.exit(1)
            registration.delete_agent(args.agent_id)
            print(f"✓ Agent deleted successfully: {args.agent_id}")

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
