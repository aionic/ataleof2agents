"""
Workflow orchestrator for Container Apps deployment.

Implements the workflow pattern defined in workflow.yaml with explicit step execution,
telemetry tracking, and error handling.
"""

import os
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from enum import Enum
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.constants import SC_001_RESPONSE_TIME_SECONDS

logger = logging.getLogger(__name__)


class WorkflowStepType(Enum):
    """Types of workflow steps."""
    AGENT_REASONING = "agent_reasoning"
    TOOL_CALL = "tool_call"
    AGENT_RESPONSE = "agent_response"


class WorkflowStep:
    """Represents a single step in the workflow."""

    def __init__(
        self,
        step_id: str,
        description: str,
        step_type: WorkflowStepType,
        depends_on: Optional[str] = None
    ):
        self.step_id = step_id
        self.description = description
        self.step_type = step_type
        self.depends_on = depends_on
        self.output = None
        self.duration = 0
        self.success = False
        self.error = None


class WorkflowOrchestrator:
    """
    Orchestrates the weather clothing advisor workflow.

    Implements the 4-step workflow pattern:
    1. Parse user input (extract zip code and intent)
    2. Get weather data (call weather function tool)
    3. Generate recommendations (AI reasoning)
    4. Format response (conversational output)
    """

    def __init__(self, agent_service):
        """
        Initialize workflow orchestrator.

        Args:
            agent_service: AgentService instance with agent and tools
        """
        self.agent_service = agent_service
        self.steps: List[WorkflowStep] = []
        self.workflow_context: Dict[str, Any] = {}

        logger.info("Workflow orchestrator initialized")

    async def execute_workflow(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete workflow for a user message.

        Args:
            message: User's message
            session_id: Optional session ID for conversation continuity

        Returns:
            Dict containing workflow execution results
        """
        workflow_start = time.time()

        # Generate or retrieve session ID
        if not session_id:
            session_id = str(uuid.uuid4())

        # Initialize workflow context
        self.workflow_context = {
            "message": message,
            "session_id": session_id,
            "workflow_id": str(uuid.uuid4()),
            "start_time": workflow_start
        }

        # Initialize workflow steps
        self.steps = [
            WorkflowStep("parse_user_input", "Parse user message", WorkflowStepType.AGENT_REASONING),
            WorkflowStep("get_weather_data", "Call weather function", WorkflowStepType.TOOL_CALL, "parse_user_input"),
            WorkflowStep("generate_recommendations", "Generate recommendations", WorkflowStepType.AGENT_REASONING, "get_weather_data"),
            WorkflowStep("format_response", "Format final response", WorkflowStepType.AGENT_RESPONSE, "generate_recommendations")
        ]

        logger.info(f"Starting workflow execution: {self.workflow_context['workflow_id']}")

        try:
            # Execute workflow steps sequentially
            for step in self.steps:
                await self._execute_step(step)

                # Check if step failed and handle error
                if not step.success:
                    return self._handle_workflow_error(step)

            # Workflow completed successfully
            workflow_duration = time.time() - workflow_start

            # Get final response from last step
            final_response = self.steps[-1].output

            # Log performance warning if needed
            if workflow_duration > SC_001_RESPONSE_TIME_SECONDS:
                logger.warning(
                    f"Workflow duration {workflow_duration:.2f}s exceeds SC-001 threshold "
                    f"of {SC_001_RESPONSE_TIME_SECONDS}s"
                )

            logger.info(f"Workflow completed successfully in {workflow_duration:.2f}s")

            return {
                "response": final_response,
                "session_id": session_id,
                "metadata": {
                    "workflow_id": self.workflow_context["workflow_id"],
                    "workflow_duration": workflow_duration,
                    "steps_executed": len(self.steps),
                    "within_threshold": workflow_duration <= SC_001_RESPONSE_TIME_SECONDS,
                    "step_durations": {step.step_id: step.duration for step in self.steps}
                }
            }

        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "session_id": session_id,
                "metadata": {
                    "workflow_id": self.workflow_context["workflow_id"],
                    "error": str(e),
                    "failed_step": self._get_current_step_id()
                }
            }

    async def _execute_step(self, step: WorkflowStep):
        """
        Execute a single workflow step.

        Args:
            step: WorkflowStep to execute
        """
        step_start = time.time()
        logger.info(f"Executing workflow step: {step.step_id} - {step.description}")

        try:
            # Check dependencies
            if step.depends_on:
                prev_step = self._get_step(step.depends_on)
                if not prev_step or not prev_step.success:
                    raise Exception(f"Dependency step {step.depends_on} failed or not found")

            # Execute step based on type
            if step.step_type == WorkflowStepType.AGENT_REASONING:
                step.output = self._execute_agent_reasoning(step)
            elif step.step_type == WorkflowStepType.TOOL_CALL:
                step.output = self._execute_tool_call(step)
            elif step.step_type == WorkflowStepType.AGENT_RESPONSE:
                step.output = await self._execute_agent_response(step)

            step.success = True
            step.duration = time.time() - step_start

            logger.info(f"Step {step.step_id} completed in {step.duration:.2f}s")

        except Exception as e:
            step.success = False
            step.error = str(e)
            step.duration = time.time() - step_start
            logger.error(f"Step {step.step_id} failed: {e}")

    def _execute_agent_reasoning(self, step: WorkflowStep) -> Any:
        """Execute agent reasoning step."""
        if step.step_id == "parse_user_input":
            # Extract zip code from message (simple pattern matching for POC)
            import re
            message = self.workflow_context["message"]
            zip_match = re.search(r'\b\d{5}\b', message)

            if zip_match:
                zip_code = zip_match.group(0)
                logger.info(f"Extracted zip code: {zip_code}")
                return {"zip_code": zip_code, "has_zip_code": True}
            else:
                logger.warning("No zip code found in message")
                return {"has_zip_code": False}

        elif step.step_id == "generate_recommendations":
            # This would normally call the agent to generate recommendations
            # For now, we'll let the full agent call handle it
            weather_step = self._get_step("get_weather_data")
            return weather_step.output

        return None

    def _execute_tool_call(self, step: WorkflowStep) -> Any:
        """Execute tool call step (get_weather)."""
        if step.step_id == "get_weather_data":
            parse_step = self._get_step("parse_user_input")

            if not parse_step.output.get("has_zip_code"):
                raise Exception("No zip code found in user message")

            zip_code = parse_step.output["zip_code"]

            # Call weather function via agent service
            weather_data = self.agent_service._call_weather_function(zip_code)

            if "error" in weather_data:
                raise Exception(f"Weather function error: {weather_data['error']}")

            return weather_data

        return None

    async def _execute_agent_response(self, step: WorkflowStep) -> str:
        """Execute final agent response step."""
        if step.step_id == "format_response":
            # Get the full agent response
            message = self.workflow_context["message"]
            session_id = self.workflow_context["session_id"]

            # Call agent service to get final formatted response
            # This includes the full conversation with tool results
            response = await self.agent_service.process_message_simple(message, session_id)
            return response

        return ""

    def _get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a workflow step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def _get_current_step_id(self) -> str:
        """Get ID of currently executing step."""
        for step in self.steps:
            if not step.success and step.error is None:
                return step.step_id
        return "unknown"

    def _handle_workflow_error(self, failed_step: WorkflowStep) -> Dict[str, Any]:
        """Handle workflow error with graceful degradation."""
        error_message = failed_step.error or "Unknown error"

        # Determine appropriate fallback message
        if "zip code" in error_message.lower():
            response = "I couldn't find a valid zip code in your message. Please provide a 5-digit US zip code."
        elif "timeout" in error_message.lower():
            response = "The weather service is taking too long to respond. Please try again in a moment."
        elif "network" in error_message.lower():
            response = "I'm having trouble connecting to the weather service. Please check your connection and try again."
        else:
            response = "I encountered an error processing your request. Please try again."

        return {
            "response": response,
            "session_id": self.workflow_context["session_id"],
            "metadata": {
                "workflow_id": self.workflow_context["workflow_id"],
                "error": error_message,
                "failed_step": failed_step.step_id
            }
        }
