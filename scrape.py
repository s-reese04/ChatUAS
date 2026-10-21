import requests
from bs4 import BeautifulSoup
from urllib.parse import (
    urljoin, urldefrag, urlparse,
    urlunparse, parse_qsl, urlencode
)
import json
from datetime import date
import time


URL = "https://www.frankfurt-university.de/"

CONTENT_SELECTORS = [
    ".frame-type-text",
    ".frame-type-textmedia",
    ".frame-type-imageTextLink",
    ".frame-type-contentElementBootstrapSlider .item",
    ".frame-type-list article",
]


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
        parts.scheme.lower(),
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


def extract_units(soup, base_url):
    units = []
    for area in soup.select("div.top-content, div#main-content"):
        for el in area.select(", ".join(CONTENT_SELECTORS)):
            unit = make_unit(el, base_url)
            if unit:
                unit["frames"] = [p.get("id", "?") for p in el.find_parents("div", class_="frame")]
                units.append(unit)
    return units

def group_links(units):
    grouped = []
    for unit in units:
        if unit["kind"] == "link" and grouped and grouped[-1]["kind"] == "linklist":
            grouped[-1]["items"].append(unit)
        elif unit["kind"] == "link":
            grouped.append({"kind": "linklist", "items": [unit]})
        else:
            grouped.append(unit)
    return grouped


def attach_headings(units, default_section=""):
    chunks = []
    heading = None
    for unit in units:
        if unit["kind"] == "heading":
            heading = unit
            continue

        if unit["kind"] == "linklist":
            frames = unit["items"][0]["frames"]
            text = "\n".join(f"{i['text']}: {i['url']}" for i in unit["items"])
        else:
            frames = unit["frames"]
            text = unit["text"]

        if heading and set(heading["frames"]) & set(frames):
            section = heading["text"]
        else:
            section = default_section

        chunks.append({"section": section, "text": text})
    return chunks

def save_jsonl(chunks, page_url, page_title, filename):
    with open(filename, "a", encoding="utf-8") as f:
        for chunk in chunks:
            record = {
                "text": chunk["text"],
                "section": chunk["section"],
                "page_title": page_title,
                "url": page_url,
                "scraped_at": date.today().isoformat(),
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
        ):
            links.add(link)

    return links


def process_page(url, domain):
    response = fetch(url)
    if response is None:
        return set()
    soup = BeautifulSoup(response.content, "html.parser")
    links = find_links(soup, url, domain)          # before removing anything
    for el in soup.select(".hidden-lg, .sr-only"):
        el.decompose()
    page_title = clean_text(soup.title) if soup.title else url
    units = extract_units(soup, url)
    chunks = attach_headings(group_links(units), default_section=page_title)
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
    crawl(URL, max_pages=5)

with open("chunks.jsonl", encoding="utf-8") as f:
    records = [json.loads(line) for line in f]

page_counts = {}

for record in records:
    url = record["url"]
    page_counts[url] = page_counts.get(url, 0) + 1

for url, count in page_counts.items():
    print(count, "records:", url)

print("Total records:", len(records))