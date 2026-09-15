#!/usr/bin/env python3
"""Direct test of algorithms module - fast diagnostics."""
import sys, time, traceback

t0 = time.time()
sys.path.insert(0, r"D:\Mirro")
try:
    from scripts.algorithms import algo
    print("Import OK (%.1fs)" % (time.time() - t0))
except Exception:
    traceback.print_exc()
    sys.exit(1)

print("Status:", algo.status())

# Test search
t1 = time.time()
try:
    r = algo.search_tfidf("Что такое НДС", top_n=3)
    print("Search OK: %d results in %.2fs" % (len(r), time.time() - t1))
    if r:
        sc = r[0][0]
        txt = r[0][1][1][:120]
        print("  Score:", sc)
        print("  Text:", txt)
except Exception:
    traceback.print_exc()
    print("Search FAILED in %.2fs" % (time.time() - t1))

# Test compose
t2 = time.time()
try:
    ans = algo.compose_answer("Что такое НДС", top_n=4)
    print("Compose OK in %.2fs, len=%d" % (time.time() - t2, len(ans) if ans else 0))
    if ans:
        print("  Answer:", ans[:200])
except Exception:
    traceback.print_exc()
    print("Compose FAILED in %.2fs" % (time.time() - t2))