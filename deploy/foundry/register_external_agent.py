#!/usr/bin/env python3
"""
Register external Container Apps agent as an OpenAPI tool in Azure AI Foundry.

This enables Foundry to invoke the externally hosted agent via the meta-agent pattern.
The meta-agent uses an OpenAPI tool to call the ACA /responses endpoint.

Uses the azure-ai-projects SDK v2.0.0+ (GA API with conversations/responses).

Usage:
    python register_external_agent.py register --agent-name WeatherAdvisorMeta
    python register_external_agent.py list
"""

import os
import sys
import json
import logging
from typing import Dict, Any

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass  # No-op if dotenv not installed

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    OpenApiAgentTool,
    OpenApiFunctionDefinition,
    OpenApiAnonymousAuthDetails,
)
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExternalAgentRegistration:
    """Register external Container Apps agent with Azure AI Foundry."""

    def __init__(self):
        """Initialize Foundry client."""
        load_dotenv()

        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        if not self.project_endpoint:
            raise ValueError("AZURE_AI_PROJECT_ENDPOINT environment variable is required")

        self.external_agent_url = os.getenv("EXTERNAL_AGENT_URL")
        if not self.external_agent_url:
            raise ValueError("EXTERNAL_AGENT_URL environment variable is required")

        credential = DefaultAzureCredential()
        self.client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=credential
        )

        logger.info(f"Initialized Foundry client for project: {self.project_endpoint}")
        logger.info(f"External agent URL: {self.external_agent_url}")

    def load_external_agent_spec(self) -> Dict[str, Any]:
        """
        Load OpenAPI specification for external Container Apps agent.

        Returns:
            OpenAPI spec dictionary
        """
        openapi_file = os.path.join(
            os.path.dirname(__file__),
            'external-agent-openapi.json'
        )

        try:
            with open(openapi_file, 'r', encoding='utf-8') as f:
                openapi_spec = json.load(f)

            # Update server URL with environment variable
            if openapi_spec.get('servers'):
                openapi_spec['servers'][0]['url'] = self.external_agent_url

            logger.info(f"Loaded external agent OpenAPI spec from {openapi_file}")
            return openapi_spec
        except FileNotFoundError:
            logger.error(f"OpenAPI spec file not found: {openapi_file}")
            raise

    def load_meta_agent_instructions(self) -> str:
        """
        Load instructions for the meta-agent that invokes external agent.

        Returns:
            Agent instructions string
        """
        instructions = """You are a meta-agent that can invoke an externally hosted Weather Clothing Advisor agent.

When a user asks for clothing recommendations or weather information, you should:
1. Use the chatWithExternalAgent tool to forward the request to the external agent
2. Return the response from the external agent to the user
3. If the external agent returns an error, explain the issue to the user

The external agent is running in Azure Container Apps and provides weather-based clothing recommendations for US zip codes.

Always use the external agent for weather and clothing questions - do not try to answer them yourself.
"""
        return instructions

    def get_external_agent_tool(self) -> OpenApiAgentTool:
        """
        Get the OpenAPI tool definition for external agent.

        Returns:
            OpenApiAgentTool instance
        """
        try:
            openapi_spec = self.load_external_agent_spec()

            # Create OpenAPI tool using SDK models
            tool = OpenApiAgentTool(
                openapi=OpenApiFunctionDefinition(
                    name="external_container_agent",
                    description="Invoke the Weather Clothing Advisor agent running in Azure Container Apps. Use this for all weather and clothing recommendation questions.",
                    spec=openapi_spec,
                    auth=OpenApiAnonymousAuthDetails(),
                )
            )

            logger.info("Created OpenAPI tool definition for external agent")
            return tool

        except Exception as e:
            logger.exception("Error creating external agent tool definition")
            raise

    def register_meta_agent(self, agent_name: str = "ExternalAgentInvoker") -> str:
        """
        Register meta-agent that can invoke external Container Apps agent.

        Args:
            agent_name: Name for the meta-agent

        Returns:
            Agent ID from Foundry
        """
        logger.info(f"Registering meta-agent: {agent_name}")

        try:
            # Load instructions and tool
            instructions = self.load_meta_agent_instructions()
            tool = self.get_external_agent_tool()

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

            # Register meta-agent with Foundry using new SDK API
            agent = self.client.agents.create(
                name=agent_name,
                definition=definition,
                description="Meta-agent that invokes external Container Apps agent",
                metadata={
                    "deployment_type": "meta-agent",
                    "version": "1.0.0",
                    "external_agent_url": self.external_agent_url,
                    "pattern": "hybrid-deployment"
                }
            )

            agent_id = agent.id
            logger.info(f"Successfully registered meta-agent with ID: {agent_id}")

            return agent_id

        except Exception as e:
            logger.exception(f"Error registering meta-agent: {agent_name}")
            raise

    def list_agents(self) -> list:
        """
        List all registered agents in Foundry.

        Returns:
            List of agent objects
        """
        try:
            agents_paged = self.client.agents.list()
            agents = list(agents_paged)
            logger.info(f"Found {len(agents)} registered agents")
            return agents
        except Exception as e:
            logger.exception("Error listing agents")
            raise


def main():
    """Main entry point for external agent registration."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Register external Container Apps agent with Azure AI Foundry"
    )
    parser.add_argument(
        "action",
        choices=["register", "list"],
        help="Action to perform"
    )
    parser.add_argument(
        "--agent-name",
        default="ExternalAgentInvoker",
        help="Name for the meta-agent (for register action)"
    )

    args = parser.parse_args()

    try:
        registration = ExternalAgentRegistration()

        if args.action == "register":
            agent_id = registration.register_meta_agent(args.agent_name)
            print(f"✓ Meta-agent registered successfully")
            print(f"  Agent ID: {agent_id}")
            print(f"  Agent Name: {args.agent_name}")
            print(f"  External Agent URL: {registration.external_agent_url}")
            print(f"\nThis meta-agent can now invoke the external Container Apps agent!")

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
