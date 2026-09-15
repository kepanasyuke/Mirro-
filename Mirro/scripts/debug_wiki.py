# -*- coding: utf-8 -*-
"""Debug Wikipedia API response directly."""
import json, urllib.request, urllib.parse

UA = "Mirro/0.2 (personal AI assistant; contact: mirro@localhost)"

def fetch(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        return {"_error": str(e)}

# 1. Поиск заголовка
q = "Александр Пушкин"
search_url = ("https://ru.wikipedia.org/w/api.php"
              "?action=query&list=search&srsearch=" + urllib.parse.quote(q)
              + "&srlimit=3&format=json")
d = fetch(search_url)
print("SEARCH response:")
if "_error" in d:
    print("  ERROR:", d["_error"])
else:
    print("  keys:", list(d.keys()))
    sr = d.get("query", {}).get("search", [])
    print("  results:", len(sr))
    for s in sr[:3]:
        print(f"    title: {s.get('title', '?')} | id: {s.get('pageid', '?')}")

# 2. Экстракт по первому результату
if sr := d.get("query", {}).get("search", []):
    title = sr[0]["title"]
    ext_url = ("https://ru.wikipedia.org/w/api.php"
               "?action=query&prop=extracts&exintro&explaintext"
               "&titles=" + urllib.parse.quote(title) + "&format=json")
    e = fetch(ext_url)
    print("\nEXTRACT response:")
    if "_error" in e:
        print("  ERROR:", e["_error"])
    else:
        pages = e.get("query", {}).get("pages", {})
        for pid, page in pages.items():
            print(f"  pageid: {pid}")
            print(f"  title: {page.get('title', '?')}")
            extr = page.get("extract", "")
            print(f"  extract len: {len(extr)}")
            print(f"  extract start: {extr[:120]}")