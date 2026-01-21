"""
Telemetry configuration for Container Apps deployment.

Configures Azure Application Insights with OpenTelemetry for
comprehensive observability and monitoring.
"""

import os
import logging
from typing import Dict, Any

try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource
except ImportError:
    logging.warning("Azure Monitor OpenTelemetry not installed. Telemetry disabled.")
    configure_azure_monitor = None
    trace = None

logger = logging.getLogger(__name__)


class TelemetryService:
    """Manages Application Insights telemetry for Container Apps deployment."""

    def __init__(self):
        """Initialize telemetry service with Application Insights."""
        self.enabled = False
        self.tracer = None

        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

        if not connection_string:
            logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not set. Telemetry disabled.")
            return

        if configure_azure_monitor is None:
            logger.warning("Azure Monitor OpenTelemetry SDK not available. Telemetry disabled.")
            return

        try:
            # Configure Azure Monitor with custom resource attributes
            configure_azure_monitor(
                connection_string=connection_string,
                resource=Resource.create({
                    "service.name": "weather-clothing-advisor",
                    "service.version": "1.0.0",
                    "deployment.type": "container-app",
                    "deployment.environment": os.getenv("ENVIRONMENT", "production")
                })
            )

            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            self.enabled = True

            logger.info("Application Insights telemetry configured successfully")

        except Exception as e:
            logger.exception("Error configuring Application Insights")
            self.enabled = False

    def track_request(self, name: str, properties: Dict[str, Any] = None):
        """
        Track a request with custom properties.

        Args:
            name: Name of the request/operation
            properties: Additional properties to track
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

    def track_event(self, name: str, properties: Dict[str, Any] = None):
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

    def track_exception(self, exception: Exception, properties: Dict[str, Any] = None):
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
        properties: Dict[str, Any] = None
    ):
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


# Global telemetry service instance
_telemetry_service = None


def get_telemetry_service() -> TelemetryService:
    """Get or create the global telemetry service instance."""
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService()
    return _telemetry_service
