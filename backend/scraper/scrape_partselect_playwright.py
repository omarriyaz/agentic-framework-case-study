"""
PartSelect scraper — BFS crawl of part detail pages.

Starts from seed URLs, extracts linked part URLs from each page,
and crawls outward keeping only Refrigerator and Dishwasher parts.

Usage (from backend/):
    python -m scraper.scrape_partselect_playwright

Appends to data/products.json and rebuilds data/compatibility.json.
Skips part numbers that are already present in products.json.

Requirements:
    pip install playwright
    playwright install chromium
"""

import asyncio
import json
import re
import logging
from collections import deque
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://www.partselect.com"
TARGET_NEW_PARTS = 60
REQUEST_DELAY = 1200  # ms between page loads

STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
window.chrome = { runtime: {} };
const origQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (p) =>
    p.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : origQuery(p);
"""

WANTED_CATEGORIES = {
    "Refrigerator": ["refrigerator", "fridge", "freezer", "ice-maker", "ice-machine", "crisper", "evaporator"],
    "Dishwasher": ["dishwasher", "dishrack", "dish-rack", "spray-arm"],
}

SKIP_KEYWORDS = [
    "washer", "dryer", "oven", "range", "microwave", "stove", "cooktop",
    "lint", "drum", "bellow", "agitator", "suspension-rod",
    "affresh-washing", "maintenance-kit-dryer",
]

SEED_URLS = [
    # Refrigerator
    "/PS11752778-Whirlpool-WPW10321304-Refrigerator-Door-Shelf-Bin.htm",
    "/PS11739119-Whirlpool-WP2188656-Refrigerator-Crisper-Drawer-with-Humidity-Control.htm",
    "/PS11739697-Whirlpool-WP2211581-Cantilever-Shelf-Glass-Included.htm",
    "/PS11740306-Whirlpool-WP2309941-Door-Shelf.htm",
    "/PS11738120-Whirlpool-W10873791-Refrigerator-Ice-Maker.htm",
    "/PS11751711-Whirlpool-WPW10276341-Refrigerator-Shelf-Frame-with-Glass.htm",
    "/PS11751713-Whirlpool-WPW10276348-Refrigerator-Slide-Out-Shelf-with-Glass.htm",
    "/PS11752389-Whirlpool-WPW10300022-Refrigerator-Ice-Maker-Replacement.htm",
    "/PS11753329-Whirlpool-WPW10347093-Ice-Container.htm",
    "/PS11759515-Whirlpool-W10830162-Door-Gasket-Gray.htm",
    "/PS11765620-Whirlpool-W10884390-Refrigerator-Ice-Maker-Assembly.htm",
    "/PS11723190-Whirlpool-W10827015-Refrigerator-Pantry-Drawer-Door-Cover.htm",
    "/PS12348013-Whirlpool-W11165546-Water-Inlet-Valve.htm",
    "/PS12347929-Whirlpool-W11162443-Crisper-Drawer.htm",
    "/PS12741350-GE-WR60X31522-Evaporator-Fan-Motor.htm",
    "/PS12364147-Frigidaire-241798231-Refrigerator-Ice-Maker-Assembly.htm",
    "/PS12364199-Frigidaire-242193213-Refrigerator-Door-Shelf-Bin.htm",
    "/PS12578777-Whirlpool-W11239961-Door-Shelf-Bin.htm",
    "/PS16555201-Whirlpool-W11527432-LED-Light-Module.htm",
    "/PS1993870-GE-WR30X10093-Ice-Maker.htm",
    "/PS429724-Frigidaire-240323001-Refrigerator-Door-Bin.htm",
    "/PS429854-Frigidaire-240337103-Refrigerator-Crisper-Pan.htm",
    "/PS429868-Frigidaire-240337901-Refrigerator-Door-Shelf-Retainer-Bin.htm",
    "/PS430122-Frigidaire-240356402-Door-Bin-Clear.htm",
    "/PS11704498-Frigidaire-EPTWFU01-Refrigerator-Water-Filter-White.htm",
    "/PS11701542-Whirlpool-EDR1RXD1-Refrigerator-Ice-and-Water-Filter.htm",
    "/PS11722128-Whirlpool-EDR3RXD1-Whirlpool-EveryDrop3-Refrigerator-Water-Filter.htm",
    "/PS7784018-Frigidaire-242252702-Refrigerator-Water-Inlet-Valve.htm",
    "/PS7784009-Frigidaire-242193213-Refrigerator-Door-Gasket.htm",
    "/PS17990263-Frigidaire-241778315-GASKET-DR-MAGNETIC-FF-WH-36.htm",
    "/PS11770643-Frigidaire-5304507199-Freezer-Door-Gasket.htm",
    "/PS17626598-GE-WR29X43994-Ice-Bucket-Auger-Assembly.htm",
    # Dishwasher
    "/PS8260087-Whirlpool-W10518394-Dishwasher-Heating-Element.htm",
    "/PS3406971-Whirlpool-W10195416-Lower-Dishrack-Wheel.htm",
    "/PS10057160-Whirlpool-W10728159-Lower-Dishrack.htm",
    "/PS10065979-Whirlpool-W10712395-Upper-Rack-Adjuster-Kit-White-Wheels-Left-and-Right-Sides.htm",
    "/PS11750057-Whirlpool-WPW10195417-Lower-Dishrack-Wheel-Assembly.htm",
    "/PS11756150-Whirlpool-WPW10546503-Dishwasher-Upper-Rack-Adjuster.htm",
    "/PS12585623-Frigidaire-5304517203-Lower-Spray-Arm.htm",
    "/PS12749241-GE-WD28X25960-Complete-Lower-Service-Rack-Assembly.htm",
    "/PS16543613-Whirlpool-W11527890-Dishrack.htm",
    "/PS17219658-Frigidaire-5304535379-Lower-Rack-Assembly-Grey.htm",
    "/PS17219659-Frigidaire-5304535380-Upper-Rack-Assembly-Grey.htm",
    "/PS18351367-GE-WD28X35779-UPPER-RACK.htm",
    "/PS17873657-GE-WD28X34744-LOWER-RACK.htm",
    "/PS17137050-GE-WD21X24901C-Main-Electronic-Control-Panel.htm",
    "/PS16744838-Whirlpool-W11603810-Electronic-Control-Board.htm",
    "/PS16618974-GE-WD28X28918-Lower-Rack-And-Swb-Replacement-Kit.htm",
    "/PS18375870-Bosch-20007189-CROCKERY-BASKET.htm",
]

PART_URL_RE = re.compile(r'(?:href="|href=\')(/PS\d+[^"\'?#\s]+\.htm)', re.IGNORECASE)


def categorize_url(url: str) -> Optional[str]:
    url_lower = url.lower()
    for kw in SKIP_KEYWORDS:
        if kw in url_lower:
            return None
    for category, keywords in WANTED_CATEGORIES.items():
        if any(kw in url_lower for kw in keywords):
            return category
    return "Refrigerator"


def parse_price(text: str) -> Optional[float]:
    m = re.search(r'\$\s*([\d,]+\.\d{2})', text.replace(',', ''))
    return float(m.group(1)) if m else None


async def make_page(pw):
    browser = await pw.chromium.launch(
        headless=False,
        slow_mo=50,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
    )
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        timezone_id="America/New_York",
        extra_http_headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
        },
    )
    await context.add_init_script(STEALTH_SCRIPT)
    return browser, await context.new_page()


async def scrape_part(page: Page, slug: str, category_hint: str) -> Optional[tuple]:
    url = BASE_URL + slug
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(REQUEST_DELAY)
    except Exception as exc:
        log.warning("Failed to load %s: %s", url, exc)
        return None

    title = await page.title()
    if "access denied" in title.lower() or "404" in title.lower():
        return None

    html = await page.content()

    name_el = await page.query_selector("h1.title-lg, h1.pd__name, h1[itemprop='name'], h1")
    name = (await name_el.inner_text()).strip() if name_el else title.split("–")[0].strip()
    if "not found" in name.lower():
        return None
    name = re.sub(r'^Official\s+\w+\s+\S+\s+', '', name).strip() or name

    brand_el = await page.query_selector("[itemprop='brand'] [itemprop='name'], .pd__brand")
    if brand_el:
        brand = (await brand_el.inner_text()).strip()
    else:
        m = re.match(r"Official\s+(\w+)", title)
        brand = m.group(1) if m else None

    price = None
    try:
        await page.wait_for_selector("span[itemprop='price']", timeout=6000)
    except Exception:
        pass
    price_el = await page.query_selector("span[itemprop='price']")
    if price_el:
        raw = await price_el.get_attribute("content")
        if raw:
            try:
                price = float(raw)
            except ValueError:
                price = parse_price(raw)
    if not price:
        js_el = await page.query_selector(".js-partPrice")
        if js_el:
            price = parse_price(await js_el.inner_text())

    description = None
    for sel in ["#Description .js-content", ".pd__description", "[itemprop='description']"]:
        el = await page.query_selector(sel)
        if el:
            description = (await el.inner_text()).strip()[:1200]
            if description:
                break

    category = category_hint
    bc_el = await page.query_selector(".breadcrumbs, nav[aria-label='breadcrumb'], .bread-crumb")
    if bc_el:
        bc_text = (await bc_el.inner_text()).lower()
        if "dishwasher" in bc_text:
            category = "Dishwasher"
        elif "refrigerator" in bc_text or "freezer" in bc_text:
            category = "Refrigerator"

    models = []
    for sel in ["#FitsList a", ".pd__crossref__list a", "[data-model-number]", ".js-modelList a"]:
        els = await page.query_selector_all(sel)
        for el in els:
            model = await el.get_attribute("data-model-number") or (await el.inner_text()).strip()
            if model and re.match(r'^[A-Z0-9]{4,}', model.upper()):
                models.append(model.upper().strip())
        if models:
            break

    pn_match = re.match(r'/?(PS\d+)', slug)
    part_number = pn_match.group(1) if pn_match else slug

    new_slugs = {
        match.group(1).split('?')[0]
        for match in PART_URL_RE.finditer(html)
        if categorize_url(match.group(1))
    }

    log.info(
        "  ✓ %s | %s | %s | $%.2f | %d models | %d new URLs",
        part_number, category,
        (name[:40] + "...") if len(name) > 40 else name,
        price or 0, len(models), len(new_slugs),
    )

    return {
        "part_number": part_number,
        "name": name,
        "price": price,
        "brand": brand,
        "category": category,
        "url": url,
        "description": description,
        "compatible_models": list(set(models)),
    }, new_slugs


def build_compatibility_map(products: list[dict]) -> dict[str, list[str]]:
    compat: dict[str, list[str]] = {}
    for p in products:
        for model in p.get("compatible_models", []):
            compat.setdefault(model, [])
            if p["part_number"] not in compat[model]:
                compat[model].append(p["part_number"])
    return compat


def save(data_dir: Path, products: list[dict]) -> None:
    with open(data_dir / "products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    with open(data_dir / "compatibility.json", "w", encoding="utf-8") as f:
        json.dump(build_compatibility_map(products), f, indent=2, ensure_ascii=False)
    log.info("Saved %d products", len(products))


async def main():
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    products_path = data_dir / "products.json"
    products = json.loads(products_path.read_text()) if products_path.exists() else []
    log.info("Loaded %d existing products", len(products))

    already_scraped = {p["part_number"] for p in products}

    queue: deque[str] = deque()
    seen: set[str] = set()
    for slug in SEED_URLS:
        slug = slug.split('?')[0]
        if slug not in seen:
            seen.add(slug)
            queue.append(slug)

    new_count = 0

    async with async_playwright() as pw:
        browser, page = await make_page(pw)

        log.info("Warming up on homepage...")
        try:
            await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1500)
        except Exception:
            pass

        while queue and new_count < TARGET_NEW_PARTS:
            slug = queue.popleft()
            category_hint = categorize_url(slug) or "Refrigerator"

            pn_match = re.match(r'/?(PS\d+)', slug)
            if pn_match and pn_match.group(1) in already_scraped:
                continue

            log.info("[+%d/%d] %s", new_count + 1, TARGET_NEW_PARTS, slug)

            result = await scrape_part(page, slug, category_hint)
            if result is None:
                continue

            part, new_slugs = result

            if part["part_number"] in already_scraped:
                for s in new_slugs:
                    if s not in seen:
                        seen.add(s)
                        queue.append(s)
                continue

            already_scraped.add(part["part_number"])
            products.append(part)
            new_count += 1

            for s in new_slugs:
                if s not in seen:
                    seen.add(s)
                    queue.append(s)

            if new_count % 10 == 0:
                save(data_dir, products)

        await browser.close()

    save(data_dir, products)
    log.info("Done — %d total parts (%d new).", len(products), new_count)


if __name__ == "__main__":
    asyncio.run(main())
