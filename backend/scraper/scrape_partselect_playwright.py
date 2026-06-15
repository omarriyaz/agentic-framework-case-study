"""
Playwright version of scraper.
"""

import asyncio
import json
import re
import logging
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)

BASE_URL = "https://www.partselect.com"

CATEGORY_URLS = {
    "Refrigerator": "/Refrigerator-Parts.htm?SortBy=1",
    "Dishwasher": "/Dishwasher-Parts.htm?SortBy=1",
}

PAGES_PER_CATEGORY = 5
REQUEST_DELAY = 1500


def parse_price(text: str) -> Optional[float]:
    match = re.search(r"\$?([\d,]+\.\d{2})", text.replace(",", ""))
    if match:
        return float(match.group(1))
    return None


async def scrape_list_page(page: Page, url: str, category: str) -> list[dict]:
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(REQUEST_DELAY)

    parts = []

    cards = await page.query_selector_all("div.mega-m__part, div.product-card")

    for card in cards:
        # Part number
        pn_el = await card.query_selector("[data-part-number]")
        if pn_el:
            part_number = (await pn_el.get_attribute("data-part-number") or "").strip()
        else:
            pn_span = await card.query_selector(
                ".mega-m__part__number, .part-number"
            )
            raw = (await pn_span.inner_text() if pn_span else "").strip()
            part_number = raw.replace("Part #", "").strip()

        if not part_number:
            continue

        # Name + URL
        name_el = await card.query_selector(
            ".mega-m__part__name a, .part-card__title a, h3 a"
        )
        name = (await name_el.inner_text()).strip() if name_el else "Unknown Part"
        href = await name_el.get_attribute("href") if name_el else None
        part_url = (BASE_URL + href) if href and href.startswith("/") else href

        # Price
        price_el = await card.query_selector(
            ".mega-m__part__price, .price, [class*='price']"
        )
        price_text = await price_el.inner_text() if price_el else ""
        price = parse_price(price_text)

        # Brand
        brand_el = await card.query_selector(".mega-m__part__brand, .brand")
        brand = (await brand_el.inner_text()).strip() if brand_el else None

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


async def scrape_part_detail(page: Page, part: dict) -> dict:
    if not part.get("url"):
        return part

    try:
        await page.goto(part["url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(REQUEST_DELAY)
    except Exception as exc:
        log.warning("Could not load %s: %s", part["url"], exc)
        return part

    # Description
    desc_el = await page.query_selector(
        "#Description .js-content, .pd__description, [itemprop='description']"
    )
    if desc_el:
        part["description"] = (await desc_el.inner_text()).strip()[:1000]

    # Brand
    if not part.get("brand"):
        brand_el = await page.query_selector(
            "[itemprop='brand'] [itemprop='name'], .pd__brand"
        )
        if brand_el:
            part["brand"] = (await brand_el.inner_text()).strip()

    # Price
    if not part.get("price"):
        price_el = await page.query_selector(
            "[itemprop='price'], .pd__price__current, .js-partPrice"
        )
        if price_el:
            price_text = (
                await price_el.get_attribute("content")
                or await price_el.inner_text()
            )
            part["price"] = parse_price(price_text)

    # Compatible models
    model_els = await page.query_selector_all(
        "#FitsList .js-collapseList a, .pd__crossref__list a, [data-model-number]"
    )
    models = []
    for el in model_els:
        model_num = (
            await el.get_attribute("data-model-number")
            or (await el.inner_text()).strip()
        )
        if model_num and re.match(r"^[A-Z0-9]{5,}", model_num.upper()):
            models.append(model_num.upper().strip())

    part["compatible_models"] = list(set(models))
    return part


async def scrape_category(
    page: Page, category: str, path: str, max_pages: int
) -> list[dict]:
    parts: list[dict] = []
    seen: set[str] = set()

    for pg in range(1, max_pages + 1):
        separator = "&" if "?" in path else "?"
        url = f"{BASE_URL}{path}{separator}start={(pg - 1) * 24}"
        log.info("Scraping %s page %d: %s", category, pg, url)

        page_parts = await scrape_list_page(page, url, category)
        if not page_parts:
            log.info("No parts found — stopping early for %s", category)
            break

        new_parts = [p for p in page_parts if p["part_number"] not in seen]
        seen.update(p["part_number"] for p in new_parts)

        log.info("Enriching %d new parts ...", len(new_parts))
        for i, part in enumerate(new_parts):
            log.info(
                "  [%d/%d] %s — %s",
                i + 1, len(new_parts), part["part_number"], part["name"]
            )
            enrich = await scrape_part_detail(page, part)
            parts.append(enrich)

    return parts


def build_compatibility_map(products: list[dict]) -> dict[str, list[str]]:
    compat: dict[str, list[str]] = {}
    for product in products:
        for model in product.get("compatible_models", []):
            compat.setdefault(model, [])
            if product["part_number"] not in compat[model]:
                compat[model].append(product["part_number"])
    return compat


async def main():
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    all_products: list[dict] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        for category, path in CATEGORY_URLS.items():
            log.info("=== Scraping category: %s ===", category)
            products = await scrape_category(page, category, path, PAGES_PER_CATEGORY)
            all_products.extend(products)
            log.info("Total for %s: %d parts", category, len(products))

        await browser.close()

    if not all_products:
        log.error("No products scraped.")
        return

    products_path = data_dir / "products.json"
    with open(products_path, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)
    log.info("Wrote %d products to %s", len(all_products), products_path)

    compat = build_compatibility_map(all_products)
    compat_path = data_dir / "compatibility.json"
    with open(compat_path, "w", encoding="utf-8") as f:
        json.dump(compat, f, indent=2, ensure_ascii=False)
    log.info(
        "Wrote compatibility map (%d models) to %s", len(compat), compat_path
    )


if __name__ == "__main__":
    asyncio.run(main())