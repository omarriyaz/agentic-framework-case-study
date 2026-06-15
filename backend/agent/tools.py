import json

with open("data/products.json", "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

with open("data/compatibility.json", "r", encoding="utf-8") as f:
    COMPATIBILITY = json.load(f)

with open("data/orders.json", "r", encoding="utf-8") as f:
    ORDERS = json.load(f)

cart = []

def search_parts(query: str, category: str = None):

    query = query.lower()
    results = []

    for product in PRODUCTS:
        searchable = " ".join([
            product.get("name", ""),
            product.get("description", ""),
            product.get("brand", ""),
            product.get("category", ""),
            product.get("part_number", ""),
        ]).lower()

        if query in searchable:
            if category is None or product.get("category", "").lower() == category.lower():
                results.append(product)

    return results[:10]

def get_part_details(part_number: str):

    for product in PRODUCTS:

        if product["part_number"] == part_number:
            return product

    return {
        "error": "Part not found"
    }

def check_compatibility(
    model_number: str,
    part_number: str = None
):
    # Find all parts compatible with this model
    compatible_parts = []
    for product in PRODUCTS:
        models = product.get("compatible_models", [])
        if model_number in models:
            compatible_parts.append(product)

    if part_number:
        match = next(
            (p for p in compatible_parts if p["part_number"] == part_number),
            None
        )
        return {
            "compatible": match is not None,
            "part": match
        }

    return {
        "compatible_parts": compatible_parts[:10],
        "total": len(compatible_parts)
    }

TROUBLESHOOTING_GUIDES = {
    "ice maker": {
        "steps": [
            "Verify the water supply line is connected and the shutoff valve is open.",
            "Check the water inlet valve for clogs or failure.",
            "Inspect the ice maker assembly for visible damage.",
            "Ensure the freezer temperature is at or below 10°F (-12°C).",
            "Check that the ice maker's power switch is turned on.",
        ],
        "keywords": ["ice", "ice maker", "no ice", "ice not making"]
    },
    "dishwasher not draining": {
        "steps": [
            "Check the drain hose for kinks or clogs.",
            "Clean the dishwasher filter at the bottom of the tub.",
            "Inspect the drain pump for obstructions.",
            "Ensure the garbage disposal knockout plug is removed if newly installed.",
        ],
        "keywords": ["drain", "water pooling", "standing water", "not draining"]
    },
    "dishwasher not cleaning": {
        "steps": [
            "Clean the spray arms — check for clogged holes.",
            "Ensure the water temperature reaches 120°F.",
            "Check detergent dispenser is working correctly.",
            "Inspect the wash pump for wear.",
        ],
        "keywords": ["not cleaning", "dirty dishes", "dishes still dirty", "spots"]
    },
    "refrigerator not cooling": {
        "steps": [
            "Check the condenser coils — clean if dusty.",
            "Ensure the condenser fan is spinning.",
            "Verify the evaporator fan is running.",
            "Check the door gaskets for a good seal.",
            "Inspect the start relay on the compressor.",
        ],
        "keywords": ["not cooling", "warm", "not cold", "temperature too high"]
    },
    "refrigerator leaking": {
        "steps": [
            "Check the defrost drain for clogs — flush with warm water.",
            "Inspect the water inlet valve for leaks.",
            "Examine the ice maker water line connections.",
            "Check door gaskets for damage causing condensation.",
        ],
        "keywords": ["leak", "leaking", "water on floor", "water inside"]
    }
}

def troubleshoot_appliance(issue: str):

    issue_lower = issue.lower()
    best_match = None
    best_score = 0

    for guide_key, guide in TROUBLESHOOTING_GUIDES.items():
        score = sum(1 for kw in guide["keywords"] if kw in issue_lower)
        if score > best_score:
            best_score = score
            best_match = guide

    if not best_match:
        return {
            "solution": "No specific guide found. Please describe the issue in more detail.",
            "suggested_parts": []
        }

    # Find relevant parts from product data
    suggested_parts = search_parts(issue)[:3]

    return {
        "steps": best_match["steps"],
        "suggested_parts": suggested_parts
    }

def add_to_cart(part_number: str):

    cart.append(part_number)

    return {
        "success": True,
        "cart": cart
    }

def get_order_status(order_id: str):

    for order in ORDERS:

        if order["order_id"] == order_id:
            return order

    return {
        "error": "Order not found"
    }

TOOLS = {
    "search_parts": search_parts,
    "get_part_details": get_part_details,
    "check_compatibility": check_compatibility,
    "troubleshoot_appliance": troubleshoot_appliance,
    "add_to_cart": add_to_cart,
    "get_order_status": get_order_status,
}