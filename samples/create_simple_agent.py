#!/usr/bin/env python3
"""
Minimal example: Create and invoke an agent in Azure AI Foundry.

This is the simplest possible agent example.
"""

import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

# Connect to Foundry project
client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.getenv("AI_PROJECT_CONNECTION_STRING")
)

# Create simple agent (no tools)
agent = client.agents.create_agent(
    model="gpt-4",
    name="SimpleAssistant",
    instructions="You are a helpful assistant. Keep responses concise."
)

print(f"✓ Agent created: {agent.id}")

# Create conversation thread
thread = client.agents.threads.create()
print(f"✓ Thread created: {thread.id}")

# Send message
message = client.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="Hello! What can you help me with?"
)

# Run agent
run = client.agents.runs.create_and_process(
    thread_id=thread.id,
    agent_id=agent.id
)

# Get response
messages = client.agents.messages.list(thread_id=thread.id)
response = messages.data[0].content[0].text.value

print(f"\nAgent: {response}")

# Cleanup
client.agents.threads.delete(thread_id=thread.id)
client.agents.delete_agent(agent.id)

print("\n✓ Cleaned up")
