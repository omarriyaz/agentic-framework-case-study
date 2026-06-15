import json
import re
import ollama

from .tools import TOOLS
from .prompts import SYSTEM_PROMPT

# Matches typical appliance model numbers: 6-20 alphanumeric chars with optional dashes
_MODEL_NUMBER_RE = re.compile(r'\b([A-Z]{1,4}[\d]{3,}[A-Z0-9\-]{2,}|[\d]{5,}[A-Z]{1,4}[\d]*)\b')

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

def _extract_parts(tool_name, result):
    """Pull product dicts out of any tool result that contains them."""
    if not isinstance(result, (dict, list)):
        return []

    # Tools that return a list of parts directly
    if tool_name == "search_parts" and isinstance(result, list):
        return result

    if isinstance(result, dict):
        # check_compatibility → compatible_parts list
        if "compatible_parts" in result:
            return result["compatible_parts"]
        # check_compatibility with a specific part
        if "part" in result and result["part"]:
            return [result["part"]]
        # troubleshoot_appliance → suggested_parts
        if "suggested_parts" in result:
            return result["suggested_parts"]
        # get_part_details / get_install_instructions → single part shape
        if "part_number" in result:
            return [result]

    return []


def _generate_chips(messages, assistant_reply):
    """Ask the LLM to suggest 2-3 natural follow-up questions given the conversation so far."""
    prompt = (
        "Based on this appliance parts support conversation, suggest exactly 2-3 short follow-up "
        "questions the user might want to ask next. Return ONLY a JSON array of strings, no explanation. "
        "Each question should be concise (under 10 words) and genuinely useful given what was just discussed. "
        "Do not suggest anything already answered or visible on screen (e.g. don't suggest 'add to cart' "
        "if part cards are shown, don't suggest 'how to install' if install steps were just given).\n\n"
        f"Last assistant reply: {assistant_reply[:400]}"
    )

    try:
        resp = ollama.chat(
            model="qwen2.5",
            messages=[
                *messages[-4:],
                {"role": "user", "content": prompt},
            ],
        )
        raw = resp["message"]["content"].strip()
        # Parse JSON array from response
        start, end = raw.find("["), raw.rfind("]")
        if start != -1 and end != -1:
            chips = json.loads(raw[start:end + 1])
            return [c for c in chips if isinstance(c, str)][:3]
    except Exception:
        pass

    return []


async def run_agent(user_message, history=[]):

    prior = [
        {"role": m.role, "content": m.content[:500]}
        for m in history[-4:]
        if m.role in ("user", "assistant") and m.content and m.content.strip()
    ]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *prior,
        {"role": "user", "content": user_message},
    ]

    collected_parts = []
    seen_part_numbers = set()
    detected_model = None

    while True:

        response = ollama.chat(
            model="qwen2.5",
            messages=messages,
            tools=TOOLS_SCHEMA
        )

        assistant_message = response["message"]
        messages.append(assistant_message)

        tool_calls = assistant_message.get("tool_calls", [])

        if not tool_calls:
            reply = assistant_message["content"]
            # Fallback: regex scan the user message if no tool gave us a model
            if not detected_model:
                match = _MODEL_NUMBER_RE.search(user_message.upper())
                if match:
                    detected_model = match.group(1)
            chips = _generate_chips(messages, reply)
            return reply, collected_parts, chips, detected_model

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            args = tool_call["function"]["arguments"]
            result = TOOLS[tool_name](**args)

            # Capture model number from compatibility checks
            if tool_name == "check_compatibility" and not detected_model:
                detected_model = args.get("model_number")

            for part in _extract_parts(tool_name, result):
                pn = part.get("part_number")
                if pn and pn not in seen_part_numbers:
                    seen_part_numbers.add(pn)
                    collected_parts.append(part)

            messages.append({"role": "tool", "content": json.dumps(result)})