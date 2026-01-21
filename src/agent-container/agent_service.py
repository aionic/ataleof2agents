"""
Agent service implementing the Weather-Based Clothing Advisor using Microsoft Agent Framework.

Uses the Microsoft Agent Framework (https://github.com/microsoft/agent-framework)
for agent lifecycle, tool registration, and message processing.
"""

import os
import logging
import time
import uuid
from typing import Dict, Any, Optional
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from agent_framework import ChatAgent
    from agent_framework.azure import AzureOpenAIChatClient
    from azure.identity import DefaultAzureCredential
except ImportError:
    # Fallback for development without SDK installed
    logging.warning("Microsoft Agent Framework SDK not installed. Using mock implementations.")
    ChatAgent = None
    AzureOpenAIChatClient = None
    DefaultAzureCredential = None

from shared.constants import SC_001_RESPONSE_TIME_SECONDS

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing the Weather-Based Clothing Advisor agent."""

    def __init__(self):
        """Initialize agent service with tools and instructions."""
        # Get weather API URL
        self.weather_api_url = os.getenv("WEATHER_API_URL")
        if not self.weather_api_url:
            raise ValueError("WEATHER_API_URL environment variable is required")

        # Load agent instructions from contracts
        self.instructions = self._load_agent_instructions()

        # Initialize sessions storage
        self.sessions: Dict[str, Any] = {}

        # Initialize agent (or mock for development)
        self.agent = self._initialize_agent()

        logger.info("Agent service initialized successfully")

    def _load_agent_instructions(self) -> str:
        """
        Load agent instructions from contracts/agent-prompts.md.

        Returns:
            Agent instruction text
        """
        # Construct path to agent-prompts.md
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
            logger.warning(f"Agent prompts file not found: {prompts_file}. Using fallback instructions.")
            return self._get_fallback_instructions()

    def _get_fallback_instructions(self) -> str:
        """Provide fallback instructions if file not found."""
        return """You are a weather-based clothing advisor assistant.

When a user provides a zip code:
1. Use the get_weather tool to retrieve current weather conditions
2. Analyze the weather data (temperature, conditions, wind, precipitation)
3. Provide 3-5 specific clothing recommendations based on the weather
4. Organize recommendations by category (outerwear, layers, accessories, footwear)
5. Explain why each item is recommended

