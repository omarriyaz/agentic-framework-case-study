"""
PartSelect scraper.
"""

import json
import time
import re
import logging
from pathlib import Path
from typing import Optional
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

BASE_URL = "https://www.partselect.com"

# Category list pages
CATEGORY_URLS = {
    "Refrigerator": (
        "/Refrigerator-Parts.htm?SortBy=1"
    ),
    "Dishwasher": (
        "/Dishwasher-Parts.htm?SortBy=1"
    ),
}

PAGES_PER_CATEGORY = 5
REQUEST_DELAY = 1.2

session = requests.Session()
session.headers.update(HEADERS)


def get(url: str) -> Optional[BeautifulSoup]:
    """Fetch a URL and return parsed HTML, or None on failure."""
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as exc:
        log.warning("Failed to fetch %s: %s", url, exc)
        return None


def parse_price(text: str) -> Optional[float]:
    """Extract the first dollar amount from a string."""
    match = re.search(r"\$?([\d,]+\.\d{2})", text.replace(",", ""))
    if match:
        return float(match.group(1))
    return None


def scrape_list_page(url: str, category: str) -> list[dict]:
    """Scrape one category list page and return stub part dicts."""
    soup = get(url)
    if not soup:
        return []

    parts = []

    # PartSelect part cards sit in <div class="mega-m__part"> elements
    cards = soup.select("div.mega-m__part")
    if not cards:
        # Fallback selector, some pages use a different layout
        cards = soup.select("div.product-card")

    for card in cards:
        # Part number
        pn_tag = card.select_one("[data-part-number]")
        part_number = pn_tag["data-part-number"].strip() if pn_tag else None

        if not part_number:
            # Try to read from a text span
            pn_span = card.select_one(".mega-m__part__number, .part-number")
            if pn_span:
                part_number = pn_span.get_text(strip=True).replace("Part #", "").strip()

        if not part_number:
            continue

        # Name
        name_tag = card.select_one(
            ".mega-m__part__name a, .part-card__title a, h3 a"
        )
        name = name_tag.get_text(strip=True) if name_tag else "Unknown Part"

        # URL
        href = name_tag["href"] if name_tag and name_tag.has_attr("href") else None
        part_url = (BASE_URL + href) if href and href.startswith("/") else href

        # Price
        price_tag = card.select_one(
            ".mega-m__part__price, .price, [class*='price']"
        )
        price = parse_price(price_tag.get_text()) if price_tag else None

        # Brand (sometimes listed in card)
        brand_tag = card.select_one(".mega-m__part__brand, .brand")
        brand = brand_tag.get_text(strip=True) if brand_tag else None

        parts.append({
            "part_number": part_number,
            "name": name,
            "price": price,
            "brand": brand,
            "category": category,
            "url": part_url,
            "description": None,
            "compatible_models": [],
        })

    log.info("  Found %d parts on list page", len(parts))
    return parts


def scrape_part_detail(part: dict) -> dict:
    """
    Enrich a part stub with description and compatible models
    by visiting the part's detail page.
    """
    if not part.get("url"):
        return part

    soup = get(part["url"])
    if not soup:
        return part

    # Description
    desc_tag = soup.select_one(
        "#Description .js-content, "
        ".pd__description, "
        "[itemprop='description']"
    )
    if desc_tag:
        part["description"] = desc_tag.get_text(" ", strip=True)[:1000]

    # Brand from detail page (more reliable than list page)
    if not part.get("brand"):
        brand_tag = soup.select_one(
            "[itemprop='brand'] [itemprop='name'], "
            ".pd__brand"
        )
        if brand_tag:
            part["brand"] = brand_tag.get_text(strip=True)

    # Price (may be more accurate on detail page)
    if not part.get("price"):
        price_tag = soup.select_one(
            "[itemprop='price'], .pd__price__current, .js-partPrice"
        )
        if price_tag:
            price_text = price_tag.get("content") or price_tag.get_text()
            part["price"] = parse_price(price_text)

    # Compatible models — listed in a table on the detail page
    model_links = soup.select(
        "#FitsList .js-collapseList a, "
        ".pd__crossref__list a, "
        "[data-model-number]"
    )
    models = []
    for link in model_links:
        model_num = (
            link.get("data-model-number")
            or link.get_text(strip=True)
        )
        if model_num and re.match(r"^[A-Z0-9]{5,}", model_num.upper()):
            models.append(model_num.upper().strip())

    part["compatible_models"] = list(set(models))
    return part


def build_compatibility_map(products: list[dict]) -> dict[str, list[str]]:
    """
    Build { model_number: [part_number, ...] } index
    from the compatible_models field on each product.
    """
    compat: dict[str, list[str]] = {}
    for product in products:
        for model in product.get("compatible_models", []):
            compat.setdefault(model, [])
            if product["part_number"] not in compat[model]:
                compat[model].append(product["part_number"])
    return compat


def scrape_category(category: str, path: str, max_pages: int) -> list[dict]:
    parts: list[dict] = []
    seen: set[str] = set()

    for page in range(1, max_pages + 1):
        separator = "&" if "?" in path else "?"
        page_url = f"{BASE_URL}{path}{separator}start={(page - 1) * 24}"
        log.info("Scraping %s page %d: %s", category, page, page_url)

        page_parts = scrape_list_page(page_url, category)
        if not page_parts:
            log.info("No parts found — stopping early for %s", category)
            break

        new_parts = [p for p in page_parts if p["part_number"] not in seen]
        seen.update(p["part_number"] for p in new_parts)

        log.info(
            "Enriching %d new parts from %s page %d ...",
            len(new_parts), category, page
        )

        for i, part in enumerate(new_parts):
            log.info(
                "  [%d/%d] %s — %s",
                i + 1, len(new_parts), part["part_number"], part["name"]
            )
            enrich = scrape_part_detail(part)
            parts.append(enrich)
            time.sleep(REQUEST_DELAY)

        time.sleep(REQUEST_DELAY)

    return parts


def main():
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    all_products: list[dict] = []

    for category, path in CATEGORY_URLS.items():
        log.info("=== Scraping category: %s ===", category)
        products = scrape_category(category, path, PAGES_PER_CATEGORY)
        all_products.extend(products)
        log.info("Total for %s: %d parts", category, len(products))

    if not all_products:
        log.error(
            "No products scraped. PartSelect may require JavaScript rendering.\n"
            "Install Playwright: pip install playwright && playwright install chromium\n"
            "Then use the playwright version of this scraper."
        )
        return

    # Write products
    products_path = data_dir / "products.json"
    with open(products_path, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)
    log.info("Wrote %d products to %s", len(all_products), products_path)

    # Write compatibility map
    compat = build_compatibility_map(all_products)
    compat_path = data_dir / "compatibility.json"
    with open(compat_path, "w", encoding="utf-8") as f:
        json.dump(compat, f, indent=2, ensure_ascii=False)
    log.info(
        "Wrote compatibility map (%d models) to %s",
        len(compat), compat_path
    )


if __name__ == "__main__":
    main()
