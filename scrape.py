import requests
from bs4 import BeautifulSoup
from urllib.parse import (
    urljoin, urldefrag, urlparse,
    urlunparse, parse_qsl, urlencode
)
import json
from datetime import date
import time
from collections import Counter


URL = "https://asta-fra-uas.de/"

CONTENT_SELECTORS = [
    ".frame-type-text",
    ".frame-type-textmedia",
    ".frame-type-imageTextLink",
    ".frame-type-contentElementBootstrapSlider .item",
    ".frame-type-list article",
]

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
BLOCK_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "table"]

SKIP_EXACT = ("/datenschutz", "/impressum")

NOISE_TEXTS = {
    "Weitere Öffnungszeiten", "Further opening times", "News",
    "Mehr Information…", "More Information…", "More Information",
    "Your Content Goes Here",
}

NOISE_SELECTORS = [
    ".hidden-lg",
    ".sr-only",
    ".my_calendar_mini_widget",
    ".mc-main",
    ".fusion-mobile-tab-nav",
    ".custom-startseite",
]

PROMOTE_SELECTORS = [".currency"]

SKIP_PATTERNS = ("/author/", "/page/", "/feed/", "/tag/", "/category/", "/wp-json/", "/wp-admin/")
SKIP_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".zip", ".docx", ".xlsx", ".mp4")


def is_crawlable(url):
    path = urlparse(url).path.lower()
    if path.endswith(SKIP_EXTENSIONS) or path in SKIP_EXACT:
        return False
    if path.startswith("/download/"):
        return False
    return not any(pattern in path + "/" for pattern in SKIP_PATTERNS)

def normalize_url(url):
    # Remove the fragment, e.g. #section
    url = urldefrag(url)[0]

    parts = urlparse(url)

    # Remove tracking parameters
    tracking_prefixes = ("mtm_", "utm_")
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query)
        if not key.lower().startswith(tracking_prefixes)
    ]

    # Remove trailing slash, except for the homepage
    path = parts.path.rstrip("/") or "/"

    # Rebuild the URL without its fragment
    return urlunparse((
        "https",
        parts.netloc.lower(),
        path,
        parts.params,
        urlencode(query),
        ""
    ))


def clean_text(el):
    text = el.get_text(" ", strip=True)
    text = text.replace("&shy;", "").replace("\u00ad", "")
    return " ".join(text.split())

def table_to_text(table):
    lines = []
    for row in table.find_all("tr"):
        cells = [cell_text(c) for c in row.find_all(["th", "td"])]
        cells = [c for c in cells if c]
        if len(cells) >= 2:
            lines.append(f"{cells[0]}: {' '.join(cells[1:])}")
        elif cells:
            lines.append(cells[0])
    return "\n".join(lines)

#fix for span blocks inside tables, so that hours remain attached to a day
def cell_text(cell):
    spans = cell.find_all("span", recursive=False)
    if len(spans) > 1:
        parts = [clean_text(s) for s in spans]
        return ", ".join(p for p in parts if p)
    return clean_text(cell)

def make_unit(el, base_url):
    link = el.select_one("a.img-text-link__link")
    if link:
        return {
            "kind": "link",
            "text": clean_text(link),
            "url": urljoin(base_url, link.get("href", "").split("?")[0]),
        }

    text = clean_text(el)
    if not text:
        return None

    heading = el.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    if heading and clean_text(heading) == text:
        return {"kind": "heading", "text": text}

    return {"kind": "text", "text": text}





def extract_chunks(area, default_section):
    chunks = []
    headings = []
    section = default_section
    parts = []

    for el in area.find_all(BLOCK_TAGS):
        if el.find_parent(BLOCK_TAGS):
            continue
        text = table_to_text(el) if el.name == "table" else clean_text(el)
        if not text or text in NOISE_TEXTS:
            continue

        if el.name in HEADING_TAGS:
            if parts:
                chunks.append({"section": section, "text": section + "\n" + "\n".join(parts)})
                parts = []
                headings = []
            headings.append(text)
            section = " – ".join(headings[-2:])
        else:
            parts.append(text)

    if parts:
        chunks.append({"section": section, "text": section + "\n" + "\n".join(parts)})
    return chunks

def save_jsonl(chunks, page_url, page_title, filename):
    with open(filename, "a", encoding="utf-8") as f:
        path = urlparse(page_url).path
        lang = "en" if path == "/en" or path.startswith("/en/") else "de"
        for chunk in chunks:
            record = {
                "text": chunk["text"],
                "section": chunk["section"],
                "page_title": page_title,
                "url": page_url,
                "scraped_at": date.today().isoformat(),
                "lang": lang
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def fetch(url):
    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    if "text/html" not in response.headers.get("Content-Type", ""):
        return None
    return response


def find_links(soup, page_url, domain):
    links = set()

    for a in soup.find_all("a", href=True):
        raw_url = urljoin(page_url, a["href"])
        link = normalize_url(raw_url)

        parts = urlparse(link)

        if (
            parts.scheme in ("http", "https")
            and parts.netloc == domain
            and is_crawlable(link)
        ):
            links.add(link)

    return links


def process_page(url, domain):
    response = fetch(url)
    if response is None:
        return set()
    soup = BeautifulSoup(response.content, "html.parser")
    links = find_links(soup, url, domain)          # before removing anything
    for el in soup.select(", ".join(NOISE_SELECTORS)):
        el.decompose()
    for el in soup.select(", ".join(PROMOTE_SELECTORS)):
        el.parent.name = "p"
    page_title = clean_text(soup.title) if soup.title else url
    area = soup.select_one(".post-content")
    chunks = extract_chunks(area, default_section=page_title) if area else []
    print(f"   {len(chunks)} chunks")
    save_jsonl(chunks, url, page_title, "chunks.jsonl")
    return links


# Crawl function
def crawl(start_url, max_pages=200):
    domain = urlparse(start_url).netloc

    # URLs waiting to be processed
    queue = [normalize_url(start_url)]

    # URLs we have already attempted
    visited = set()

    # Start with an empty output file
    with open("chunks.jsonl", "w", encoding="utf-8"):
        pass

    while queue and len(visited) < max_pages:
        url = queue.pop(0)

        if url in visited:
            continue

        print(f"[{len(visited) + 1}/{max_pages}] Crawling: {url}")

        # Mark the URL as visited before processing
        visited.add(url)

        links = process_page(url, domain)

        # Add newly discovered links to the queue
        for link in sorted(links):
            link = normalize_url(link)

            if link not in visited and link not in queue:
                queue.append(link)

        # Wait between requests
        if queue and len(visited) < max_pages:
            time.sleep(1)

    print(f"\nFinished. Pages attempted: {len(visited)}")
    print(f"Pages remaining in queue: {len(queue)}")



# main stuff
if __name__ == "__main__":
    crawl(URL, max_pages=200)

with open("chunks.jsonl", encoding="utf-8") as f:
    records = [json.loads(line) for line in f]

page_counts = {}

for record in records:
    url = record["url"]
    page_counts[url] = page_counts.get(url, 0) + 1

for url, count in page_counts.items():
    print(count, "records:", url)

print("Total records:", len(records))