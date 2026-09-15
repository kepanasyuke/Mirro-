# -*- coding: utf-8 -*-
"""Probe large datasets (millions of examples) for Mirro scaling."""
import json, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/1.0"

def info(ds):
    try:
        req = urllib.request.Request(f"https://huggingface.co/api/datasets/{ds}", headers={"User-Agent": UA})
        d = json.loads(urllib.request.urlopen(req, timeout=12).read())
        files = [s.get("rfilename", "") for s in d.get("siblings", [])]
        train_files = [f for f in files if "train" in f and f.endswith((".parquet", ".jsonl", ".json"))]
        card = d.get("cardData", {})
        size = card.get("size_categories", "?")
        dl = d.get("downloads", 0)
        print(f"{ds}")
        print(f"  downloads={dl} size={size} train-файлов={len(train_files)}")
        if train_files:
            print(f"  пример: {train_files[0]}")
        # размер через последнюю версию - посчитаем по файлам lfs
        return len(train_files)
    except Exception as e:
        print(f"{ds}: ERR {str(e)[:60]}")
        return 0

# Кандидаты на 30-40 млн примеров
print("=" * 60)
print("  КАНДИДАТЫ ДЛЯ 30-40 МЛН ПРИМЕРОВ")
print("=" * 60)
info("bigcode/the-stack-smol")          # код, ~100k
info("lmsys/lmsys-chat-1m")             # 1 млн диалогов
info("HuggingFaceFW/fineweb-sample")    # выборка fineweb
info("wikimedia/wikipedia")             # википедия все
info("cerebras/SlimPajama-627B")        # 627B токенов (гигант)
info("tiiuae/falcon-refinedweb")        # много веба
info("pszemraj/simple_wikiann")         # аннотации
info("wikimedia/translated_wikipedia")  # переводы
info("yhavinga/ccmatrix")               # параллельные корпуса