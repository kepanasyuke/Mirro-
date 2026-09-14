# -*- coding: utf-8 -*-
"""Test Mirro web_search with Wikidata source."""
import sys, time
sys.path.insert(0, r"D:\Mirro")
from scripts.thinking import thinking

tests = [
    "кто такой Александр Пушкин",
    "что такое НДС",
    "кто такой Ломоносов",
]

for q in tests:
    t0 = time.time()
    r = thinking.web_search(q)
    dt = time.time() - t0
    print(f"Q: {q}")
    print(f"  [{dt:.1f}s] source={r.get('source')} title={r.get('title')!r}")
    print(f"  summary: {r.get('summary','')[:140]}")
    print(f"  url: {r.get('url')}")
    print()

# Тёплый кэш
t0 = time.time()
r = thinking.web_search("кто такой Александр Пушкин")
print(f"Кэш: {time.time()-t0:.3f}s, source={r.get('source')}")