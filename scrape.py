import requests
from bs4 import BeautifulSoup


URL = "https://www.frankfurt-university.de/"

response = requests.get(URL, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

for el in soup.select(".hidden-lg, .sr-only"):
    el.decompose()

text = soup.get_text(separator="\n", strip=True)

def clean_text(el):
    text = el.get_text(" ", strip=True)
    text = text.replace("&shy;", "").replace("\u00ad", "")
    return " ".join(text.split())


UNIT_SELECTORS = [
    ".frame-type-text",
    ".frame-type-textmedia",
    ".frame-type-contentElementBootstrapSlider .item",
    ".frame-type-list article",
]

units = []
areas = soup.select("div.top-content, div#main-content")

MIN_LENGTH = 80


def merge_short(units):
    merged = []
    pending = ""
    for text in units:
        if len(text) < MIN_LENGTH:
            pending = (pending + " " + text).strip()
        else:
            merged.append((pending + " " + text).strip())
            pending = ""
    if pending:
        merged.append(pending)
    return merged

units = []
for area in soup.select("div.top-content, div#main-content"):
    for el in area.select(", ".join(UNIT_SELECTORS)):
        text = clean_text(el)
        if text:
            units.append(text)

units = merge_short(units)

with open("units.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(units))
