#!/usr/bin/env python3
"""
Example: Add OpenAPI tool to agent.

Shows how to integrate an external API using OpenAPI specification.
"""

import os
import json
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
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
            "url": "https://ca-weather-api-dev-ezbvua.mangomushroom-3560f614.swedencentral.azurecontainerapps.io"
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

# Create tool definition
weather_tool = {
    "type": "openapi",
    "openapi": {
        "name": "get_weather",
        "description": "Get current weather for US zip code",
        "spec": weather_api_spec,
        "auth": {"type": "anonymous"}
    }
}

# Connect and create agent
client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.getenv("AI_PROJECT_CONNECTION_STRING")
)

agent = client.agents.create_agent(
    model="gpt-4",
    name="WeatherBot",
    instructions="""You are a weather assistant.

When user asks about weather:
1. Use get_weather tool with their zip code
2. Report the current conditions
3. Be friendly and conversational
""",
    tools=[weather_tool]
)

print(f"✓ Agent created with OpenAPI tool: {agent.id}")
print(f"  Agent: {agent.name}")
print(f"  Tools: {len(agent.tools)}")

# Test the agent
thread = client.agents.threads.create()

message = client.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="What's the weather in 10001?"
)

run = client.agents.runs.create_and_process(
    thread_id=thread.id,
    agent_id=agent.id
)

messages = client.agents.messages.list(thread_id=thread.id)
response = messages.data[0].content[0].text.value

print(f"\nUser: What's the weather in 10001?")
print(f"Agent: {response}")

# Cleanup
client.agents.threads.delete(thread_id=thread.id)
client.agents.delete_agent(agent.id)

print("\n✓ Cleaned up")
