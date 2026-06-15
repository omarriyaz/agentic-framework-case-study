import json
import ollama

from .tools import TOOLS
from .prompts import SYSTEM_PROMPT

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_parts",
            "description": "Search appliance parts",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_part_details",
            "description": "Get part details",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_number": {"type": "string"}
                },
                "required": ["part_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_compatibility",
            "description": "Check model compatibility",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_number": {"type": "string"},
                    "part_number": {"type": "string"}
                },
                "required": [
                    "model_number",
                    "part_number"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "troubleshoot_appliance",
            "description": "Troubleshoot appliance issues",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue": {"type": "string"}
                },
                "required": ["issue"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add part to cart",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_number": {"type": "string"}
                },
                "required": ["part_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Get order status",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"}
                },
                "required": ["order_id"]
            }
        }
    }
]

async def run_agent(user_message):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    while True:

        response = ollama.chat(
            model="qwen2.5",
            messages=messages,
            tools=TOOLS_SCHEMA
        )

        assistant_message = response["message"]

        messages.append(assistant_message)

        tool_calls = assistant_message.get(
            "tool_calls",
            []
        )

        if not tool_calls:
            return assistant_message["content"]

        for tool_call in tool_calls:

            tool_name = (
                tool_call["function"]["name"]
            )

            args = (
                tool_call["function"]["arguments"]
            )

            result = TOOLS[tool_name](**args)

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result)
                }
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