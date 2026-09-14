#!/usr/bin/env python3
"""Show Mirro current status summary."""
import sys
sys.path.insert(0, r'D:\Mirro\core')
exec(open(r'D:\Mirro\core\mirro_core.py', encoding='utf-8').read())

c = MirroCore()
s = c.status()
print('')
print('=' * 60)
print('  MIRRO — СТАТУС ПРОЕКТА')
print('=' * 60)
print('  Ядро: http://127.0.0.1:3443')
print('  Всего примеров: {:,}'.format(s['total_examples']))
print('  Вызовов: {}'.format(s['total_calls']))
print('  Кластеров: {}'.format(len(s['clusters'])))
print()
print('  КЛАСТЕРЫ ЗНАНИЙ:')
for name, info in sorted(s['clusters'].items(), key=lambda x: -x[1]['examples']):
    print('    {:<16} {:>8,} примеров'.format(name, info['examples']))
print()

# Project structure
from pathlib import Path
base = Path(r'D:\Mirro')
print('  СТРУКТУРА:')
for p in sorted(base.rglob('*.py')):
    print('    {:<40} {} KB'.format(str(p.relative_to(base)), p.stat().st_size // 1024))
print()

# Catalog count
cat = base / 'data' / 'catalog_phase1.json'
if cat.exists():
    import json
    data = json.loads(cat.read_text('utf-8'))
    from collections import Counter
    c2 = Counter(e['cat'] for e in data)
    print('  КАТАЛОГ: {} датасетов'.format(len(data)))
    for k, v in sorted(c2.items(), key=lambda x: -x[1]):
        print('    {:<16} {}'.format(k, v))