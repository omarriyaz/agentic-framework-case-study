"""Build compatibility.json from products.json."""
import json
from pathlib import Path

data_dir = Path(__file__).parent.parent / "data"

with open(data_dir / "products.json") as f:
    products = json.load(f)

compat = {}
for p in products:
    for model in p.get("compatible_models", []):
        compat.setdefault(model, [])
        if p["part_number"] not in compat[model]:
            compat[model].append(p["part_number"])

with open(data_dir / "compatibility.json", "w") as f:
    json.dump(compat, f, indent=2)

print(f"Built compatibility map: {len(compat)} models, {len(products)} parts")
