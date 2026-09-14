# -*- coding: utf-8 -*-
"""Test DuckDuckGo Instant Answer for knowledge summaries."""
import json, urllib.request, urllib.parse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/0.2"

def ddg(q):
    url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(q)}&format=json&no_html=1&skip_disambig=1"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))

for q in ["Александр Пушкин", "Налог на добавленную стоимость", "python programming language", "кто такой Ломоносов"]:
    try:
        d = ddg(q)
        head = d.get("Heading", "")
        abstract = d.get("AbstractText", "")
        url = d.get("AbstractURL", "")
        print(f"Q: {q}")
        print(f"  Heading: {head}")
        print(f"  Abstract: {abstract[:120]}")
        print(f"  URL: {url}")
        related = d.get("RelatedTopics", [])
        print(f"  Related: {len(related)}")
        print()
    except Exception as e:
        print(f"Q: {q} → ERROR {e}")