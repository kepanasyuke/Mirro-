# -*- coding: utf-8 -*-
"""Тест мыслительного движка: осмысленные ответы по типам."""
import sys
sys.path.insert(0, r"D:\Mirro\algos")
import importlib.util

spec = importlib.util.spec_from_file_location("think", r"D:\Mirro\algos\think.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

tests = [
    "сколько будет 2+2",
    "15% от 200",
    "реши x²-5x+6=0",
    "реши x^2 - 3x + 2 = 0",
    "НОД 48 и 36",
    "энергия связи 0.002",
    "C(10,3)",
    "сортировать 5 2 8 1",
    "привет",
]

for q in tests:
    r = m.think(q)
    ans = r["explanation"] if r["explanation"] else r["answer"]
    print(f"Q: {q}")
    print(f"  -> {ans}")
    print()