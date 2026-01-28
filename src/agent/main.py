"""
Weather-Based Clothing Advisor Agent

Entry point for the agent server exposing the /responses API.
Works identically on Container Apps and Foundry Hosted deployments.

Usage:
    python -m agent.main [--port 8088] [--host 0.0.0.0]
"""

import argparse
import logging
import os

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_PORT = 8088


def main():
    """Start the Responses API server."""
    parser = argparse.ArgumentParser(
        description="Weather-Based Clothing Advisor Agent Server"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", DEFAULT_PORT)),
        help=f"Port to listen on (default: {DEFAULT_PORT})",
    )

    args = parser.parse_args()

    # Import and start server
    from agent.hosting.responses_server import ResponsesServer

    logger.info(f"Starting Weather Clothing Advisor on {args.host}:{args.port}")
    server = ResponsesServer()
    server.start(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
