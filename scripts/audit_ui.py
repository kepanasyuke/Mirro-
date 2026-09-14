# -*- coding: utf-8 -*-
"""Аудит типографики и тегов UI Mirro."""
import re
from pathlib import Path

c = Path(r"D:\Mirro\web\index.html").read_text("utf-8")

# Жёсткие font-size остались?
sizes = re.findall(r"font-size:\s*([\d.]+)\s*px", c)
hard = [s for s in sizes if s in ("10", "11", "11.5", "12", "12.5", "12.8", "13", "13.5", "15", "16", "18", "19", "24", "25")]
print("Жёстких font-size:", len(hard), sorted(set(hard)) if hard else "нет — всё на переменных")

# Баланс тегов
ok = True
for t in ["div", "section", "button", "script", "svg", "style", "table", "select"]:
    o = len(re.findall(fr"<{t}[ >]", c))
    cl = len(re.findall(fr"</{t}>", c))
    if o != cl:
        print(f"  {t}: {o}/{cl}")
        ok = False
print("HTML сбалансирован" if ok else "ОШИБКА ТЕГОВ")

# Проверка сервера
import urllib.request
try:
    r = urllib.request.urlopen("http://127.0.0.1:3443/", timeout=5)
    data = r.read()
    print(f"UI отдаётся: {r.status} {len(data)}B")
    text = data.decode("utf-8", errors="replace")
    print("Модульная шкала:", "--fs-hero" in text and "--fs-tiny" in text)
except Exception as e:
    print(f"Сервер: {e}")