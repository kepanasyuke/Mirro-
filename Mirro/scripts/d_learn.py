# -*- coding: utf-8 -*-
"""Diagnose qa_score/risk values to tune should_auto_learn."""
import sys
sys.path.insert(0, r"D:\Mirro")
from scripts.algorithms import algo

def show(q, a):
    score = algo.qa_score(q, a)
    risk = algo.detect_hallucination(q, a)
    print(f"Q: {q!r}")
    print(f"A: {a!r}")
    print(f"  qa_score={score:.3f}  risk={risk:.3f}  -> learn? {algo.should_auto_learn(q, a)}")
    print()

show("Что такое НДС?", "НДС это налог на добавленную стоимость")
show("Что такое НДС?", "привет")
show("Как заменить mspaint на маке?", "Берите мини. Не понравится OSX или ностальгия замучает - дуалбут в windows.")
show("Как установить python на windows", "Скачайте установщик с python.org и запустите его. Отметьте Add to PATH.")