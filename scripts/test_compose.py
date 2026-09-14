# -*- coding: utf-8 -*-
"""Direct test: compose_answer + _call_smart to catch real exception."""
import sys, traceback, time

sys.path.insert(0, r"D:\Mirro")

try:
    from scripts.algorithms import algo
    print("algo loaded:", algo.status()["examples"])
except Exception:
    traceback.print_exc()
    sys.exit(1)

# Test TF-IDF search
try:
    t0 = time.time()
    res = algo.search_tfidf("Что такое НДС", top_n=3)
    print("search OK: %d results, %.3fs" % (len(res), time.time() - t0))
    for ex, sc in res[:2]:
        print("   score=%.2f | %s" % (sc, ex[1][:70]))
except Exception:
    print("SEARCH FAILED")
    traceback.print_exc()

# Test compose_answer (the one that crashes the server)
try:
    t0 = time.time()
    ans = algo.compose_answer("Что такое НДС", top_n=4)
    print("compose OK: %d chars in %.2fs" % (len(ans) if ans else 0, time.time() - t0))
except Exception:
    print("COMPOSE FAILED")
    traceback.print_exc()