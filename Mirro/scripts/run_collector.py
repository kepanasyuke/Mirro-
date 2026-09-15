#!/usr/bin/env python3
"""Run collector on first 5 queries to build initial reference catalog."""
import sys
sys.path.insert(0, r'D:\Mirro\scripts')
exec(open(r'D:\Mirro\scripts\collector.py', encoding='utf-8').read())

c = ReferenceCollector()
print('Collecting references from Wikimedia + MetMuseum...')
n = 0
for q in DESIGN_QUERIES[:5]:
    n += c.collect_wikimedia(q, 5)
    n += c.collect_met(q, 5)
c._save_catalog()
print(f'Total collected: {n}')
print(f'Catalog size: {len(c.catalog)}')
for r in c.catalog[-10:]:
    src = r.get("source", "?")
    title = r.get("title", "")[:50]
    print(f'  [{src}] {title}')