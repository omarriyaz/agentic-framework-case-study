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

_CORPUS = [
    " ".join(filter(None, [
        p.get("name", ""),
        p.get("description", "") or "",
        p.get("brand", ""),
        p.get("category", ""),
        p.get("part_number", ""),
    ]))
    for p in PRODUCTS
]
_VECTORIZER = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
_TFIDF_MATRIX = _VECTORIZER.fit_transform(_CORPUS)

cart = []

INSTALL_DIFFICULTY = {
    "ice maker":           {"difficulty": "Moderate", "time": "45 min",  "tools": "Screwdriver, nut driver"},
    "water inlet valve":   {"difficulty": "Moderate", "time": "30 min",  "tools": "Screwdriver, pliers, bucket"},
    "drain pump":          {"difficulty": "Moderate", "time": "1 hour",  "tools": "Screwdriver, pliers, towels"},
    "spray arm":           {"difficulty": "Easy",     "time": "10 min",  "tools": "None — tool-free snap fit"},
    "door gasket":         {"difficulty": "Easy",     "time": "20 min",  "tools": "Flathead screwdriver"},
    "door bin":            {"difficulty": "Easy",     "time": "2 min",   "tools": "None — tool-free snap fit"},
    "shelf bin":           {"difficulty": "Easy",     "time": "2 min",   "tools": "None — tool-free snap fit"},
    "crisper drawer":      {"difficulty": "Easy",     "time": "5 min",   "tools": "None"},
    "evaporator fan":      {"difficulty": "Moderate", "time": "1 hour",  "tools": "Screwdriver, nut driver"},
    "condenser fan":       {"difficulty": "Moderate", "time": "45 min",  "tools": "Screwdriver, nut driver"},
    "start relay":         {"difficulty": "Easy",     "time": "15 min",  "tools": "None — pull and replace"},
    "detergent dispenser": {"difficulty": "Easy",     "time": "20 min",  "tools": "Screwdriver"},
    "wash pump":           {"difficulty": "Advanced", "time": "2 hours", "tools": "Screwdriver, pliers, multimeter"},
    "drain hose":          {"difficulty": "Easy",     "time": "20 min",  "tools": "Pliers, bucket"},
}

