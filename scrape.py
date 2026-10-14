import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from datetime import date


URL = "https://www.frankfurt-university.de/"

CONTENT_SELECTORS = [
    ".frame-type-text",
    ".frame-type-textmedia",
    ".frame-type-imageTextLink",
    ".frame-type-contentElementBootstrapSlider .item",
    ".frame-type-list article",
]

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

# main stuff
response = requests.get(URL, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

for el in soup.select(".hidden-lg, .sr-only"):
    el.decompose()

units = extract_units(soup, URL)
page_title = clean_text(soup.title)
chunks = attach_headings(group_links(units), default_section=page_title)

save_jsonl(chunks, URL, page_title, "chunks.jsonl")

with open("units.txt", "w", encoding="utf-8") as f:
    for chunk in chunks:
        f.write(f"[{chunk['section']}]\n{chunk['text']}\n\n")

with open("chunks.jsonl", encoding="utf-8") as f:
    records = [json.loads(line) for line in f]

print(len(records), "records")
print(records[0])
