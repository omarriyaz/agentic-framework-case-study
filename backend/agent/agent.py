import json
import ollama

from .tools import TOOLS
from .prompts import SYSTEM_PROMPT

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_parts",
            "description": "Search for refrigerator or dishwasher parts by keyword, part number, brand, or symptom description",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword, symptom, or part name"},
                    "category": {"type": "string", "enum": ["Refrigerator", "Dishwasher"], "description": "Optional: filter by appliance type"}
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
            "name": "get_install_instructions",
            "description": "Get installation instructions for a specific part by part number. Use this whenever a user asks how to install, replace, or fit a part.",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_number": {"type": "string", "description": "The part number to get installation instructions for"}
                },
                "required": ["part_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_compatibility",
            "description": "Check if a part is compatible with a model, or list all compatible parts for a model",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_number": {"type": "string", "description": "The appliance model number"},
                    "part_number": {"type": "string", "description": "Optional: a specific part number to check against the model"}
                },
                "required": ["model_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "troubleshoot_appliance",
            "description": "Get a step-by-step troubleshooting guide for a refrigerator or dishwasher issue, along with suggested replacement parts",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue": {"type": "string", "description": "Description of the appliance problem"}
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

async def run_agent(user_message, history=[]):

    # Keep last 6 messages (3 turns) to stay within Ollama's context window
    recent_history = history[-6:] if len(history) > 6 else history
    prior = [
        {"role": m.role, "content": m.content}
        for m in recent_history
        if m.role in ("user", "assistant")
    ]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *prior,
        {"role": "user", "content": user_message},
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