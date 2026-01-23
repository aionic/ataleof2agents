"""
Telemetry configuration for agent deployment.

Configures Azure Application Insights with OpenTelemetry for
comprehensive observability and monitoring. Works identically
in Container Apps and Foundry Hosted deployments.
"""

import logging
import os
from typing import Any, Dict, Optional

try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    logging.warning("Azure Monitor OpenTelemetry not installed. Telemetry disabled.")
    configure_azure_monitor = None
    trace = None
    Resource = None
    TracerProvider = None
    OPENTELEMETRY_AVAILABLE = False

logger = logging.getLogger(__name__)


class TelemetryService:
    """Manages Application Insights telemetry for agent deployment."""

    def __init__(self, service_name: str = "weather-clothing-advisor"):
        """
        Initialize telemetry service with Application Insights.

        Args:
            service_name: Name of the service for telemetry tagging
        """
        self.enabled = False
        self.tracer = None
        self.service_name = service_name

        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

        if not connection_string:
            logger.warning(
                "APPLICATIONINSIGHTS_CONNECTION_STRING not set. Telemetry disabled."
            )
            return

        if not OPENTELEMETRY_AVAILABLE:
            logger.warning(
                "Azure Monitor OpenTelemetry SDK not available. Telemetry disabled."
            )
            return

        try:
            # Determine deployment type from environment
            deployment_type = os.getenv("DEPLOYMENT_TYPE", "unknown")
            if os.getenv("FOUNDRY_PROJECT_URL"):
                deployment_type = "foundry-hosted"
            elif os.getenv("CONTAINER_APP_NAME"):
                deployment_type = "container-app"

            # Configure Azure Monitor with custom resource attributes
            configure_azure_monitor(
                connection_string=connection_string,
                resource=Resource.create(
                    {
                        "service.name": service_name,
                        "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
                        "deployment.type": deployment_type,
                        "deployment.environment": os.getenv(
                            "ENVIRONMENT", "production"
                        ),
                    }
                ),
            )

            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            self.enabled = True

            logger.info(
                f"Application Insights telemetry configured successfully "
                f"(deployment={deployment_type})"
            )

        except Exception as e:
            logger.exception("Error configuring Application Insights")
            self.enabled = False

    def track_request(
        self, name: str, properties: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Track a request with custom properties.

        Args:
            name: Name of the request/operation
            properties: Additional properties to track

        Returns:
            Span object if telemetry is enabled, None otherwise
        """
        if not self.enabled or not self.tracer:
            return None

        try:
            span = self.tracer.start_span(name)

            # Add custom properties as span attributes
            if properties:
                for key, value in properties.items():
                    span.set_attribute(key, str(value))

            return span

        except Exception as e:
            logger.exception(f"Error tracking request: {name}")
            return None

    def track_event(
        self, name: str, properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track a custom event.

        Args:
            name: Name of the event
            properties: Additional properties to track
        """
        if not self.enabled or not self.tracer:
            return

        try:
            with self.tracer.start_as_current_span(name) as span:
                span.set_attribute("event.type", "custom")

                if properties:
                    for key, value in properties.items():
                        span.set_attribute(key, str(value))

            logger.info(f"Tracked event: {name}")

        except Exception as e:
            logger.exception(f"Error tracking event: {name}")

    def track_exception(
        self, exception: Exception, properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track an exception with context.

        Args:
            exception: The exception to track
            properties: Additional context properties
        """
        if not self.enabled or not self.tracer:
            return

        try:
            with self.tracer.start_as_current_span("exception") as span:
                span.set_attribute("exception.type", type(exception).__name__)
                span.set_attribute("exception.message", str(exception))
                span.record_exception(exception)

                if properties:
                    for key, value in properties.items():
                        span.set_attribute(key, str(value))

            logger.error(f"Tracked exception: {type(exception).__name__}")

        except Exception as e:
            logger.exception("Error tracking exception")

    def track_dependency(
        self,
        name: str,
        dependency_type: str,
        target: str,
        success: bool,
        duration_ms: float,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track a dependency call (e.g., API, database).

        Args:
            name: Name of the dependency operation
            dependency_type: Type of dependency (HTTP, Database, etc.)
            target: Target of the dependency call
            success: Whether the call succeeded
            duration_ms: Duration in milliseconds
            properties: Additional properties
        """
        if not self.enabled or not self.tracer:
            return

        try:
            with self.tracer.start_as_current_span(name) as span:
                span.set_attribute("dependency.type", dependency_type)
                span.set_attribute("dependency.target", target)
                span.set_attribute("dependency.success", success)
                span.set_attribute("dependency.duration_ms", duration_ms)

                if properties:
                    for key, value in properties.items():
                        span.set_attribute(key, str(value))

            logger.debug(f"Tracked dependency: {name} ({dependency_type})")

        except Exception as e:
            logger.exception(f"Error tracking dependency: {name}")

    def track_workflow_step(
        self,
        step_id: str,
        step_type: str,
        success: bool,
        duration_ms: float,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track a workflow step execution.

        Args:
            step_id: Identifier for the workflow step
            step_type: Type of step (agent_reasoning, tool_call, agent_response)
            success: Whether the step succeeded
            duration_ms: Duration in milliseconds
            properties: Additional properties
        """
        if not self.enabled or not self.tracer:
            return

        try:
            with self.tracer.start_as_current_span(f"workflow.step.{step_id}") as span:
                span.set_attribute("workflow.step_id", step_id)
                span.set_attribute("workflow.step_type", step_type)
                span.set_attribute("workflow.success", success)
                span.set_attribute("workflow.duration_ms", duration_ms)

                if properties:
                    for key, value in properties.items():
                        span.set_attribute(key, str(value))

            logger.debug(f"Tracked workflow step: {step_id} ({step_type})")

        except Exception as e:
            logger.exception(f"Error tracking workflow step: {step_id}")


# Global telemetry service instance
_telemetry_service: Optional[TelemetryService] = None


def get_telemetry_service() -> TelemetryService:
    """Get or create the global telemetry service instance."""
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService()
    return _telemetry_service


def reset_telemetry_service() -> None:
    """Reset the global telemetry service (for testing)."""
    global _telemetry_service
    _telemetry_service = None
