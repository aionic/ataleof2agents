"""
Responses API server for Foundry Hosted compatibility.

This module provides the /responses endpoint that matches the Foundry
Hosted Agent protocol, allowing the same agent code to run in both
Container Apps and Foundry Hosted deployments.
"""

import logging
import os
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default port for Foundry protocol
FOUNDRY_PORT = 8088


class ResponsesServer:
    """
    HTTP server implementing the Foundry Responses API protocol.

    Wraps the AgentService to expose it via the /responses endpoint
    expected by Foundry Hosted Agents.
    """

    def __init__(self, agent_service: Any = None):
        """
        Initialize the responses server.

        Args:
            agent_service: Optional AgentService instance. If not provided,
                         one will be created when start() is called.
        """
        self._agent_service = agent_service
        self._app = None
        self._conversations: Dict[str, List[Dict[str, str]]] = {}

    async def handle_responses(
        self,
        messages: List[Dict[str, str]],
        conversation_id: Optional[str] = None,
        stream: bool = False,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle a /responses API request.

        Args:
            messages: List of conversation messages
            conversation_id: Optional conversation ID for continuity
            stream: Whether to stream the response
            model: Optional model override

        Returns:
            Response dictionary with content and metadata
        """
        # Import here to avoid circular imports
        from agent.core.agent_service import AgentService

        # Ensure agent service is initialized
        if self._agent_service is None:
            self._agent_service = AgentService()

        # Generate or retrieve conversation ID
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # Get conversation history
        history = self._conversations.get(conversation_id, [])

        # Add new messages to history
        for msg in messages:
            if msg not in history:
                history.append(msg)

        # Get the latest user message
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return {
                "error": {
                    "code": "invalid_request",
                    "message": "No user message found in request",
                }
            }

        try:
            # Process through agent service
            result = await self._agent_service.process_message(
                message=user_message, session_id=conversation_id
            )

            # Update conversation history
            history.append({"role": "assistant", "content": result["response"]})
            self._conversations[conversation_id] = history

            # Return Foundry-compatible response format
            return {
                "id": str(uuid.uuid4()),
                "object": "response",
                "created": int(uuid.uuid1().time // 10000000 - 12219292800),
                "model": model or os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4"),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": result["response"],
                        },
                        "finish_reason": "stop",
                    }
                ],
                "conversation_id": conversation_id,
                "usage": {
                    "prompt_tokens": 0,  # Would need token counting
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "metadata": result.get("metadata", {}),
            }

        except Exception as e:
            logger.exception(f"Error processing responses request: {e}")
            return {
                "error": {
                    "code": "internal_error",
                    "message": str(e),
                }
            }

    async def handle_responses_stream(
        self,
        messages: List[Dict[str, str]],
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Handle a streaming /responses API request.

        Args:
            messages: List of conversation messages
            conversation_id: Optional conversation ID
            model: Optional model override

        Yields:
            Server-sent event strings
        """
        # For now, get full response and simulate streaming
        result = await self.handle_responses(
            messages=messages,
            conversation_id=conversation_id,
            stream=False,
            model=model,
        )

        if "error" in result:
            yield f"data: {result}\n\n"
            return

        # Simulate streaming by yielding character by character
        content = result["choices"][0]["message"]["content"]
        response_id = result["id"]
        model_name = result["model"]

        # Start event
        yield f"data: {{'id': '{response_id}', 'object': 'response.chunk', 'model': '{model_name}', 'choices': [{{'index': 0, 'delta': {{'role': 'assistant'}}, 'finish_reason': null}}]}}\n\n"

        # Content chunks (simplified - in production would chunk better)
        for char in content:
            chunk = {
                "id": response_id,
                "object": "response.chunk",
                "model": model_name,
                "choices": [
                    {"index": 0, "delta": {"content": char}, "finish_reason": None}
                ],
            }
            yield f"data: {chunk}\n\n"

        # End event
        yield f"data: {{'id': '{response_id}', 'object': 'response.chunk', 'model': '{model_name}', 'choices': [{{'index': 0, 'delta': {{}}, 'finish_reason': 'stop'}}]}}\n\n"
        yield "data: [DONE]\n\n"

    def create_app(self):
        """
        Create a FastAPI application with the /responses endpoint.

        Returns:
            FastAPI application instance
        """
        try:
            from fastapi import FastAPI, Request
            from fastapi.responses import JSONResponse, StreamingResponse
        except ImportError:
            raise ImportError(
                "FastAPI is required for ResponsesServer. "
                "Install with: pip install fastapi uvicorn"
            )

        app = FastAPI(
            title="Weather Clothing Advisor Agent",
            description="Foundry Responses API compatible agent server",
            version="1.0.0",
        )

        @app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy"}

        @app.get("/ready")
        async def ready():
            """Readiness check endpoint."""
            return {"status": "ready"}

        @app.post("/responses")
        async def responses(request: Request):
            """
            Handle Foundry Responses API requests.

            Expects JSON body with:
            - input: List of conversation messages (Foundry v6 protocol)
            - messages: Legacy format (also supported)
            - conversation_id: Optional conversation ID
            - stream: Optional boolean for streaming
            - model: Optional model override
            """
            try:
                body = await request.json()
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content={"error": {"code": "invalid_json", "message": "Invalid JSON body"}},
                )

            # Support both "input" (Foundry v6) and "messages" (legacy) formats
            messages = body.get("input") or body.get("messages", [])

            # Handle nested format: {"input": {"messages": [...]}}
            if isinstance(messages, dict) and "messages" in messages:
                messages = messages["messages"]

            # Handle string input (simple message)
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]

            conversation_id = body.get("conversation_id") or body.get("conversation")
            stream = body.get("stream", False)
            model = body.get("model")

            if stream:
                return StreamingResponse(
                    self.handle_responses_stream(
                        messages=messages,
                        conversation_id=conversation_id,
                        model=model,
                    ),
                    media_type="text/event-stream",
                )

            result = await self.handle_responses(
                messages=messages,
                conversation_id=conversation_id,
                stream=False,
                model=model,
            )

            if "error" in result:
                return JSONResponse(status_code=500, content=result)

            return JSONResponse(content=result)

        self._app = app
        return app

    def start(self, host: str = "0.0.0.0", port: int = FOUNDRY_PORT):
        """
        Start the responses server.

        Args:
            host: Host to bind to
            port: Port to listen on (default 8088 for Foundry)
        """
        try:
            import uvicorn
        except ImportError:
            raise ImportError(
                "uvicorn is required to start the server. "
                "Install with: pip install uvicorn"
            )

        app = self.create_app()
        logger.info(f"Starting Responses API server on {host}:{port}")
        uvicorn.run(app, host=host, port=port)


def create_responses_server(agent_service: Any = None) -> ResponsesServer:
    """
    Factory function to create a ResponsesServer instance.

    Args:
        agent_service: Optional AgentService instance

    Returns:
        Configured ResponsesServer instance
    """
    return ResponsesServer(agent_service)


# Entry point for running as a module
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start the Responses API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument(
        "--port", type=int, default=FOUNDRY_PORT, help="Port to listen on"
    )
    args = parser.parse_args()

    server = ResponsesServer()
    server.start(host=args.host, port=args.port)
