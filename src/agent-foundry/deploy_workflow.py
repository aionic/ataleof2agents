"""
Workflow deployment script for Azure AI Foundry.

Deploys the Weather Clothing Advisor workflow using declarative YAML configuration
files (agent.yaml and workflow.yaml).
"""

import os
import sys
import json
import yaml
import logging
from typing import Dict, Any
from pathlib import Path

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


class WorkflowDeployment:
    """Handles deployment of Foundry workflow from YAML configuration."""

    def __init__(self):
        """Initialize workflow deployment."""
        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        self.weather_function_url = os.getenv("WEATHER_FUNCTION_URL")

        if not self.project_endpoint:
            raise ValueError("AZURE_AI_PROJECT_ENDPOINT environment variable is required")
        if not self.weather_function_url:
            raise ValueError("WEATHER_FUNCTION_URL environment variable is required")

        # Initialize Azure AI Project Client
        credential = DefaultAzureCredential()
        self.client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=credential
        )

        self.base_dir = Path(__file__).parent
        logger.info(f"Initialized Foundry client for project: {self.project_endpoint}")

    def load_yaml_with_env_vars(self, file_path: Path) -> Dict[str, Any]:
        """
        Load YAML file and substitute environment variables.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML with environment variables substituted
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple environment variable substitution: ${VAR_NAME} or ${VAR_NAME:default}
            import re

            def replace_env_var(match):
                var_expr = match.group(1)
                if ':' in var_expr:
                    var_name, default = var_expr.split(':', 1)
                    return os.getenv(var_name.strip(), default.strip())
                else:
                    var_name = var_expr.strip()
                    value = os.getenv(var_name)
                    if value is None:
                        logger.warning(f"Environment variable {var_name} not set")
                        return match.group(0)  # Return original if not found
                    return value

            content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)

            config = yaml.safe_load(content)
            logger.info(f"Loaded configuration from {file_path}")
            return config

        except FileNotFoundError:
            logger.error(f"Configuration file not found: {file_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}")
            raise

    def load_agent_instructions(self, instructions_file: str) -> str:
        """
        Load agent instructions from file specified in agent.yaml.

        Args:
            instructions_file: Relative path to instructions file

        Returns:
            Instructions content
        """
        instructions_path = self.base_dir / instructions_file

        try:
            with open(instructions_path, 'r', encoding='utf-8') as f:
                instructions = f.read()
            logger.info(f"Loaded agent instructions from {instructions_path}")
            return instructions
        except FileNotFoundError:
            logger.error(f"Instructions file not found: {instructions_path}")
            raise

    def deploy_workflow(self, workflow_name: str = None) -> str:
        """
        Deploy workflow to Azure AI Foundry using YAML configuration.

        Args:
            workflow_name: Optional custom workflow name (overrides YAML)

        Returns:
            Workflow ID from Foundry
        """
        logger.info("Loading workflow and agent configurations...")

        # Load workflow and agent configurations
        workflow_config = self.load_yaml_with_env_vars(self.base_dir / "workflow.yaml")
        agent_config = self.load_yaml_with_env_vars(self.base_dir / "agent.yaml")

        # Override workflow name if provided
        if workflow_name:
            workflow_config['name'] = workflow_name

        # Load agent instructions
        instructions_file = agent_config.get('instructions_file')
        if instructions_file:
            instructions = self.load_agent_instructions(instructions_file)
        else:
            logger.warning("No instructions_file specified in agent.yaml")
            instructions = "You are a helpful assistant."

        try:
            logger.info(f"Deploying workflow: {workflow_config['name']}")

            # Extract model configuration
            model_config = agent_config.get('model', {})
            model_deployment = model_config.get('deployment_name')

            if not model_deployment:
                raise ValueError("model.deployment_name not specified in agent.yaml")

            # Extract tool configurations
            tools = []
            for tool_config in agent_config.get('tools', []):
                tool_def = {
                    "type": "function",
                    "function": {
                        "name": tool_config['name'],
                        "description": tool_config['description'],
                        "parameters": tool_config['parameters']
                    }
                }

                # Add URL for HTTP-based tools
                if 'url' in tool_config:
                    tool_def['function']['url'] = tool_config['url']

                tools.append(tool_def)
                logger.info(f"  Registered tool: {tool_config['name']}")

            # Create agent with workflow configuration
            agent = self.client.agents.create_agent(
                name=agent_config['name'],
                instructions=instructions,
                model=model_deployment,
                tools=tools,
                metadata={
                    "workflow_name": workflow_config['name'],
                    "workflow_version": workflow_config.get('version', '1.0.0'),
                    "deployment_type": "foundry-workflow",
                    **agent_config.get('metadata', {})
                },
                # Apply additional settings from agent.yaml
                temperature=model_config.get('temperature', 0.7),
                top_p=model_config.get('top_p', 0.95)
            )

            agent_id = agent.id
            logger.info(f"✓ Workflow deployed successfully")
            logger.info(f"  Agent ID: {agent_id}")
            logger.info(f"  Workflow: {workflow_config['name']}")
            logger.info(f"  Agent: {agent_config['name']}")
            logger.info(f"  Tools: {len(tools)}")

            return agent_id

        except Exception as e:
            logger.exception(f"Error deploying workflow: {workflow_config['name']}")
            raise

    def update_workflow(self, agent_id: str) -> None:
        """
        Update an existing workflow deployment.

        Args:
            agent_id: ID of the agent to update
        """
        logger.info(f"Updating workflow: {agent_id}")

        # Load configurations
        agent_config = self.load_yaml_with_env_vars(self.base_dir / "agent.yaml")

        # Load instructions
        instructions_file = agent_config.get('instructions_file')
        if instructions_file:
            instructions = self.load_agent_instructions(instructions_file)
        else:
            instructions = None

        try:
            # Extract tools
            tools = []
            for tool_config in agent_config.get('tools', []):
                tool_def = {
                    "type": "function",
                    "function": {
                        "name": tool_config['name'],
                        "description": tool_config['description'],
                        "parameters": tool_config['parameters']
                    }
                }

                if 'url' in tool_config:
                    tool_def['function']['url'] = tool_config['url']

                tools.append(tool_def)

            self.client.agents.update_agent(
                agent_id=agent_id,
                instructions=instructions,
                tools=tools
            )

            logger.info(f"✓ Workflow updated successfully: {agent_id}")

        except Exception as e:
            logger.exception(f"Error updating workflow: {agent_id}")
            raise

    def delete_workflow(self, agent_id: str) -> None:
        """
        Delete a workflow deployment.

        Args:
            agent_id: ID of the agent/workflow to delete
        """
        logger.info(f"Deleting workflow: {agent_id}")

        try:
            self.client.agents.delete_agent(agent_id)
            logger.info(f"✓ Workflow deleted successfully: {agent_id}")
        except Exception as e:
            logger.exception(f"Error deleting workflow: {agent_id}")
            raise

    def list_workflows(self) -> list:
        """
        List all deployed workflows.

        Returns:
            List of workflow/agent objects
        """
        try:
            agents = self.client.agents.list_agents()
            workflows = [a for a in agents if a.metadata.get('deployment_type') == 'foundry-workflow']
            logger.info(f"Found {len(workflows)} deployed workflows")
            return workflows
        except Exception as e:
            logger.exception("Error listing workflows")
            raise

    def validate_configuration(self) -> bool:
        """
        Validate workflow and agent YAML configurations.

        Returns:
            True if valid, raises exception if invalid
        """
        logger.info("Validating workflow configuration...")

        try:
            # Load and validate YAML files
            workflow_config = self.load_yaml_with_env_vars(self.base_dir / "workflow.yaml")
            agent_config = self.load_yaml_with_env_vars(self.base_dir / "agent.yaml")

            # Validate required fields
            required_workflow_fields = ['name', 'description', 'workflow']
            for field in required_workflow_fields:
                if field not in workflow_config:
                    raise ValueError(f"Missing required field in workflow.yaml: {field}")

            required_agent_fields = ['name', 'description', 'model', 'tools']
            for field in required_agent_fields:
                if field not in agent_config:
                    raise ValueError(f"Missing required field in agent.yaml: {field}")

            # Validate instructions file exists
            instructions_file = agent_config.get('instructions_file')
            if instructions_file:
                instructions_path = self.base_dir / instructions_file
                if not instructions_path.exists():
                    raise ValueError(f"Instructions file not found: {instructions_path}")

            logger.info("✓ Configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"✗ Configuration validation failed: {e}")
            raise


def main():
    """Main entry point for workflow deployment."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Deploy Weather Clothing Advisor workflow to Azure AI Foundry"
    )
    parser.add_argument(
        "action",
        choices=["deploy", "update", "delete", "list", "validate"],
        help="Action to perform"
    )
    parser.add_argument("--agent-id", help="Agent ID (required for update/delete)")
    parser.add_argument("--workflow-name", help="Custom workflow name (for deploy action)")

    args = parser.parse_args()

    try:
        deployment = WorkflowDeployment()

        if args.action == "validate":
            deployment.validate_configuration()
            print("✓ Configuration is valid")

        elif args.action == "deploy":
            agent_id = deployment.deploy_workflow(args.workflow_name)
            print(f"\n✓ Workflow deployed successfully")
            print(f"  Agent ID: {agent_id}")
            print(f"\nNext steps:")
            print(f"  1. Test the workflow in Azure AI Foundry portal")
            print(f"  2. Use this agent ID in your applications")
            print(f"  3. Monitor telemetry in Application Insights")

        elif args.action == "update":
            if not args.agent_id:
                print("Error: --agent-id is required for update action")
                sys.exit(1)
            deployment.update_workflow(args.agent_id)
            print(f"✓ Workflow updated successfully: {args.agent_id}")

        elif args.action == "delete":
            if not args.agent_id:
                print("Error: --agent-id is required for delete action")
                sys.exit(1)
            deployment.delete_workflow(args.agent_id)
            print(f"✓ Workflow deleted successfully: {args.agent_id}")

        elif args.action == "list":
            workflows = deployment.list_workflows()
            print(f"\nDeployed Workflows ({len(workflows)}):")
            for workflow in workflows:
                print(f"  - {workflow.name} (ID: {workflow.id})")
                print(f"    Version: {workflow.metadata.get('workflow_version', 'N/A')}")
                print(f"    Workflow: {workflow.metadata.get('workflow_name', 'N/A')}")

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