TROUBLESHOOTING_GUIDES = {
    "ice maker": {
        "keywords": ["ice", "ice maker", "no ice", "ice not making"],
        "causes": [
            {"rank": 1, "cause": "Ice maker power switch is off",                    "cost": "Free",      "difficulty": "Easy",     "time": "1 min"},
            {"rank": 2, "cause": "Freezer temperature too warm (above 10°F)",        "cost": "Free",      "difficulty": "Easy",     "time": "5 min"},
            {"rank": 3, "cause": "Water supply line kinked or shutoff valve closed", "cost": "Free",      "difficulty": "Easy",     "time": "10 min"},
            {"rank": 4, "cause": "Faulty water inlet valve",                         "cost": "$20–$50",   "difficulty": "Moderate", "time": "30 min"},
            {"rank": 5, "cause": "Ice maker assembly failure",                       "cost": "$50–$150",  "difficulty": "Moderate", "time": "45 min"},
        ],
        "steps": [
            "Verify the ice maker power switch is turned on.",
            "Ensure the freezer temperature is at or below 10°F (-12°C).",
            "Check the water supply line is connected and the shutoff valve is open.",
            "Test the water inlet valve for clogs or electrical failure.",
            "Inspect the ice maker assembly for damage and replace if needed.",
        ],
        "part_queries": [("ice maker assembly", "Refrigerator"), ("water inlet valve", "Refrigerator")],
    },
    "dishwasher not draining": {
        "keywords": ["drain", "water pooling", "standing water", "not draining"],
        "causes": [
            {"rank": 1, "cause": "Clogged filter or food debris in drain area",       "cost": "Free",     "difficulty": "Easy",     "time": "10 min"},
            {"rank": 2, "cause": "Kinked or clogged drain hose",                      "cost": "Free–$15", "difficulty": "Easy",     "time": "15 min"},
            {"rank": 3, "cause": "Garbage disposal knockout plug not removed",         "cost": "Free",     "difficulty": "Easy",     "time": "5 min"},
            {"rank": 4, "cause": "Faulty drain pump",                                 "cost": "$30–$80",  "difficulty": "Moderate", "time": "1 hour"},
        ],
        "steps": [
            "Clean the dishwasher filter at the bottom of the tub.",
            "Check the drain hose for kinks or clogs.",
            "Ensure the garbage disposal knockout plug is removed if newly installed.",
            "Inspect and test the drain pump — replace if it won't run.",
        ],
        "part_queries": [("drain pump", "Dishwasher"), ("drain hose", "Dishwasher"), ("filter", "Dishwasher")],
    },
    "dishwasher not cleaning": {
        "keywords": ["not cleaning", "dirty dishes", "dishes still dirty", "spots"],
        "causes": [
            {"rank": 1, "cause": "Clogged spray arm holes",         "cost": "Free",     "difficulty": "Easy",     "time": "10 min"},
            {"rank": 2, "cause": "Water temperature below 120°F",   "cost": "Free",     "difficulty": "Easy",     "time": "5 min"},
            {"rank": 3, "cause": "Detergent dispenser not opening", "cost": "$15–$40",  "difficulty": "Easy",     "time": "20 min"},
            {"rank": 4, "cause": "Worn or failed wash pump",        "cost": "$50–$120", "difficulty": "Advanced", "time": "2 hours"},
        ],
        "steps": [
            "Remove and clean the spray arms — clear any clogged holes with a toothpick.",
            "Run the hot water at the sink before starting a cycle to ensure 120°F water.",
            "Inspect the detergent dispenser door — replace if it sticks or won't latch.",
            "Test the wash pump motor for continuity and replace if failed.",
        ],
        "part_queries": [("spray arm", "Dishwasher"), ("wash pump", "Dishwasher"), ("detergent dispenser", "Dishwasher")],
    },
    "refrigerator not cooling": {
        "keywords": ["not cooling", "warm", "not cold", "temperature too high"],
        "causes": [
            {"rank": 1, "cause": "Dirty condenser coils restricting airflow",              "cost": "Free",       "difficulty": "Easy",     "time": "15 min"},
            {"rank": 2, "cause": "Door gasket not sealing — warm air leaking in",          "cost": "$20–$60",    "difficulty": "Easy",     "time": "20 min"},
            {"rank": 3, "cause": "Evaporator fan not circulating cold air",                "cost": "$30–$80",    "difficulty": "Moderate", "time": "1 hour"},
            {"rank": 4, "cause": "Faulty start relay preventing compressor from starting", "cost": "$10–$30",    "difficulty": "Moderate", "time": "30 min"},
            {"rank": 5, "cause": "Compressor failure",                                     "cost": "$200–$500+", "difficulty": "Advanced", "time": "Professional recommended"},
        ],
        "steps": [
            "Clean the condenser coils with a vacuum or brush.",
            "Inspect door gaskets — close a dollar bill in the door; if it slides out easily, replace the gasket.",
            "Listen for the evaporator fan — if silent, test and replace the motor.",
            "Shake the start relay (on the compressor side) — a rattling sound means replace it.",
            "If none of the above, have a technician inspect the compressor.",
        ],
        "part_queries": [("evaporator fan", "Refrigerator"), ("door gasket", "Refrigerator"), ("start relay", "Refrigerator"), ("condenser fan", "Refrigerator")],
    },
    "refrigerator leaking": {
        "keywords": ["leak", "leaking", "water on floor", "water inside"],
        "causes": [
            {"rank": 1, "cause": "Clogged defrost drain — ice dam forcing water out", "cost": "Free",    "difficulty": "Easy",     "time": "20 min"},
            {"rank": 2, "cause": "Cracked or loose water inlet valve connection",      "cost": "$20–$50", "difficulty": "Moderate", "time": "30 min"},
            {"rank": 3, "cause": "Ice maker water line loose or cracked",              "cost": "$10–$25", "difficulty": "Easy",     "time": "20 min"},
            {"rank": 4, "cause": "Damaged door gasket causing condensation",           "cost": "$20–$60", "difficulty": "Easy",     "time": "20 min"},
        ],
        "steps": [
            "Flush the defrost drain with warm water using a turkey baster.",
            "Inspect the water inlet valve and its connections for drips.",
            "Trace the ice maker water line from the back of the fridge to the valve.",
            "Check door gaskets for tears or gaps that could cause condensation pooling.",
        ],
        "part_queries": [("water inlet valve", "Refrigerator"), ("drain", "Refrigerator"), ("door gasket", "Refrigerator")],
    },
}

REPAIR_BUNDLES = {
    "ice maker":           ["water inlet valve", "ice maker fill tube", "ice maker assembly"],
    "water inlet valve":   ["ice maker assembly", "water line", "ice maker fill tube"],
    "drain pump":          ["drain hose", "door gasket", "filter"],
    "spray arm":           ["wash pump", "detergent dispenser", "door gasket"],
    "evaporator fan":      ["start relay", "door gasket", "condenser fan"],
    "door gasket":         ["door hinge", "door handle"],
    "start relay":         ["evaporator fan", "condenser fan"],
    "detergent dispenser": ["spray arm", "door latch"],
    "condenser fan":       ["evaporator fan", "start relay"],
    "defrost":             ["evaporator fan", "door gasket"],
}


