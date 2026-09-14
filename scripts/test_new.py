# -*- coding: utf-8 -*-
"""Test new algorithms: spellcheck, jaccard, query_expansion, compose_v2, auto-learn trigger."""
import sys, time
sys.path.insert(0, r"D:\Mirro")
from scripts.algorithms import algo

print("Индекс:", algo.status()["examples"])
print()

# 1. SpellCheck (опечатки)
t0 = time.time()
clean = algo.spellcheck("Кок исправить код в питоне")
print(f"[1] SpellCheck: '{clean}' ({time.time()-t0:.2f}s)")

# 2. Jaccard
sim = algo.jaccard_similarity("налог на добавленную стоимость", "ндс налог добавленная стоимость расчет")
print(f"[2] Jaccard: {sim:.3f}")

# 3. Query expansion
exp = algo.query_expansion("как установить python")
print(f"[3] Query expansion: {exp}")

# 4. compose_answer_v2 (новый пайплайн)
t0 = time.time()
ans = algo.compose_answer_v2("Как заменить mspaint на маке", top_n=6)
print(f"[4] compose_v2: {time.time()-t0:.2f}s, {len(ans) if ans else 0} chars")
if ans:
    print(f"    {ans[:150]}...")

# 5. Auto-learn trigger
trigger = algo.should_auto_learn("Что такое НДС?", "НДС это налог на добавленную стоимость")
print(f"[5] should_auto_learn(хороший ответ): {trigger}")
trigger2 = algo.should_auto_learn("Что такое НДС?", "привет")
print(f"[6] should_auto_learn(плохой ответ): {trigger2}")