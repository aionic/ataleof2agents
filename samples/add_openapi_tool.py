#!/usr/bin/env python3
"""
Example: Add OpenAPI tool to agent.

Shows how to integrate an external API using OpenAPI specification.
Uses the GA SDK v2.0.0+ API with conversations/responses pattern.
"""

import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    OpenApiAgentTool,
    OpenApiFunctionDefinition,
    OpenApiAnonymousAuthDetails,
)
from azure.identity import DefaultAzureCredential

load_dotenv()

# External API OpenAPI spec
weather_api_spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "Weather API",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": os.getenv("WEATHER_API_URL", "https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io")
        }
    ],
    "paths": {
        "/api/weather": {
            "get": {
                "operationId": "getWeather",
                "summary": "Get current weather",
                "parameters": [
                    {
                        "name": "zip_code",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Weather data",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "temperature": {"type": "number"},
                                        "condition": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

# Create tool definition using SDK models
weather_tool = OpenApiAgentTool(
    openapi=OpenApiFunctionDefinition(
        name="get_weather",
        description="Get current weather for US zip code",
        spec=weather_api_spec,
        auth=OpenApiAnonymousAuthDetails(),
    )
)

# Connect to Foundry project
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
    credential=DefaultAzureCredential()
)

# Get model deployment name
model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4.1")

# Create agent with OpenAPI tool
agent_name = "WeatherBot"
definition = PromptAgentDefinition(
    model=model_deployment,
    instructions="""You are a weather assistant.

When user asks about weather:
1. Use get_weather tool with their zip code
2. Report the current conditions
3. Be friendly and conversational
""",
    tools=[weather_tool]
)

agent = client.agents.create(
    name=agent_name,
    definition=definition,
    description="Weather assistant with OpenAPI tool"
)

print(f"✓ Agent created with OpenAPI tool: {agent.id}")
print(f"  Agent Name: {agent.name}")

# Get OpenAI client for conversations
openai = client.get_openai_client()

# Create conversation with weather question
conversation = openai.conversations.create(
    items=[{'type': 'message', 'role': 'user', 'content': "What's the weather in 10001?"}]
)

# Invoke agent using agent_reference pattern
response = openai.responses.create(
    conversation=conversation.id,
    extra_body={'agent': {'name': agent_name, 'type': 'agent_reference'}},
    input='',
)

print(f"\nUser: What's the weather in 10001?")
print(f"Agent: {response.output_text}")

# Cleanup
openai.conversations.delete(conversation_id=conversation.id)
client.agents.delete(agent_name)

print("\n✓ Cleaned up")
