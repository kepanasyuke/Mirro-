# -*- coding: utf-8 -*-
"""Строит карту «английская тема Mirro → русское понятие».

Источник пар — интервики en.wikipedia → ru.wikipedia (батчами по 50), для промахов
добираем через поиск Wikidata и её русскую подпись. Результат пишется в
data/bilingual_map.json и используется будущим обработчиком try_bilingual.

Запуск:
    python scripts/build_bilingual_map.py --limit 200   # пробный прогон
    python scripts/build_bilingual_map.py               # все темы
    python scripts/build_bilingual_map.py --force       # перезаписать карту
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "bilingual_map.json"
UA = {"User-Agent": "Mirro-bilingual/1.0 (local project; contact: local)"}
BATCH = 50
PAUSE = 1.0


def _is_ru(value):
    """Похоже ли на русское название (есть кириллица, нет латиницы-подмены).
    Один return: bool."""
    text = (value or "").strip()
    return bool(text) and any("а" <= c.lower() <= "я" or c.lower() == "ё" for c in text)


def topics():
    """Ключи английской базы как список тем. Один return: list."""
    from algos.english_kb import _EN_KB
    return [name for name in _EN_KB if isinstance(name, str) and name]


def _get(url, tries=4):
    """GET JSON с повторами; на 429 выжидает дольше. Один return: dict или None."""
    result = None
    for attempt in range(tries):
        try:
            request = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            time.sleep(5 + attempt * 5 if exc.code == 429 else 1 + attempt)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(1 + attempt)
    return result


def wiki_pairs(titles):
    """Интервики en→ru для партии заголовков. Один return: dict {en: ru}."""
    found = {}
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "titles": "|".join(titles), "prop": "langlinks",
        "lllang": "ru", "lllimit": "max", "format": "json", "redirects": 1,
        "normalized": 1})
    data = _get(url) or {}
    query = data.get("query") or {}
    by_final = {}
    for page in (query.get("pages") or {}).values():
        links = page.get("langlinks") or []
        if links and _is_ru(links[0].get("*", "")):
            by_final[page.get("title", "")] = links[0].get("*", "")
    alias = {}
    for item in query.get("normalized") or []:
        alias[item.get("from", "")] = item.get("to", "")
    for item in query.get("redirects") or []:
        alias[item.get("from", "")] = item.get("to", "")
    for title in titles:
        final = alias.get(title, title)
        for _ in range(3):
            final = alias.get(final, final)
        if final in by_final:
            found[title] = by_final[final]
    return found


def wikidata_ids(topics_list):
    """Ищет QID для каждой темы через wbsearchentities. Один return: dict {topic: qid}."""
    found = {}
    for topic in topics_list:
        data = _get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
            "action": "wbsearchentities", "search": topic, "language": "en",
            "uselang": "en", "type": "item", "limit": 1, "format": "json"})) or {}
        hits = data.get("search") or []
        if hits and hits[0].get("id"):
            found[topic] = hits[0]["id"]
        time.sleep(PAUSE)
    return found


def wikidata_labels(ids):
    """Русские подписи для пачки QID (по 50 за запрос). Один return: dict {qid: ru}."""
    labels = {}
    id_list = list(ids)
    for start in range(0, len(id_list), BATCH):
        chunk = id_list[start:start + BATCH]
        data = _get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
            "action": "wbgetentities", "ids": "|".join(chunk),
            "props": "labels", "languages": "ru", "format": "json"})) or {}
        for qid, entity in (data.get("entities") or {}).items():
            ru = ((entity.get("labels") or {}).get("ru") or {}).get("value")
            if _is_ru(ru):
                labels[qid] = ru
        time.sleep(PAUSE)
    return labels


def wikidata_pair(topic):
    """Русская подпись из Wikidata для темы. Один return: str или None."""
    search = _get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbsearchentities", "search": topic, "language": "en",
        "uselang": "en", "type": "item", "limit": 1, "format": "json"})) or {}
    hits = search.get("search") or []
    if not hits:
        return None
    entity_id = hits[0].get("id")
    entity = _get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbgetentities", "ids": entity_id, "props": "labels|descriptions",
        "languages": "ru|en", "format": "json"})) or {}
    labels = ((entity.get("entities") or {}).get(entity_id) or {}).get("labels") or {}
    ru = (labels.get("ru") or {}).get("value")
    return ru if _is_ru(ru) else None


def save(all_topics, resolved):
    """Пишет карту на диск (после каждой партии, чтобы прогресс не терялся)."""
    clean = {k: v for k, v in resolved.items() if v}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                               "total_topics": len(all_topics),
                               "resolved": len(clean),
                               "map": clean}, ensure_ascii=False, indent=1), encoding="utf-8")


def collect(all_topics, resolved, limit, use_wikidata=True, wikidata_limit=0, skip_wiki=False):
    """Добирает пары: сначала интервики батчами, потом Wikidata. Возвращает карту."""
    pending = [t for t in all_topics if t not in resolved][:limit]
    if not skip_wiki:
        for start in range(0, len(pending), BATCH):
            chunk = pending[start:start + BATCH]
            pairs = wiki_pairs(chunk)
            resolved.update(pairs)
            save(all_topics, resolved)
            print("[wiki] %d/%d, найдено %d" % (min(start + BATCH, len(pending)), len(pending), len(pairs)),
                  flush=True)
            time.sleep(PAUSE)
    if not use_wikidata:
        return resolved
    missing = [t for t in pending if t not in resolved]
    batch = missing[:wikidata_limit] if wikidata_limit else missing
    # по 20 тем за подход: после каждой пачки ищем подписи и сохраняем карту,
    # чтобы долгий прогон был прерываемым и прогресс был виден
    for start in range(0, len(batch), 20):
        chunk = batch[start:start + 20]
        ids = wikidata_ids(chunk)
        labels = wikidata_labels(set(ids.values()))
        for topic, qid in ids.items():
            if qid in labels:
                resolved[topic] = labels[qid]
        save(all_topics, resolved)
        print("[wikidata] %d/%d, в карте %d" % (min(start + 20, len(batch)), len(batch), len(resolved)),
              flush=True)
    return resolved


def main():
    """Точка входа: строит карту и печатает статистику."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-wikidata", action="store_true")
    parser.add_argument("--wikidata-limit", type=int, default=0)
    parser.add_argument("--skip-wiki", action="store_true")
    args = parser.parse_args()
    all_topics = topics()
    resolved = {}
    if OUT.exists() and not args.force:
        resolved = json.loads(OUT.read_text(encoding="utf-8")).get("map") or {}
    limit = args.limit or len(all_topics)
    collect(all_topics, resolved, limit, not args.no_wikidata, args.wikidata_limit, args.skip_wiki)
    clean = {k: v for k, v in resolved.items() if v}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                               "total_topics": len(all_topics),
                               "resolved": len(clean),
                               "map": clean}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nтем всего: %d, с русской парой: %d (%.0f%%)" % (
        len(all_topics), len(clean), 100.0 * len(clean) / max(1, len(all_topics))))
    sample = list(clean.items())[:12]
    for en, ru in sample:
        print("   %-22s -> %s" % (en, ru))
    if len(clean) < len(all_topics):
        print("без пары:", [t for t in all_topics if t not in clean][:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())
