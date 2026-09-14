# -*- coding: utf-8 -*-
"""Test web search speed with cache + parallelism."""
import sys, time
sys.path.insert(0, r"D:\Mirro")
from scripts.thinking import thinking

q = "кто такой Александр Пушкин"

# Холодный поиск (без кэша, параллельный ru/en)
t0 = time.time()
r1 = thinking.web_search(q)
t1 = time.time()
print(f"Холодный поиск: {t1-t0:.1f}с")
print(f"  Title: {r1.get('title')}")
print(f"  Source: {r1.get('source')}")

# Тёплый поиск (с кэшем)
t2 = time.time()
r2 = thinking.web_search(q)
t3 = time.time()
print(f"Тёплый (кэш): {t3-t2:.3f}с")
print(f"  Same result: {r1.get('title') == r2.get('title')}")
print(f"  Кэш размер: {len(thinking.web_cache)} записей")