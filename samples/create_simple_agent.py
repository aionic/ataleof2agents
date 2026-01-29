#!/usr/bin/env python3
"""
Minimal example: Create and invoke an agent in Azure AI Foundry.

This is the simplest possible agent example using the GA SDK v2.0.0+ API.
Uses the conversations/responses pattern with agent_reference.
"""

import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

load_dotenv()

# Connect to Foundry project
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
    credential=DefaultAzureCredential()
)

# Get model deployment name
model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4.1")

# Create simple agent (no tools) using PromptAgentDefinition
agent_name = "SimpleAssistant"
definition = PromptAgentDefinition(
    model=model_deployment,
    instructions="You are a helpful assistant. Keep responses concise."
)

agent = client.agents.create(
    name=agent_name,
    definition=definition,
    description="Simple demo agent"
)

print(f"✓ Agent created: {agent.name} (ID: {agent.id})")

# Get OpenAI client for conversations
openai = client.get_openai_client()

# Create conversation with initial message
conversation = openai.conversations.create(
    items=[{'type': 'message', 'role': 'user', 'content': 'Hello! What can you help me with?'}]
)
print(f"✓ Conversation created: {conversation.id}")

# Invoke agent using agent_reference pattern
response = openai.responses.create(
    conversation=conversation.id,
    extra_body={'agent': {'name': agent_name, 'type': 'agent_reference'}},
    input='',
)

print(f"\nAgent: {response.output_text}")

# Cleanup
openai.conversations.delete(conversation_id=conversation.id)
client.agents.delete(agent_name)

print("\n✓ Cleaned up")
