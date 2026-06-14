import json
import ollama

from .tools import TOOLS
from .prompts import SYSTEM_PROMPT

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_part_details",
            "description":
                "Get information about a part",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_number": {
                        "type": "string"
                    }
                },
                "required": [
                    "part_number"
                ]
            }
        }
    }
]

async def run_agent(user_message: str):

    response = ollama.chat(
        model="qwen2.5",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        tools=TOOLS_SCHEMA
    )

    message = response["message"]

    if "tool_calls" not in message:
        return message["content"]
    
    tool_call = message["tool_calls"][0]

    tool_name = (
        tool_call["function"]["name"]
    )

    arguments = (
        tool_call["function"]["arguments"]
    )

    result = TOOLS[tool_name](
        **arguments
    )

    final_response = ollama.chat(
        model="qwen2.5",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_message
            },
            {
                "role": "tool",
                "content": json.dumps(result)
            }
        ]
    )

    return final_response["message"]["content"]