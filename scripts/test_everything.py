# -*- coding: utf-8 -*-
"""Тест: автообучалка + новые алгоритмы на сервере."""
import json, sys, time, urllib.request

HOST = "http://127.0.0.1:3443"

def api(method, path, data=None):
    url = HOST + path
    req = urllib.request.Request(url, method=method,
        headers={"Content-Type": "application/json", "User-Agent": "MirroTest/1.0"},
        data=json.dumps(data).encode("utf-8") if data else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"_error": str(e)}

print("1. Health:")
h = api("GET", "/health")
print(f"   {h.get('total_examples', '?')} примеров")
print(f"   clusters: {len(h.get('clusters', {}))}")
na = h.get("algorithms", {}).get("new_algorithms", {})
print(f"   новые: {list(na.keys()) if na else 'нет'}")

print("\n2. Чат (база): прямые вопросы")
for q in [
    "Что такое НДС?",
    "Как заменить mspaint на маке?",
    "Напиши код на Python для сортировки",
]:
    r = api("POST", "/v1/chat/completions", {"messages": [{"role": "user", "content": q}]})
    if "_error" not in r:
        ans = r.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"   {q[:40]}... → {len(ans)} chars, start: {ans[:70]}")
    else:
        print(f"   {q[:40]}... → ERROR: {r['_error'][:50]}")

print("\n3. Самообучение:")
t0 = time.time()
r = api("POST", "/v1/self-learn", {})
t1 = time.time()
if "_error" not in r:
    print(f"   усвоено: {r.get('learned', 0)} за {t1-t0:.1f}s")
else:
    print(f"   ERROR: {r['_error'][:50]}")
    
print(f"\n4. Веб-поиск (Wikipedia):")
r = api("POST", "/v1/chat/completions", {"messages": [{"role": "user", "content": "кто такой Александр Пушкин"}]})
if "_error" not in r:
    ans = r.get("choices", [{}])[0].get("message", {}).get("content", "")
    print(f"   {len(ans)} chars, содержит 'поэт': {'поэт' in ans}")
else:
    print(f"   ERROR: {r['_error'][:50]}")

print(f"\n5. Новые алгоритмы:")
sys.path.insert(0, r"D:\Mirro")
from scripts.algorithms import algo
print(f"   Jaccard(налог, ндс): {algo.jaccard_similarity('налог', 'ндс'):.3f}")
print(f"   should_auto_learn('НДС', 'привет'): {algo.should_auto_learn('Что такое НДС?', 'привет')}")
print(f"   should_auto_learn('НДС', 'НДС это налог'): {algo.should_auto_learn('Что такое НДС?', 'НДС это налог на добавленную стоимость')}")
print("\nDone.")