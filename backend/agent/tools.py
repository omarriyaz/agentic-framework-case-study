import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

with open("data/products.json", "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

with open("data/compatibility.json", "r", encoding="utf-8") as f:
    COMPATIBILITY = json.load(f)

with open("data/orders.json", "r", encoding="utf-8") as f:
    ORDERS = json.load(f)

# Build TF-IDF index once at startup
_CORPUS = [
    " ".join([
        p.get("name", ""),
        p.get("description", "") or "",
        p.get("brand", ""),
        p.get("category", ""),
        p.get("part_number", ""),
    ])
    for p in PRODUCTS
]
_VECTORIZER = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
_TFIDF_MATRIX = _VECTORIZER.fit_transform(_CORPUS)

cart = []

def _summarise(product):
    """Return a compact dict — omit compatible_models to keep context small."""
    return {
        "part_number": product.get("part_number"),
        "name": product.get("name"),
        "brand": product.get("brand"),
        "category": product.get("category"),
        "price": product.get("price") or "See PartSelect website for current price",
        "description": product.get("description", "")[:150] if product.get("description") else None,
        "url": product.get("url"),
    }

def search_parts(query: str, category: str = None):

    query_vec = _VECTORIZER.transform([query])
    scores = cosine_similarity(query_vec, _TFIDF_MATRIX).flatten()

    # Sort all products by relevance score, take top 20 candidates
    ranked_indices = np.argsort(scores)[::-1]

    results = []
    for i in ranked_indices:
        if scores[i] < 0.05:
            break
        product = PRODUCTS[i]
        if category and product.get("category", "").lower() != category.lower():
            continue
        results.append(_summarise(product))
        if len(results) == 10:
            break

    return results

def get_part_details(part_number: str):

    for product in PRODUCTS:

        if product["part_number"] == part_number:
            return _summarise(product)

    return {"error": "Part not found"}

def get_install_instructions(part_number: str):

    for product in PRODUCTS:

        if product["part_number"] == part_number:
            description = product.get("description") or ""
            return {
                "part_number": part_number,
                "name": product.get("name"),
                "url": product.get("url"),
                "description": description,
            }

    return {"error": "Part not found"}

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
            "part": _summarise(match) if match else None,
        }

    return {
        "compatible_parts": [_summarise(p) for p in compatible_parts[:10]],
        "total": len(compatible_parts),
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
        "keywords": ["ice", "ice maker", "no ice", "ice not making"],
        "part_queries": [
            ("ice maker assembly", "Refrigerator"),
            ("water inlet valve", "Refrigerator"),
        ],
    },
    "dishwasher not draining": {
        "steps": [
            "Check the drain hose for kinks or clogs.",
            "Clean the dishwasher filter at the bottom of the tub.",
            "Inspect the drain pump for obstructions.",
            "Ensure the garbage disposal knockout plug is removed if newly installed.",
        ],
        "keywords": ["drain", "water pooling", "standing water", "not draining"],
        "part_queries": [
            ("drain pump", "Dishwasher"),
            ("drain hose", "Dishwasher"),
            ("filter", "Dishwasher"),
        ],
    },
    "dishwasher not cleaning": {
        "steps": [
            "Clean the spray arms — check for clogged holes.",
            "Ensure the water temperature reaches 120°F.",
            "Check detergent dispenser is working correctly.",
            "Inspect the wash pump for wear.",
        ],
        "keywords": ["not cleaning", "dirty dishes", "dishes still dirty", "spots"],
        "part_queries": [
            ("spray arm", "Dishwasher"),
            ("wash pump", "Dishwasher"),
            ("detergent dispenser", "Dishwasher"),
        ],
    },
    "refrigerator not cooling": {
        "steps": [
            "Check the condenser coils — clean if dusty.",
            "Ensure the condenser fan is spinning.",
            "Verify the evaporator fan is running.",
            "Check the door gaskets for a good seal.",
            "Inspect the start relay on the compressor.",
        ],
        "keywords": ["not cooling", "warm", "not cold", "temperature too high"],
        "part_queries": [
            ("condenser fan", "Refrigerator"),
            ("evaporator fan", "Refrigerator"),
            ("door gasket", "Refrigerator"),
            ("start relay", "Refrigerator"),
        ],
    },
    "refrigerator leaking": {
        "steps": [
            "Check the defrost drain for clogs — flush with warm water.",
            "Inspect the water inlet valve for leaks.",
            "Examine the ice maker water line connections.",
            "Check door gaskets for damage causing condensation.",
        ],
        "keywords": ["leak", "leaking", "water on floor", "water inside"],
        "part_queries": [
            ("water inlet valve", "Refrigerator"),
            ("drain", "Refrigerator"),
            ("door gasket", "Refrigerator"),
        ],
    },
}

def troubleshoot_appliance(issue: str):

    issue_lower = issue.lower()
    best_match = None
    best_score = 0

    for guide in TROUBLESHOOTING_GUIDES.values():
        score = sum(1 for kw in guide["keywords"] if kw in issue_lower)
        if score > best_score:
            best_score = score
            best_match = guide

    if not best_match:
        return {
            "solution": "No specific guide found. Please describe the issue in more detail.",
            "suggested_parts": [],
        }

    # Run each targeted part query and collect unique results
    seen = set()
    suggested_parts = []
    for query, category in best_match["part_queries"]:
        for part in search_parts(query, category=category):
            if part["part_number"] not in seen:
                seen.add(part["part_number"])
                suggested_parts.append(part)
            if len(suggested_parts) == 4:
                break
        if len(suggested_parts) == 4:
            break

    return {
        "steps": best_match["steps"],
        "suggested_parts": suggested_parts,
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
    "get_install_instructions": get_install_instructions,
    "check_compatibility": check_compatibility,
    "troubleshoot_appliance": troubleshoot_appliance,
    "add_to_cart": add_to_cart,
    "get_order_status": get_order_status,
}