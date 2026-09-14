# -*- coding: utf-8 -*-
"""Probe which open knowledge APIs are reachable from this PC."""
import json, urllib.request, urllib.parse, socket

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/0.2"

def probe(name, url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            return f"OK  ({len(data)//1024} KB) {name}"
    except Exception as e:
        err = str(e)[:60]
        return f"FAIL {name}: {err}"

tests = [
    ("Wikipedia RU", "https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch=test&srlimit=1&format=json"),
    ("Wikipedia EN", "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=test&srlimit=1&format=json"),
    ("Wikidata", "https://www.wikidata.org/w/api.php?action=query&list=search&srsearch=test&srlimit=1&format=json"),
    ("Open Library", "https://openlibrary.org/search.json?q=python&limit=1"),
    ("Free Dictionary", "https://api.dictionaryapi.dev/api/v2/entries/en/hello"),
    ("Nasa", "https://images-api.nasa.gov/search?q=moon&media_type=image&page_size=1"),
    ("Dog API", "https://dog.ceo/api/breeds/image/random"),
    ("Joke API", "https://official-joke-api.appspot.com/random_joke"),
    ("Agify (имя→возраст)", "https://api.agify.io/?name=michael"),
    ("Yandex wiki-mirror? no", "none"),
]

for name, url in tests:
    if url == "none":
        continue
    print(probe(name, url))
    socket.setdefaulttimeout(3)  # not used but harmless