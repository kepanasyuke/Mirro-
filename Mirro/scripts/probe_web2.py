# -*- coding: utf-8 -*-
"""Probe web knowledge sources reachable from this PC (non-Wikipedia)."""
import json, urllib.request, urllib.parse, time

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/0.2"

def probe(name, url, timeout=12, parse=None):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        dt = time.time() - t0
        if parse:
            result = parse(data)
            return f"OK {name} ({dt:.1f}s): {result}"
        return f"OK {name} ({dt:.1f}s, {len(data)} B)"
    except Exception as e:
        return f"FAIL {name}: {str(e)[:55]}"

# 1. Open Library - work search with description
def ol_parse(data):
    d = json.loads(data)
    works = d.get("docs", [])
    if not works:
        return "нет результата"
    w = works[0]
    return f"{w.get('title','')[:40]}"
print(probe("Open Library search", "https://openlibrary.org/search.json?q=Пушкин&limit=1", parse=ol_parse))

# 2. Open Library - subjects
def ol_subject(data):
    d = json.loads(data)
    w = d.get("works", [])
    return f"{len(w)} работ" if w else "пусто"
print(probe("Open Library subjects", "https://openlibrary.org/subjects/poetry.json?limit=1", parse=ol_subject))

# 3. Quotable API (цитаты, работает обычно)
def quote_parse(data):
    d = json.loads(data)
    return f"'{d.get('content','')[:40]}' - {d.get('author','')}"
print(probe("Quotable", "https://api.quotable.io/quotes/random", parse=quote_parse))

# 4. Wikipedia via wikimirror/public CDN (raw REST, иногда проходит иначе)
def wiki_parse(data):
    d = json.loads(data)
    q = d.get("query", {}).get("search", [])
    return q[0]["title"] if q else "нет"
print(probe("Wikipedia RU API (повтор)", "https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch=пушкин&srlimit=1&format=json", parse=wiki_parse))

# 5. Vikidia (детская вики, другой домен)
def viki_parse(data):
    d = json.loads(data)
    q = d.get("query", {}).get("search", [])
    return q[0]["title"] if q else "нет"
print(probe("Wikidata Q-item", "https://www.wikidata.org/w/api.php?action=query&list=search&srsearch=pushkin&srlimit=1&format=json", parse=viki_parse))

# 6. DuckDuckGo Instant Answer (wiki summaries, TLS? проверим)
def ddg_parse(data):
    d = json.loads(data)
    return d.get("AbstractText", "")[:60] or d.get("Heading", "") or "нет"
print(probe("DuckDuckGo Instant", "https://api.duckduckgo.com/?q=pushkin&format=json&no_html=1", parse=ddg_parse))