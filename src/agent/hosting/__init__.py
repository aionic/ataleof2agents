"""
Hosting adapters for different deployment targets.

This module contains the Responses API server implementation
for Foundry Hosted deployment compatibility.
"""

from agent.hosting.responses_server import (
    FOUNDRY_PORT,
    ResponsesServer,
    create_responses_server,
)

__all__ = [
    "ResponsesServer",
    "create_responses_server",
    "FOUNDRY_PORT",
]
