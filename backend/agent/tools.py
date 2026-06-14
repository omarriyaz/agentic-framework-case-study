import json

with open("data/products.json") as f:
    PRODUCTS = json.load(f)

with open("data/compatibility.json") as f:
    COMPATIBILITY = json.load(f)

with open("data/orders.json") as f:
    ORDERS = json.load(f)

cart = []

def search_parts(query: str):

    query = query.lower()

    results = []

    for product in PRODUCTS:

        if query in product["name"].lower():
            results.append(product)

    return results

def get_part_details(part_number: str):

    for product in PRODUCTS:

        if product["part_number"] == part_number:
            return product

    return {
        "error": "Part not found"
    }

def check_compatibility(
    model_number: str,
    part_number: str
):

    compatible_parts = COMPATIBILITY.get(
        model_number,
        []
    )

    return {
        "compatible":
            part_number in compatible_parts
    }

TROUBLESHOOTING = {
    "ice maker not working":
        """
        1. Verify water supply.
        2. Check inlet valve.
        3. Inspect ice maker assembly.
        4. Ensure freezer temperature
           is below 10°F.
        """
}

def troubleshoot_appliance(issue: str):

    issue = issue.lower()

    for problem, solution in TROUBLESHOOTING.items():

        if problem in issue:
            return {
                "solution": solution
            }

    return {
        "solution":
            "No troubleshooting guide found."
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