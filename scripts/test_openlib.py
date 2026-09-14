# -*- coding: utf-8 -*-
"""Test reachable APIs for knowledge content."""
import json, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/0.2"

def fetch(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None

# Open Library - subject search (encyclopedic)
for q in ["finance", "python", "history"]:
    data = fetch(f"https://openlibrary.org/subjects/{q}.json?limit=2")
    if data:
        d = json.loads(data)
        works = d.get("works", [])
        print(f"Open Library '{q}': {len(works)} works")
        for w in works[:2]:
            print(f"  {w.get('title','')[:60]} — {w.get('authors',[{}])[0].get('name','')[:30]}")
    else:
        print(f"Open Library '{q}': no response")

# Dog API (работает)
data = fetch("https://dog.ceo/api/breeds/list/all")
if data:
    d = json.loads(data)
    breeds = list(d.get("message", {}).keys())
    print(f"Dog API: {len(breeds)} пород (ok)")
else:
    print("Dog API: FAIL")

# Joke API (работает)
data = fetch("https://official-joke-api.appspot.com/random_joke")
if data:
    d = json.loads(data)
    print(f"Joke API: {d.get('setup','')[:50]} -> {d.get('punchline','')[:40]}")
else:
    print("Joke API: FAIL")