# -*- coding: utf-8 -*-
"""ru_definitions.py — русские определения из корпуса, без перевода.

Ищет в корпусе предложения-определения по шаблонам «X — это …»,
«X называется …», «под X понимают …» и отбрасывает мусор (реклама,
«почитайте в критике», ссылки). Нужен потому, что русская база
(algos/module_knowledge) — это 155 понятий, а корпус — гигабайты текста.

Ответ кэшируется в data/knowledge/ru_definitions.json, чтобы не сканировать
корпус на каждый вопрос.

Запуск:  python scripts/ru_definitions.py "память"
         python scripts/ru_definitions.py "память" --scan      # пересобрать кэш
"""
import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "knowledge", "ru_definitions.json")
CORPUS_DIRS = (os.path.join(ROOT, "data", "processed"), os.path.join(ROOT, "data", "corpus_ready"))

# мусор, который часто содержит слово, но определением не является
_NOISE = ("почитайте", "почитай", "подпишись", "реклама", "скидк", "купить",
          "заказать", "http", "www.", "промокод", "доставка", "цена", "оптом")

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WS = re.compile(r"\s+")


def _stems(term):
    """Основы термина для учёта словоформ («память» → «памят»). Один return: list."""
    stems = [term]
    for cut in (1, 2):
        base = term[:-cut]
        if len(base) >= 4 and base not in stems:
            stems.append(base)
    return stems


def _patterns(term):
    """Шаблоны определений для термина и его словоформ. Один return: list."""
    patterns = []
    for stem in _stems(term):
        t = re.escape(stem) + r"[а-яё]*"
        patterns.extend([
            re.compile(r"\b%s\b\s*[—–-]\s*(?:это|это есть|такой|такая|такое|такие)\b" % t, re.I),
            re.compile(r"\b%s\b\s+(?:называется|называют|зовут)\b" % t, re.I),
            re.compile(r"под\s+\b%s\b\s+понимают\b" % t, re.I),
            re.compile(r"\b%s\b\s*[—–-]\s+[а-яё]" % t, re.I),
        ])
    return patterns


def _clean(sentence):
    """Нормализует пробелы в предложении. Один return: str."""
    return _WS.sub(" ", sentence).strip()


def _looks_like_definition(sentence, term, patterns):
    """Похоже ли предложение на определение термина. Один return: bool."""
    low = sentence.lower()
    noisy = any(marker in low for marker in _NOISE)
    has_pattern = any(pattern.search(sentence) for pattern in patterns)
    long_enough = 40 <= len(sentence) <= 400
    mentions = term.lower() in low
    return bool(mentions and has_pattern and long_enough and not noisy)


def extract_from_text(text, term, limit=3):
    """Определения термина из одного текста. Один return: list."""
    patterns = _patterns(term)
    found = []
    for raw in _SENT_SPLIT.split(text or ""):
        sentence = _clean(raw)
        if _looks_like_definition(sentence, term, patterns) and sentence not in found:
            found.append(sentence)
        if len(found) >= limit:
            break
    return found


def _iter_texts(path, max_lines=0):
    """Поток текстов из jsonl/текстового файла. Один return: generator."""
    limit = max_lines or 0
    count = 0
    try:
        with io.open(path, encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                count += 1
                if limit and count > limit:
                    break
                line = line.strip()
                if not line:
                    continue
                if line.startswith("{"):
                    try:
                        record = json.loads(line)
                    except ValueError:
                        continue
                    for key in ("output", "text", "content", "instruction"):
                        value = record.get(key)
                        if isinstance(value, str) and len(value) > 40:
                            yield value
                elif len(line) > 40:
                    yield line
    except OSError:
        return


def _corpus_files():
    """Файлы корпуса для сканирования. Один return: list."""
    files = []
    for folder in CORPUS_DIRS:
        if os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                if name.endswith((".jsonl", ".txt")):
                    files.append(os.path.join(folder, name))
    return files


def load_cache():
    """Кэш определений с диска. Один return: dict."""
    try:
        with io.open(CACHE, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def save_cache(cache):
    """Пишет кэш на диск. Один return: bool."""
    ok = True
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with io.open(CACHE, "w", encoding="utf-8") as handle:
            json.dump(cache, handle, ensure_ascii=False, indent=1, sort_keys=True)
    except OSError:
        ok = False
    return ok


def scan(term, limit=3, max_lines=0):
    """Ищет определения термина по корпусу (медленно, разово). Один return: list."""
    found = []
    for path in _corpus_files():
        if len(found) >= limit:
            break
        for text in _iter_texts(path, max_lines=max_lines):
            for sentence in extract_from_text(text, term, limit=limit - len(found)):
                if sentence not in found:
                    found.append(sentence)
            if len(found) >= limit:
                break
    return found


def find(term, limit=3, use_cache=True, allow_scan=False, max_lines=0):
    """Определения термина: кэш, затем (по разрешению) корпус. Один return: list."""
    cache = load_cache() if use_cache else {}
    known = cache.get(term)
    found = list(known[:limit]) if isinstance(known, list) else []
    if not found and allow_scan:
        found = scan(term, limit=limit, max_lines=max_lines)
        if found and use_cache:
            cache[term] = found
            save_cache(cache)
    return found


def main(argv):
    """CLI: поиск определений термина. Один return: int."""
    parser = argparse.ArgumentParser(description="Русские определения из корпуса")
    parser.add_argument("term", help="термин, например «память»")
    parser.add_argument("--scan", action="store_true", help="сканировать корпус и обновить кэш")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--max-lines", type=int, default=0, help="ограничить строк на файл (0 — все)")
    args = parser.parse_args(argv)
    found = find(args.term, limit=args.limit, allow_scan=args.scan, max_lines=args.max_lines)
    print("кэш:", CACHE)
    for number, sentence in enumerate(found, 1):
        print("%d. %s" % (number, sentence))
    print("найдено:", len(found))
    return 0 if found else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
