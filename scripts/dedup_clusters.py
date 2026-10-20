# -*- coding: utf-8 -*-
"""Дедупликация в кластерах processed (улучшение №32).

Убирает повторяющиеся записи: по инструкции (и хвосту ответа), чтобы
поиск не возвращал одни и те же примеры по несколько раз.

Запуск:  python scripts/dedup_clusters.py
Сначала «сухой прогон»: используйте --apply чтобы реально перезаписать.
"""
import argparse, json, hashlib, re
from pathlib import Path

PROC = Path(r"D:\Mirro\data\processed")


def norm_key(inst, out):
    # Нормализуем: приводим к нижнему регистру, убираем пробелы/пунктуацию
    text = f"{inst}::{out[:200]}".lower()
    text = re.sub(r"\s+", " ", text).strip()
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def dedup_file(path, apply, max_rows=None):
    seen = set()
    kept = 0
    dup = 0
    out_rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            if max_rows is not None and kept >= max_rows:
                break
            try:
                item = json.loads(line)
            except Exception:
                continue
            inst = (item.get("instruction") or item.get("question") or "").strip()
            out = (item.get("output") or item.get("answer") or "").strip()
            k = norm_key(inst, out)
            if k in seen:
                dup += 1
                continue
            seen.add(k)
            kept += 1
            out_rows.append(item)
    if apply:
        with open(path, "w", encoding="utf-8") as f:
            for item in out_rows:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return kept, dup


def main():
    ap = argparse.ArgumentParser(description="Дедупликация кластеров processed")
    ap.add_argument("--apply", action="store_true", help="реально перезаписать файлы (по умолчанию сухой прогон)")
    ap.add_argument("--limit", type=int, default=0, help="ограничить строк на файл (уже выгруженный; 0 = без ограничения)")
    args = ap.parse_args()

    print("==" + (" Применяем " if args.apply else " Сухой прогон (--apply для записи) ") + "==")
    total_kept = 0
    total_dup = 0
    for f in sorted(PROC.glob("*.jsonl")):
        # Генер. корпус огромный — пропускаем по умолчанию (это не processed-кластер)
        if f.stem in ("generated", "corpus"):
            continue
        kept, dup = dedup_file(f, args.apply, args.limit or None)
        print(f"  {f.name:16} до={kept+dup:>8} после={kept:>8} дублей={dup}")
        total_kept += kept
        total_dup += dup
    print(f"ИТОГО: {total_kept} строк останется, {total_dup} дублей убрано")


if __name__ == "__main__":
    main()