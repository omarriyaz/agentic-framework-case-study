"""
Test if individual part detail pages are accessible. Also tests their search endpoint.
"""
import requests, re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

s = requests.Session()
s.headers.update(HEADERS)

urls_to_test = [
    "https://www.partselect.com/PS11752778-Whirlpool-W10195416V-Ice-Maker-Assembly.htm",
    "https://www.partselect.com/PS11752778.htm",
    "https://www.partselect.com/Dishwasher-Parts.htm",
    "https://www.partselect.com/api/search/?q=ice+maker&category=Refrigerator",
]

for url in urls_to_test:
    try:
        r = s.get(url, timeout=10)
        print(f"[{r.status_code}] {url}")
        if r.status_code == 200:
            text = r.text
            body = text[text.find('<body'):text.find('<body')+400] if '<body' in text else text[:400]
            print("  Preview:", body[:300].replace('\n', ' ').strip())
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
    print()
