import os
from openai import OpenAI
import json

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1")  # Allow env override


def generate_text(user_input: str, instructions: str) -> str:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")
    client = OpenAI()
    response = client.responses.create(
        model=DEFAULT_MODEL,
        input=user_input,
        instructions=instructions,
    )  # Call Responses API for text output
    return response.output_text.strip()  # Normalize output for storage


def generate_structured(
    user_input: str, instructions: str, schema: dict[str, object], name: str
) -> dict[str, object]:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")
    client = OpenAI()
    response = client.responses.create(
        model=DEFAULT_MODEL,
        input=user_input,
        instructions=instructions,
        text={
            "format": {
                "type": "json_schema",
                "name": name,
                "schema": schema,
                "strict": True,
            }
        },
    )  # Enforce schema output
    return json.loads(response.output_text)  # Parse structured JSON
