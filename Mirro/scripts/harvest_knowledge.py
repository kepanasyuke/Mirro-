# -*- coding: utf-8 -*-
"""
Mirro Knowledge Harvester — загрузка энциклопедических знаний.
Источник: Open Library + Wikipedia (если доступна).
Пополняет кластер knowledge.
"""
import json, urllib.request, urllib.parse, time, sys, re
from pathlib import Path

DATA_DIR = Path(r"D:\Mirro\data")
PROC = DATA_DIR / "processed"
PROC.mkdir(exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MirroHarvester/1.0"

# Темы для сбора знаний
SUBJECTS = [
    "finance", "economics", "python", "computers", "mathematics",
    "history", "geography", "biology", "physics", "medicine",
    "art", "music", "psychology", "law", "technology",
]

def fetch_json(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"    ! {str(e)[:60]}")
        return None

def fetch_book_desc(work_key, timeout=10):
    """Получает описание книги по ключу из Open Library."""
    url = f"https://openlibrary.org{work_key}.json"
    data = fetch_json(url, timeout)
    if not data:
        return None
    desc = data.get("description", "")
    if isinstance(desc, dict):
        desc = desc.get("value", "")
    return str(desc) if desc else None

def collect_subject(subject, limit=5):
    """Собирает работы по теме и их описания."""
    url = f"https://openlibrary.org/subjects/{urllib.parse.quote(subject)}.json?limit={limit}"
    data = fetch_json(url)
    if not data:
        return []
    works = data.get("works", [])
    collected = []
    for w in works:
        title = w.get("title", "")
        key = w.get("key", "")
        authors = ", ".join(a.get("name", "") for a in w.get("authors", [])[:2])
        if not key:
            continue
        desc = fetch_book_desc(key)
        if desc and len(desc) > 80:
            collected.append({
                "instruction": f"Расскажи про книгу: {title}",
                "input": f"автор: {authors}",
                "output": desc[:3000],
            })
        if len(collected) >= limit:
            break
    return collected

def main():
    print("=" * 60)
    print("  MIRRO — СБОР ЗНАНИЙ (Open Library)")
    print("=" * 60)
    total = 0
    for subject in SUBJECTS:
        print(f"  [{subject}]")
        items = collect_subject(subject, limit=3)
        if items:
            with open(PROC / "knowledge.jsonl", "a", encoding="utf-8") as f:
                for it in items:
                    f.write(json.dumps(it, ensure_ascii=False) + "\n")
            total += len(items)
            print(f"    +{len(items)} описаний книг")
        time.sleep(0.3)

    print(f"\n  Всего добавлено в knowledge: {total}")
    # Итого
    if PROC.joinpath("knowledge.jsonl").exists():
        n = sum(1 for _ in PROC.joinpath("knowledge.jsonl").open(encoding="utf-8") if _.strip())
        print(f"  Кластер knowledge теперь: {n} примеров")

if __name__ == "__main__":
    main()