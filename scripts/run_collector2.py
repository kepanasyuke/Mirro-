#!/usr/bin/env python3
"""Run collector - proper import, no exec()."""
import sys
sys.path.insert(0, r'D:\Mirro\scripts')
from collector import ReferenceCollector

c = ReferenceCollector()
print('Starting collection...')
total = 0
queries = ['poster design', 'typography poster', 'color palette',
           'magazine layout', 'logo design', 'flat illustration',
           'abstract art', 'character design', 'landscape illustration',
           'nature landscape', 'architecture design', 'interior design']

for q in queries:
    n1 = c.collect_wikimedia(q, 4)
    n2 = c.collect_met(q, 4)
    total += (n1 or 0) + (n2 or 0)
    print(f'  {q[:30]:30} wikimedia={n1} met={n2}')

c._save_catalog()
print(f'Done. Total: {total} references, catalog: {len(c.catalog)}')

import random
for r in random.sample(c.catalog, min(5, len(c.catalog))):
    src = r.get('source', '?')
    title = r.get('title', '')[:50]
    print(f'  [{src}] {title}')