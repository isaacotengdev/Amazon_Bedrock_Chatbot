"""
AWS Bedrock Conversational Chatbot using Amazon Titan Text

This script demonstrates how to:
- Invoke Amazon Bedrock models using boto3
- Implement conversation memory manually
- Format prompts for deterministic, repeatable responses
- Build a simple terminal-based chatbot

Author: Isaac Oteng
"""

import boto3
import json
import pprint
from botocore.exceptions import ClientError

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

# AWS region where Bedrock is enabled
REGION = "us-east-1"

# Amazon Titan Text model ID
MODEL_ID = "amazon.titan-text-express-v1"

# Initialize the Bedrock Runtime client
# NOTE: invoke_model() exists ONLY on bedrock-runtime
client = boto3.client(
    service_name="bedrock-runtime",
    region_name=REGION
)

# Pretty printer for clean console output (optional)
pp = pprint.PrettyPrinter(width=100)

# ---------------------------------------------------------
# CONVERSATION STATE (MEMORY)
# ---------------------------------------------------------

# Stores the entire conversation history
# Titan does NOT manage state — we must send history manually
history = []

# Simulated system prompt (Titan does not support system roles natively)
SYSTEM_PROMPT = (
    "You are a helpful, concise, and knowledgeable assistant. "
    "Use the conversation history to answer naturally.\n"
)

def build_prompt():
    """
    Constructs the full prompt sent to the Titan model.

    The prompt includes:
    - A system instruction
    - The full conversation history
    - An explicit 'Assistant:' cue to guide generation
    """
    conversation = "\n".join(history)
    return f"{SYSTEM_PROMPT}\n{conversation}\nAssistant:"

def build_payload():
    """
    Builds the request payload for the Bedrock invoke_model API.

    Key configuration choices:
    - maxTokenCount: Controls response length
    - temperature: Lower = more deterministic
    - stopSequences: Prevents the model from hallucinating user input
    """
    return json.dumps({
        "inputText": build_prompt(),
        "textGenerationConfig": {
            "maxTokenCount": 512,
            "temperature": 0.3,
            "topP": 1,
            "stopSequences": ["User:"]
        }
    })

# ---------------------------------------------------------
# CHAT LOOP
# ---------------------------------------------------------

print("🤖 Bot: Hello! I am your chatbot. Type 'exit' to quit.\n")

try:
    while True:
        # Read user input from terminal
        user_input = input("User: ").strip()

        # Exit condition
        if user_input.lower() == "exit":
            print("👋 Bot: Goodbye!")
            break

        # Append user message to conversation history
        history.append(f"User: {user_input}")

        # Invoke the Titan model
        response = client.invoke_model(
            modelId=MODEL_ID,
            body=build_payload(),
            accept="application/json",
            contentType="application/json"
        )

        # Bedrock returns a streaming body → must be read()
        response_body = json.loads(response["body"].read())

        # Extract the generated text
        output_text = response_body["results"][0]["outputText"].strip()

        # Display response
        print(f"\n🤖 Bot: {output_text}\n")

        # Append assistant response to history
        history.append(f"Assistant: {output_text}")

except (ClientError, Exception) as e:
    print(f"❌ ERROR invoking {MODEL_ID}: {e}")