Be helpful, concise, and practical in your recommendations."""

    def _initialize_agent(self) -> Optional[Any]:
        """
        Initialize the Microsoft Agent Framework ChatAgent with tools.

        Returns:
            ChatAgent instance or None if SDK not available
        """
        if ChatAgent is None or AzureOpenAIChatClient is None:
            logger.warning("ChatAgent not available - using mock mode")
            return None

        try:
            # Define get_weather tool as a function
            # Agent Framework uses Python functions with type annotations
            from typing import Annotated
            from pydantic import Field

            def get_weather(
                zip_code: Annotated[str, Field(description="5-digit US zip code")]
            ) -> str:
                """Retrieve current weather data for a US zip code."""
                result = self._call_weather_function(zip_code)
                # Return JSON string for the agent to parse
                return json.dumps(result)

            # Store the tool function
            self._get_weather_tool = get_weather

            # Get Azure AI Foundry Models endpoint
            # Use Foundry resource endpoint (not project endpoint) with Agent Framework
            azure_endpoint = os.getenv("AZURE_FOUNDRY_ENDPOINT")
            deployment_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4")

            if not azure_endpoint:
                raise ValueError("AZURE_FOUNDRY_ENDPOINT environment variable is required")

            logger.info(f"Using endpoint: {azure_endpoint}")
            logger.info(f"Using deployment: {deployment_name}")

            # Create chat client
            chat_client = AzureOpenAIChatClient(
                endpoint=azure_endpoint,
                deployment_name=deployment_name,
                credential=DefaultAzureCredential()
            )

            # Create agent with tools and instructions
            agent = ChatAgent(
                name="WeatherClothingAdvisor",
                instructions=self.instructions,
                chat_client=chat_client,
                tools=[get_weather]
            )

            logger.info("ChatAgent initialized with get_weather tool using Microsoft Agent Framework")
            return agent

        except Exception as e:
            logger.exception("Error initializing ChatAgent")
            raise

    def _call_weather_function(self, zip_code: str) -> Dict[str, Any]:
        """
        Call the weather API container to get current conditions.

        Args:
            zip_code: 5-digit US zip code

        Returns:
            Weather data or error response
        """
        import requests

        try:
            logger.info(f"Getting weather for zip code: {zip_code}")

            # Call weather API container
            response = requests.get(
                f"{self.weather_api_url}/api/weather",
                params={"zip_code": zip_code},
                timeout=SC_001_RESPONSE_TIME_SECONDS
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Weather data retrieved for {result.get('location', 'unknown location')}")
            return result

        except requests.exceptions.Timeout:
            logger.error(f"Weather API timeout for zip code: {zip_code}")
            return {
                "error": {
                    "error_code": "TIMEOUT",
                    "message": "Weather request timed out",
                    "details": f"Request exceeded {SC_001_RESPONSE_TIME_SECONDS} seconds"
                }
            }
        except Exception as e:
            logger.exception(f"Error calling weather API for zip code: {zip_code}")
            return {
                "error": {
                    "error_code": "API_ERROR",
                    "message": "Error calling weather API",
                    "details": str(e)
                }
            }

    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the agent.

        Args:
            message: User's message
            session_id: Optional session ID for conversation continuity

        Returns:
            Dict containing response, session_id, and metadata
        """
        start_time = time.time()

        # Generate or retrieve session ID
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Created new session: {session_id}")

        try:
            if self.agent is None:
                # Mock response for development
                response_text = self._generate_mock_response(message)
            else:
                # Get or create session conversation history
                conversation = self.sessions.get(session_id, [])

                # Add user message
                conversation.append({"role": "user", "content": message})

                # Process with agent using Agent Framework's run method
                response_text = await self.agent.run(message)

                # Add assistant response to history
                conversation.append({"role": "assistant", "content": response_text})

                # Store updated conversation
                self.sessions[session_id] = conversation

            # Calculate response time
            response_time = time.time() - start_time
            logger.info(f"Response time: {response_time:.2f}s for session {session_id}")

            # Log warning if exceeding SC-001 threshold
            if response_time > SC_001_RESPONSE_TIME_SECONDS:
                logger.warning(
                    f"Response time {response_time:.2f}s exceeds SC-001 threshold "
                    f"of {SC_001_RESPONSE_TIME_SECONDS}s"
                )

            return {
                "response": response_text,
                "session_id": session_id,
                "metadata": {
                    "response_time": response_time,
                    "within_threshold": response_time <= SC_001_RESPONSE_TIME_SECONDS
                }
            }

        except Exception as e:
            logger.exception(f"Error processing message for session {session_id}")
            raise

    def _generate_mock_response(self, message: str) -> str:
        """Generate mock response for development without SDK."""
        return f"Mock response to: {message}\n\nNote: Azure Agent Framework SDK not installed."

    async def process_message_simple(self, message: str, session_id: str) -> str:
        """
        Process message and return simple text response (for workflow orchestrator).

        Args:
            message: User's message
            session_id: Session ID

        Returns:
            Response text string
        """
        if self.agent is None:
            return self._generate_mock_response(message)

        try:
            # Get or create session conversation history
            conversation = self.sessions.get(session_id, [])

            # Add user message
            conversation.append({"role": "user", "content": message})

            # Process with agent - now properly async
            agent_response = await self.agent.run(message)
            
            # Extract text from AgentResponse object
            response_text = agent_response.text if hasattr(agent_response, 'text') else str(agent_response)

            # Add assistant response to history
            conversation.append({"role": "assistant", "content": response_text})

            # Store updated conversation
            self.sessions[session_id] = conversation

            return response_text

        except Exception as e:
            logger.exception(f"Error in simple message processing: {e}")
            return "I encountered an error processing your request. Please try again."

    def reset_session(self, session_id: str):
        """Reset a conversation session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session {session_id} reset")
        else:
            logger.warning(f"Session {session_id} not found")
