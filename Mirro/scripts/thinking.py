#!/usr/bin/env python3
"""
Mirro Thinking — алгоритмы включения и веб-поиск
=================================================
Определяет, КОГДА Mirro должна:
  - искать в своей базе знаний (instant)
  - искать в интернете (web)
  - просто отвечать (direct)
  - учиться (learn)

Методы:
  1. Rules engine  — триггеры по типу вопроса
  2. Confidence    — насколько уверен ответ из базы
  3. Web search    — Wikipedia + фоллбэки
  4. Decision tree — выбор стратегии
"""

import json, re as _re, urllib.request, urllib.error, urllib.parse, time, threading
from pathlib import Path
try:
    from concurrent.futures import ThreadPoolExecutor
    _HAS_TPE = True
except ImportError:
    _HAS_TPE = False

DATA_DIR = Path(r"D:\Mirro\data")
WEB_CACHE = DATA_DIR / "web_cache.json"


class MirroThinking:
    """Алгоритмы включения Mirro."""

    # ===== Rules: когда искать в интернете =====
    WEB_TRIGGERS = {
        # Свежие события / актуальность
        "новост", "сегодня", "сейчас", "последн", "актуальн", "свеж",
        "вчера", "сегодня", "завтра", "новое", "вышел", "вышла", "обновил",
        "происход", "случил", "итоги", "результаты матч", "чемпионат",
        "курс", "доллар", "евро", "нефть", "котировк", "акци",
        # Люди/факты вне датасета
        "кто такой", "кто такая", "кто такие", "биографи",
        "самый большой", "самая большая", "рекорд", "список",
        # Технологии которые быстро меняются
        "версия", "последняя версия", "новоe приложение",
    }

    # ===== Rules: когда учиться =====
    LEARN_TRIGGERS = [
        "научи", "обучи", "запомн", "запиши", "сохрани это",
        "добавь в базу", "выучи", "запомни что",
    ]

    # ===== Rules: когда ответить напрямую (math, greetings) =====
    DIRECT_TRIGGERS = [
        "привет", "здравств", "добрый", "спасибо", "пока",
        "как дела", "как ты", "как жизнь", "как твои дела", "как у тебя",
        "как настроение", "чё как", "че как",
        "2+2", "+", "-", "*", "/", "=", "%",
    ]

    def __init__(self):
        self.stats = {
            "base_answers": 0,
            "web_answers": 0,
            "direct_answers": 0,
            "learn_requests": 0,
        }
        self.web_cache = self._load_cache()
        self._cache_lock = threading.Lock()

    def _load_cache(self):
        try:
            if WEB_CACHE.exists():
                return json.loads(WEB_CACHE.read_text("utf-8"))
        except Exception:
            pass
        return {}

    def _save_cache(self):
        try:
            WEB_CACHE.write_text(json.dumps(self.web_cache, ensure_ascii=False), "utf-8")
        except Exception:
            pass

    # ========================
    #  ОСНОВНОЙ АЛГОРИТМ ВКЛЮЧЕНИЯ
    # ========================
    def decide(self, query: str, base_confidence: float = 0.0,
               has_base_result: bool = False) -> str:
        """
        Дерево решений: возвращает стратегию.
        - 'learn'   — пользователь хочет научить
        - 'direct'  — ответить напрямую (приветствие/математика)
        - 'web'     — искать в интернете
        - 'base'    — база знаний достаточно уверена
        - 'base+web'— база + подстраховка интернетом
        """
        q = query.lower().strip()

        # 1. Обучение
        if any(t in q for t in self.LEARN_TRIGGERS):
            self.stats["learn_requests"] += 1
            return "learn"

        # 2. Прямые ответы
        if any(t in q for t in self.DIRECT_TRIGGERS) and len(q) < 40:
            self.stats["direct_answers"] += 1
            return "direct"

        # 3. Свежесть/актуальность → web
        web_hits = sum(1 for t in self.WEB_TRIGGERS if t in q)
        if web_hits > 0:
            self.stats["web_answers"] += 1
            return "web"

        # 4. База достаточно уверена?
        if has_base_result and base_confidence >= 0.55:
            self.stats["base_answers"] += 1
            return "base"

        # 5. Есть результат, но слабый → base+web
        if has_base_result and base_confidence >= 0.3:
            self.stats["web_answers"] += 1
            return "base+web"

        # 6. Нет результата → web
        self.stats["web_answers"] += 1
        return "web"

    # ========================
    #  ОЦЕНКА УВЕРЕННОСТИ БАЗЫ
    # ========================
    @staticmethod
    def confidence_from_results(results, top_k=3):
        """Оценивает уверенность ответа из базы по скорингу результатов.
        Формат results: [(example_tuple, score), ...]"""
        if not results:
            return 0.0
        try:
            # search_tfidf возвращает (example, score) — берём score (индекс 1)
            top_scores = [r[1] for r in results[:top_k] if isinstance(r, (tuple, list)) and len(r) > 1]
        except Exception:
            return 0.0
        if not top_scores:
            return 0.0
        top = max(top_scores)
        # Нормализуем: типичный топ ≈ 1-5, уверенность = сигмоид
        import math
        return 1.0 / (1.0 + math.exp(-(top - 1.5)))

    # ========================
    #  ВЕБ-ПОИСК (Wikidata + Wikipedia фоллбэк)
    # ========================
    def web_search(self, query: str, top_k: int = 3) -> dict:
        """
        Ищет в интернете. Первичный источник — Wikidata (работает из РФ).
        Фоллбэк — Wikipedia RU/EN API.
        С кэшем результатов.
        """
        # 1. Кэш
        cache_key = query.strip().lower()[:100]
        with self._cache_lock:
            if cache_key in self.web_cache:
                return self.web_cache[cache_key]

        # 2. Wikidata (основной, быстрый, русский)
        result = self._search_wikidata(query)
        if not result.get("title"):
            # 3. Фоллбэк: Wikipedia параллельно
            result = self._search_wikipedia_parallel(query)

        if not result:
            result = {"title": "", "summary": "Не удалось найти в сети.", "url": "", "source": "none"}

        # 4. Сохранить в кэш
        with self._cache_lock:
            if len(self.web_cache) > 300:
                self.web_cache = dict(list(self.web_cache.items())[-200:])
            self.web_cache[cache_key] = result
        self._save_cache()

        return result

    def _search_wikidata(self, query: str) -> dict:
        """Поиск в Wikidata: сущность → русское описание + алиасы."""
        # Чистим запрос от "кто такой / что такое"
        clean = _re.sub(r"\b(кто такой|кто такая|кто такие|что такое|что это|расскажи про|расскажи о|что за)\b",
                        "", query, flags=_re.IGNORECASE).strip()
        if not clean:
            clean = query
        query = clean

        try:
            # 1. Поиск сущности
            search_url = (
                "https://www.wikidata.org/w/api.php?action=wbsearchentities"
                "&search=" + urllib.parse.quote(query)
                + "&language=ru&uselang=ru&format=json&limit=3"
            )
            data = self._fetch_json(search_url, timeout=10)
            if not data:
                return {}
            search = data.get("search", [])
            if not search:
                return {}

            # 2. Взять описание сущности
            qid = search[0].get("id", "")
            if not qid:
                return {}
            label = search[0].get("label", "") or search[0].get("id", "")
            desc = search[0].get("description", "")
            url = f"https://www.wikidata.org/wiki/{qid}"

            if label:
                summary = desc or f"{label} — сведения из Wikidata."
                # Дополнительно: попробовать алиасы
                try:
                    ent_url = (
                        "https://www.wikidata.org/w/api.php?action=wbgetentities"
                        f"&ids={qid}&props=descriptions|labels|aliases"
                        "&languages=ru&format=json"
                    )
                    ent_data = self._fetch_json(ent_url, timeout=8)
                    if ent_data:
                        ent = ent_data.get("entities", {}).get(qid, {})
                        desc_from_ent = ent.get("descriptions", {}).get("ru", {}).get("value", "")
                        if desc_from_ent:
                            summary = desc_from_ent
                except Exception:
                    pass

                return {
                    "title": label,
                    "summary": summary[:3000],
                    "url": url,
                    "source": "wikidata",
                }
        except Exception:
            pass
        return {}

    def _search_wikipedia_parallel(self, query: str) -> dict:
        """Запускает поиск по ru и en параллельно, берёт первый успешный."""
        results = [None, None]
        if _HAS_TPE:
            with ThreadPoolExecutor(max_workers=2) as pool:
                f1 = pool.submit(self._search_wikipedia_lang, query, "ru")
                f2 = pool.submit(self._search_wikipedia_lang, query, "en")
                r1 = f1.result(timeout=15)
                r2 = f2.result(timeout=15)
            # Сначала ru (важнее для русских запросов), потом en
            for r in (r1, r2):
                if r.get("title"):
                    return r
            return {}
        # Фоллбэк без threading
        r = self._search_wikipedia_lang(query, "ru")
        if r.get("title"):
            return r
        return self._search_wikipedia_lang(query, "en")

    def _search_wikipedia_lang(self, query: str, lang: str) -> dict:
        """Поиск Wikipedia в одном языке."""
        try:
            search_url = (
                f"https://{lang}.wikipedia.org/w/api.php"
                "?action=query&list=search&srsearch=" + urllib.parse.quote(query)
                + "&srlimit=3&format=json"
            )
            data = self._fetch_json(search_url, timeout=12)
            if not data:
                return {}
            search = data.get("query", {}).get("search", [])
            if not search:
                return {}
            best_title = search[0]["title"]

            extract_url = (
                f"https://{lang}.wikipedia.org/w/api.php"
                "?action=query&prop=extracts&exintro&explaintext"
                "&titles=" + urllib.parse.quote(best_title)
                + "&format=json"
            )
            extract_data = self._fetch_json(extract_url, timeout=12)
            if not extract_data:
                return {}
            pages = extract_data.get("query", {}).get("pages", {})
            for pid, page in pages.items():
                if pid == "-1":
                    continue
                summary = page.get("extract", "")
                if summary:
                    return {
                        "title": best_title,
                        "summary": summary[:3000],
                        "url": f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(best_title.replace(' ', '_'))}",
                        "source": f"wikipedia-{lang}",
                    }
        except Exception:
            pass
        return {}

    def _fetch_json(self, url, timeout=10):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/0.2"
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except Exception:
            return None

    # ========================
    #  ФОРМАТИРОВАНИЕ ВЕБ-ОТВЕТА
    # ========================
    def format_web_answer(self, query, result) -> str:
        if not result or not result.get("summary"):
            return "Я не нашла это в интернете. Попробуй переформулировать."
        lines = [
            f"[Веб] {result['title']}",
            "",
            result["summary"][:2500],
            "",
            f"Источник: {result['url']}",
        ]
        return "\n".join(lines)

    def status(self):
        return dict(self.stats)


# Singleton
thinking = MirroThinking()


if __name__ == "__main__":
    # Тест алгоритма включения
    tests = [
        "Привет",
        "Что такое НДС?",
        "новости сегодня про технологии",
        "кто такой Пушкин?",
        "научи меня отвечать про Python",
        "2+2",
        "какой курс доллара",
    ]
    for q in tests:
        strategy = thinking.decide(q, base_confidence=0.4, has_base_result=True)
        print(f"  {q[:35]:38} → {strategy}")

    print("\nВеб-поиск:")
    r = thinking.web_search("Налог на добавленную стоимость")
    print(f"  {r['title']}")
    print(f"  {r['summary'][:150]}...")
    print(f"  URL: {r['url']}")