"""
Unified entry point for the Weather-Based Clothing Advisor agent.

This module provides a single entry point that works for both
Container Apps and Foundry Hosted deployments.

Usage:
    # Run as Responses API server (Foundry Hosted compatible)
    python -m agent.main --mode responses --port 8088

    # Run as legacy API server (Container Apps compatible)
    python -m agent.main --mode legacy --port 8000

    # Run interactively for testing
    python -m agent.main --mode interactive
"""

import argparse
import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_responses_server(host: str, port: int):
    """Run the Foundry-compatible Responses API server."""
    from agent.hosting.responses_server import ResponsesServer

    logger.info(f"Starting Responses API server on {host}:{port}")
    server = ResponsesServer()
    server.start(host=host, port=port)


def run_legacy_server(host: str, port: int):
    """Run the legacy Container Apps compatible server."""
    try:
        import uvicorn
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
    except ImportError:
        logger.error("FastAPI and uvicorn are required. Install with: pip install fastapi uvicorn")
        sys.exit(1)

    from agent.core.agent_service import AgentService

    app = FastAPI(
        title="Weather Clothing Advisor Agent",
        description="Legacy API compatible server",
        version="1.0.0",
    )

    agent_service = None

    @app.on_event("startup")
    async def startup():
        nonlocal agent_service
        agent_service = AgentService()
        logger.info("Agent service initialized")

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/ready")
    async def ready():
        return {"status": "ready"}

    @app.post("/chat")
    async def chat(request: Request):
        """Legacy chat endpoint for Container Apps."""
        try:
            body = await request.json()
            message = body.get("message", "")
            session_id = body.get("session_id")

            if not message:
                return JSONResponse(
                    status_code=400,
                    content={"error": "message is required"},
                )

            result = await agent_service.process_message(
                message=message,
                session_id=session_id,
            )
            return JSONResponse(content=result)

        except Exception as e:
            logger.exception("Error processing chat request")
            return JSONResponse(
                status_code=500,
                content={"error": str(e)},
            )

    logger.info(f"Starting legacy server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


async def run_interactive():
    """Run interactive mode for testing."""
    from agent.core.agent_service import AgentService

    logger.info("Starting interactive mode...")

    try:
        agent_service = AgentService()
    except ValueError as e:
        logger.error(f"Failed to initialize agent: {e}")
        logger.info("Set WEATHER_API_URL environment variable and try again.")
        return

    session_id = None

    print("\n" + "=" * 60)
    print("Weather-Based Clothing Advisor - Interactive Mode")
    print("=" * 60)
    print("Enter a US zip code to get clothing recommendations.")
    print("Type 'quit' or 'exit' to stop.")
    print("Type 'reset' to start a new conversation.")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                break

            if user_input.lower() == "reset":
                if session_id:
                    agent_service.reset_session(session_id)
                session_id = None
                print("Conversation reset.\n")
                continue

            # Process message
            result = await agent_service.process_message(
                message=user_input,
                session_id=session_id,
            )

            session_id = result.get("session_id")
            response = result.get("response", "No response received.")
            metadata = result.get("metadata", {})

            print(f"\nAdvisor: {response}")

            if metadata.get("response_time"):
                print(f"(Response time: {metadata['response_time']:.2f}s)\n")
            else:
                print()

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            logger.exception("Error processing input")
            print(f"Error: {e}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Weather-Based Clothing Advisor Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  responses   - Run Foundry-compatible Responses API server (default)
  legacy      - Run legacy Container Apps compatible server
  interactive - Run interactive mode for testing

Examples:
  python -m agent.main --mode responses --port 8088
  python -m agent.main --mode legacy --port 8000
  python -m agent.main --mode interactive
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["responses", "legacy", "interactive"],
        default="responses",
        help="Server mode (default: responses)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to listen on (default: 8088 for responses, 8000 for legacy)",
    )

    args = parser.parse_args()

    # Determine port
    if args.port is None:
        args.port = 8088 if args.mode == "responses" else 8000

    # Run appropriate mode
    if args.mode == "responses":
        run_responses_server(args.host, args.port)
    elif args.mode == "legacy":
        run_legacy_server(args.host, args.port)
    elif args.mode == "interactive":
        asyncio.run(run_interactive())


if __name__ == "__main__":
    main()
