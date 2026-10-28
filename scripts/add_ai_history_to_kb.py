# -*- coding: utf-8 -*-
"""
Mirro — положить справочник по истории ИИ в базу знаний (self_learned).
======================================================================
Берёт ответы из algos/knowledge_ai_history.py (вопрос->ответ с авторами) и
дописывает их парами `{"instruction","output"}` в data/self_learned/..., чтобы
Mirro отвечала по этим темам и через обычный поиск TF-IDF/RAG, а не только
через триггер try_ai_history. Файл-назначение уже подхватывается при обучении
и дедуплицируется по началу вопроса.

Запуск:
  python scripts/add_ai_history_to_kb.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TARGET = ROOT / "data" / "self_learned" / "wikipedia_ru.jsonl"


def _pairs():
    """Вопрос-ответ пары по истории ИИ. Один return: list((q, a))."""
    from algos.knowledge_ai_history import AI_HISTORY
    pairs = []
    # Шаблоны вопросов под каждый ключ
    templates = [
        "кто создал {k}?", "кто придумал {k}?",
        "что такое {k}?", "объясни {k}",
        "расскажи про {k}", "кто автор {k}?",
    ]
    for key, (answer, _authors, _idea) in AI_HISTORY.items():
        for tpl in templates:
            q = tpl.format(k=key)
            pairs.append((q, answer))
    return pairs


def _existing_prefixes(path):
    """Множество префиксов вопросов уже в файле. Один return: set of str."""
    prefixes = set()
    if not path.exists():
        return prefixes
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ex = json.loads(line)
                prefixes.add((ex.get("instruction") or "")[:50].lower())
            except Exception:
                pass
    return prefixes


def main():
    pairs = _pairs()
    if not pairs:
        print("[err] нет пар из knowledge_ai_history")
        return 1
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    existing = _existing_prefixes(TARGET)
    added = 0
    with open(TARGET, "a", encoding="utf-8") as fh:
        for q, a in pairs:
            key = q[:50].lower()
            if key in existing:
                continue
            fh.write(json.dumps({"instruction": q, "input": "", "output": a}, ensure_ascii=False) + "\n")
            existing.add(key)
            added += 1
    print(f"[ok] добавлено {added} пар по истории ИИ в {TARGET}")
    print(f"     теперь Mirro найдёт их через поиск при следующем обучении/пересборке индекса")
    return 0


if __name__ == "__main__":
    sys.exit(main())