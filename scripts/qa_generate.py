# -*- coding: utf-8 -*-
"""Автогенерация большого набора QA-кейсов Mirro из реальной базы знаний.

Кейсы строятся так, что железно проверяемы: для понятия/функции мы знаем
ожидаемое слово (topic), поэтому проверяем, что ответ его содержит и не
является мусором. Генерирует сотни-тысячи вопросов-парафраз.

Источники:
  * понятия  (algos.module_knowledge, ключи с «_»);
  * функции  (algos.module_knowledge._by_module) по имени и по теме;
  * история ИИ (algos.knowledge_ai_history) — «кто создал X»;
  * диалог/метапознание — ручные шаблоны.

Вывод: модуль tests/qa_generated.py (список CASES) — тот же формат,
что tests/qa_cases.py, поэтому прогоняется и юнит-тестом, и run_qa.py.

Запуск:  python scripts/qa_generate.py [--limit 1000] [--out tests/qa_generated.py]
"""
import argparse, re, sys
from pathlib import Path

MIRRO_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MIRRO_HOME))
sys.path.insert(0, str(MIRRO_HOME / "algos"))


def norm(w):
    w = (w or "").strip().lower()
    return re.sub(r"\s+", " ", w)


def _collect_concepts():
    """Понятия: «что такое X» должно содержать само понятие или synonymа.
    Возвращает список кейсов. Один return: list."""
    from algos.module_knowledge import fk
    cases = []
    for key, info in fk._by_name.items():
        if not key.startswith("_"):
            continue
        topic = norm(info.get("topic", ""))
        expect = topic.split()[0][:40]       # первое слово темы
        full = topic
        for q in (f"что такое {expect}", f"расскажи про {expect}",
                  f"объясни что такое {expect}", f"что значит {expect}",
                  f"расскажи про понятие {expect}", f"объясни понятие {expect}",
                  f"что за {expect}", f"что такое понятие {expect}"):
            cases.append({"question": q,
                          "expect": expect[:20],
                          "min_len": 15})
    return cases


def _collect_functions():
    """Функции по имени и по теме. «Что такое <fn>» должно дать topic функции.
    Возвращает список кейсов. Один return: list."""
    from algos.module_knowledge import fk
    cases = []
    seen = set()
    for name, info in fk._by_name.items():
        if name.startswith("_") or len(name) <= 2:
            continue
        topic = norm(info.get("topic", ""))
        expect = (topic.split()[0] or name)[:20]
        # точное имя функции содержит подчёркивание или короткое — знаем ответ
        forms = set()
        for q in (f"что такое {name}", f"расскажи про {name} ()",
                  f"как работает {name}", f"что делает {name} что такое",
                  f"расскажи про функцию {name}", f"объясни {name}",
                  f"что означает {name}", f"какая функция {name}", 
                  f"напиши функцию {name}"):
            key = norm(q)
            if key not in seen:
                seen.add(key)
                forms.add(q)
        for q in sorted(forms):
            cases.append({"question": q, "expect": expect, "min_len": 15,
                          "forbid": _junk_for("") })
    return cases


def _junk_for(_):
    """Мусорные слова, которых не должно быть в ответе функции.
    Один return: str."""
    return "вот что я нахожу"


def _collect_ai_history():
    """История ИИ: «кто создал <X>» — ответ должен содержать автора/имя.
    Возвращает список кейсов. Один return: list."""
    try:
        from algos.knowledge_ai_history import DB
    except Exception:
        try:
            from algos.knowledge_ai_history import СПРАВОЧНИК as DB
        except Exception:
            DB = {}
    cases = []
    if not DB:
        return cases
    # DB — dict или list записей {термин: (описание, автор,...)} — постараемся
    def entries(d):
        out = []
        if isinstance(d, dict):
            for k, v in d.items():
                out.append((k, v))
        elif isinstance(d, (list, tuple)):
            for it in d:
                if isinstance(it, dict):
                    out.append((it.get("term") or it.get("термин") or it.get("кто"),
                                it.get("описание") or it.get("desc") or str(it)))
                else:
                    out.append((str(it), ""))
        return out
    for term, _v in entries(DB):
        lw = norm(term)
        if not lw or len(lw) < 3:
            continue
        cases.append({"question": f"кто создал {lw.split()[0]}",
                      "expect": lw.split()[0][:20], "min_len": 15})
    return cases


def _collect_dialog_meta():
    """Диалог и метапознание — ручные шаблоны (не должны давать мусор).
    Один return: list."""
    return [
        {"question": "привет", "min_len": 5},
        {"question": "как дела", "min_len": 5},
        {"question": "можно тебя спросить", "forbid": "bipartite", "min_len": 5},
        {"question": "осознаёшь ли ты себя", "expect": "осознаю", "min_len": 15},
        {"question": "над чем думаешь", "min_len": 10},
        {"question": "что ты думаешь о себе", "min_len": 10},
    ]


def _collect_relations():
    """Сравнительные вопросы по парам понятий («чем похожи X и Y»).
    Один return: list."""
    from algos.module_knowledge import fk
    terms = []
    for key, info in fk._by_name.items():
        if key.startswith("_"):
            t = info.get("topic", "").split()[0]
        else:
            t = info.get("topic", "").split()[0]
        if t and len(t) > 2:
            terms.append(t)
    terms = list(dict.fromkeys(terms))
    cases = []
    for i in range(0, len(terms), 2):
        a = terms[i]
        b = terms[i + 1] if i + 1 < len(terms) else terms[0]
        if a != b:
            cases.append({"question": f"чем похожи {a} и {b}", "expect": None,
                          "min_len": 5})
            cases.append({"question": f"что общего у {a} и {b}", "expect": None,
                          "min_len": 5})
    return cases


def generate():
    """Собирает все кейсы, дедуплицирует по вопросу. Один return: list."""
    all_cases = (_collect_concepts() + _collect_functions()
                 + _collect_ai_history() + _collect_relations()
                 + _collect_dialog_meta())
    seen = set()
    out = []
    for c in all_cases:
        key = norm(c.get("question", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        # уберём пустые expect/forbid из сериализации
        clean = {}
        for k in ("question", "expect", "forbid", "min_len"):
            if c.get(k) is not None:
                clean[k] = c[k]
        out.append(clean)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=1000)
    ap.add_argument("--out", default=str(MIRRO_HOME / "tests" / "qa_generated.py"))
    args = ap.parse_args()
    cases = generate()
    cases = cases[:args.limit]
    import json
    lines = [
        "# -*- coding: utf-8 -*-",
        "# АВТОГЕНЕРИРОВАНО: python scripts/qa_generate.py. Не редактировать.",
        "# Набор QA-кейсов, построен из реальной базы знаний Mirro.",
        "CASES = " + json.dumps(cases, ensure_ascii=False, indent=1),
    ]
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Сгенерировано {len(cases)} кейсов -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())