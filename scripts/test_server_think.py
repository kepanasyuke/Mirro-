# -*- coding: utf-8 -*-
"""Тестируем подключение думания к серверу Mirro."""
import json, urllib.request

HOST = "http://127.0.0.1:3443"

def ask(q):
    req = urllib.request.Request(HOST + "/v1/chat/completions",
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "Test/1.0"},
        data=json.dumps({"messages": [{"role": "user", "content": q}]}).encode("utf-8"))
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        return d.get("choices", [{}])[0].get("message", {}).get("content", "нет")
    except Exception as e:
        return f"ОШИБКА: {e}"

tests = [
    "сколько будет 2+2",
    "реши x²-5x+6=0",
    "НОД 48 и 36",
    "C(10,3)",
    "Что такое НДС?",
    "привет",
]
for t in tests:
    print(f"Q: {t}")
    a = ask(t)
    print(f"  A: {a[:180]}")
    print()