def _get_difficulty(name: str):
    name_lower = name.lower()
    for keyword, info in INSTALL_DIFFICULTY.items():
        if keyword in name_lower:
            return info
    return {"difficulty": "Moderate", "time": "30–60 min", "tools": "Screwdriver"}


def _summarise(p):
    return {
        "part_number": p.get("part_number"),
        "name":        p.get("name"),
        "brand":       p.get("brand"),
        "category":    p.get("category"),
        "price":       p.get("price") or "See PartSelect website for current price",
        "description": (p.get("description", "") or "")[:150] or None,
        "url":         p.get("url"),
        "image_url":   p.get("image_url"),
        "install":     _get_difficulty(p.get("name", "")),
        "rating":      p.get("rating"),
        "review_count":p.get("review_count", 0),
        "is_oem":      p.get("is_oem", False),
        "cross_refs":  p.get("cross_refs", []),
    }


def search_parts(query: str, category: str = None):
    scores = cosine_similarity(_VECTORIZER.transform([query]), _TFIDF_MATRIX).flatten().copy()

    for i, p in enumerate(PRODUCTS):
        if (p.get("rating") or 0) >= 4.5 and (p.get("review_count") or 0) >= 10:
            scores[i] *= 1.1

    results = []
    for i in np.argsort(scores)[::-1]:
        if scores[i] < 0.05:
            break
        p = PRODUCTS[i]
        if category and p.get("category", "").lower() != category.lower():
            continue
        results.append(_summarise(p))
        if len(results) == 10:
            break
    return results


def get_part_details(part_number: str):
    p = next((p for p in PRODUCTS if p["part_number"] == part_number), None)
    return _summarise(p) if p else {"error": "Part not found"}


def get_install_instructions(part_number: str):
    p = next((p for p in PRODUCTS if p["part_number"] == part_number), None)
    if not p:
        return {"error": "Part not found"}
    return {
        "part_number": part_number,
        "name":        p.get("name"),
        "url":         p.get("url"),
        "description": p.get("description") or "",
    }


def check_compatibility(model_number: str, part_number: str = None):
    compatible = [p for p in PRODUCTS if model_number in p.get("compatible_models", [])]
    if part_number:
        match = next((p for p in compatible if p["part_number"] == part_number), None)
        return {"compatible": match is not None, "part": _summarise(match) if match else None}
    return {"compatible_parts": [_summarise(p) for p in compatible[:10]], "total": len(compatible)}


def troubleshoot_appliance(issue: str):
    issue_lower = issue.lower()
    best_match = max(
        TROUBLESHOOTING_GUIDES.values(),
        key=lambda g: sum(1 for kw in g["keywords"] if kw in issue_lower),
        default=None,
    )
    if not best_match or not any(kw in issue_lower for kw in best_match["keywords"]):
        return {"solution": "No specific guide found. Please describe the issue in more detail.", "suggested_parts": []}

    seen, suggested_parts = set(), []
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
        "ranked_causes":   best_match["causes"],
        "steps":           best_match["steps"],
        "suggested_parts": suggested_parts,
    }


def get_related_parts(part_number: str):
    part = get_part_details(part_number)
    if "error" in part:
        return {"error": "Part not found"}

    name_lower = part.get("name", "").lower()
    related_queries = next((v for k, v in REPAIR_BUNDLES.items() if k in name_lower), [])
    if not related_queries:
        return {"related_parts": [], "message": "No bundle data for this part."}

    seen, related = {part_number}, []
    for query in related_queries:
        for candidate in search_parts(query, category=part.get("category")):
            if candidate["part_number"] not in seen:
                seen.add(candidate["part_number"])
                related.append(candidate)
                break
        if len(related) == 3:
            break

    return {
        "part":          part,
        "related_parts": related,
        "message":       f"Customers replacing {part['name']} also commonly replace these parts.",
    }


def add_to_cart(part_number: str):
    cart.append(part_number)
    return {"success": True, "cart": cart}


def get_order_status(order_id: str):
    order = next((o for o in ORDERS if o["order_id"] == order_id), None)
    return order if order else {"error": "Order not found"}


TOOLS = {
    "search_parts":            search_parts,
    "get_part_details":        get_part_details,
    "get_install_instructions":get_install_instructions,
    "get_related_parts":       get_related_parts,
    "check_compatibility":     check_compatibility,
    "troubleshoot_appliance":  troubleshoot_appliance,
    "add_to_cart":             add_to_cart,
    "get_order_status":        get_order_status,
}
