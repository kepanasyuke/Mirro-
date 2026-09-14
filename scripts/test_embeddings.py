# -*- coding: utf-8 -*-
"""Прогон самообучения Mirro (Word2Vec + семантика) с выводом в файл."""
import sys, io, time

sys.path.insert(0, r"D:\Mirro")

t0 = time.time()
print("Загрузка алгоритмов...", flush=True)
from scripts.algorithms import algo
print(f"Загружено за {time.time()-t0:.1f}s", flush=True)

print("Кол-во word_vectors:", len(algo.word_vectors), flush=True)
print("Размер cooc:", len(algo.cooc_matrix), flush=True)

# Пробуем найти соседей слова (семантика)
def neighbors(word, top=5):
    wv = algo.word_vectors.get(word)
    if not wv:
        return []
    scored = []
    for w, v in algo.word_vectors.items():
        if w == word:
            continue
        # косинус
        dot = sum(a*b for a,b in zip(wv, v))
        na = sum(x*x for x in wv) ** 0.5
        nb = sum(x*x for x in v) ** 0.5
        if na and nb:
            scored.append((dot/(na*nb), w))
    scored.sort(key=lambda x: -x[0])
    return [w for _, w in scored[:top]]

for w in ["налог", "python", "код", "машина"]:
    n = neighbors(w)
    print(f"Соседи слова '{w}': {n}", flush=True)