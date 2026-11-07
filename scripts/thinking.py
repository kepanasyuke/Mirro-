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

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
WEB_CACHE = DATA_DIR / "web_cache.json"


class MirroThinking:
    """Алгоритмы включения Mirro."""

    # ===== Rules: когда искать в интернете =====
    WEB_TRIGGERS = {
        # Свежие события / актуальность
        "новост", "сегодня", "сейчас", "последн", "актуальн", "свеж",
        "вчера", "завтра", "новое", "вышел", "вышла", "обновил",
        "происход", "случил", "итоги", "результаты матч", "чемпионат",
        "курс", "доллар", "евро", "нефть", "котировк", "акци",
        # Люди/факты вне датасета
        "кто такой", "кто такая", "кто такие", "биографи",
        "самый большой", "самая большая", "рекорд", "список",
        # Технологии которые быстро меняются
        "версия", "последняя версия", "новое приложение",
        # Актуальность/тренды — дополнено для веб-first
        "новейш", "тренд", "модно", "в 2025", "в 2026", "сейчас президент",
        "кто сейчас",
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
        cache = {}
        try:
            if WEB_CACHE.exists():
                cache = json.loads(WEB_CACHE.read_text("utf-8"))
        except Exception:
            cache = {}
        return cache

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
        strategy = "web"
        stat_key = "web_answers"
        if self._wants_learn(q):
            strategy, stat_key = "learn", "learn_requests"
        elif self._wants_direct(q):
            strategy, stat_key = "direct", "direct_answers"
        elif self._wants_web(q):
            strategy, stat_key = "web", "web_answers"
        elif self._base_confident(has_base_result, base_confidence, 0.55):
            strategy, stat_key = "base", "base_answers"
        elif self._base_confident(has_base_result, base_confidence, 0.3):
            strategy, stat_key = "base+web", "web_answers"
        self.stats[stat_key] = self.stats.get(stat_key, 0) + 1
        return strategy

    # ---- покомпонентные проверки (один выход, чтобы верхний decide был один return) ----
    def _wants_learn(self, q):
        return any(t in q for t in self.LEARN_TRIGGERS)

    def _wants_direct(self, q):
        return any(t in q for t in self.DIRECT_TRIGGERS) and len(q) < 40

    def _wants_web(self, q):
        return any(t in q for t in self.WEB_TRIGGERS)

    @staticmethod
    def _base_confident(has_result, confidence, threshold):
        return has_result and confidence >= threshold

    # ========================
    #  ОЦЕНКА УВЕРЕННОСТИ БАЗЫ
    # ========================
    @staticmethod
    def confidence_from_results(results, top_k=3):
        """Оценивает уверенность ответа из базы по скорингу результатов.
        Формат results: [(example_tuple, score), ...]"""
        conf = 0.0
        try:
            top_scores = [r[1] for r in results[:top_k] if isinstance(r, (tuple, list)) and len(r) > 1]
        except Exception:
            top_scores = []
        if top_scores:
            top = max(top_scores)
            # Нормализуем: типичный топ ≈ 1-5, уверенность = сигмоид
            import math
            conf = 1.0 / (1.0 + math.exp(-(top - 1.5)))
        return conf

    # ========================
    #  ВЕБ-ПОИСК (Wikidata + Wikipedia фоллбэк)
    # ========================
    def web_search(self, query: str, top_k: int = 3) -> dict:
        """
        Ищет в интернете. Первичный источник — Wikidata (работает из РФ).
        Фоллбэк — Wikipedia RU/EN API.
        С кэшем результатов.
        """
        # 1. Кэш (только для успешных результатов — пустоту не кэшируем)
        cache_key = query.strip().lower()[:100]
        result = None
        with self._cache_lock:
            cached = self.web_cache.get(cache_key)
            if cached and cached.get("title"):
                result = cached
        if result is None:
            # 2. Wikidata (основной, быстрый, русский)
            result = self._search_wikidata(query)
            if not result.get("title"):
                # 3. Фоллбэк: Wikipedia параллельно
                result = self._search_wikipedia_parallel(query)

            if not result or not result.get("title"):
                result = {"title": "", "summary": "Не удалось найти в сети.", "url": "", "source": "none"}

            # 4. Сохранить в кэш только успешные результаты (пустоту не храним)
            if result.get("title"):
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

        result = {}
        try:
            # 1. Поиск сущности
            search_url = (
                "https://www.wikidata.org/w/api.php?action=wbsearchentities"
                "&search=" + urllib.parse.quote(query)
                + "&language=ru&uselang=ru&format=json&limit=3"
            )
            data = self._fetch_json(search_url, timeout=10)
            search = data.get("search", []) if data else []

            # 2. Взять описание сущности
            qid = search[0].get("id", "") if search else ""
            label = (search[0].get("label", "") or search[0].get("id", "")) if search else ""
            desc = search[0].get("description", "") if search else ""
            url = f"https://www.wikidata.org/wiki/{qid}" if qid else ""
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
                result = {
                    "title": label,
                    "summary": summary[:3000],
                    "url": url,
                    "source": "wikidata",
                }
        except Exception:
            result = {}
        return result

    def _search_wikipedia_parallel(self, query: str) -> dict:
        """Запускает поиск по ru и en параллельно, берёт первый успешный."""
        result = {}
        if _HAS_TPE:
            with ThreadPoolExecutor(max_workers=2) as pool:
                f1 = pool.submit(self._search_wikipedia_lang, query, "ru")
                f2 = pool.submit(self._search_wikipedia_lang, query, "en")
                r1 = f1.result(timeout=15)
                r2 = f2.result(timeout=15)
            # Сначала ru (важнее для русских запросов), потом en
            for r in (r1, r2):
                if r.get("title"):
                    result = r
                    break
        else:
            # Фоллбэк без threading
            r = self._search_wikipedia_lang(query, "ru")
            if r.get("title"):
                result = r
            else:
                result = self._search_wikipedia_lang(query, "en")
        return result

    def _search_wikipedia_lang(self, query: str, lang: str) -> dict:
        """Поиск Wikipedia в одном языке."""
        result = {}
        try:
            search_url = (
                f"https://{lang}.wikipedia.org/w/api.php"
                "?action=query&list=search&srsearch=" + urllib.parse.quote(query)
                + "&srlimit=3&format=json"
            )
            data = self._fetch_json(search_url, timeout=12)
            search = data.get("query", {}).get("search", []) if data else []
            if search:
                best_title = search[0]["title"]

                extract_url = (
                    f"https://{lang}.wikipedia.org/w/api.php"
                    "?action=query&prop=extracts&exintro&explaintext"
                    "&titles=" + urllib.parse.quote(best_title)
                    + "&format=json"
                )
                extract_data = self._fetch_json(extract_url, timeout=12)
                if extract_data:
                    pages = extract_data.get("query", {}).get("pages", {})
                    for pid, page in pages.items():
                        if pid != "-1":
                            summary = page.get("extract", "")
                            if summary:
                                result = {
                                    "title": best_title,
                                    "summary": summary[:3000],
                                    "url": f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(best_title.replace(' ', '_'))}",
                                    "source": f"wikipedia-{lang}",
                                }
                                break
        except Exception:
            result = {}
        return result

    def _fetch_json(self, url, timeout=10):
        data = None
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/0.2"
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
        except Exception:
            data = None
        return data

    # ========================
    #  ФОРМАТИРОВАНИЕ ВЕБ-ОТВЕТА
    # ========================
    def format_web_answer(self, query, result) -> str:
        ans = "Я не нашла это в интернете. Попробуй переформулировать."
        if result and result.get("summary"):
            lines = [
                f"[Веб] {result['title']}",
                "",
                result["summary"][:2500],
                "",
                f"Источник: {result['url']}",
            ]
            # умный веб: если вопрос про свежее/новости — помечаем, что данные
            # актуальны на момент обращения, и разделяем тип ответа
            q = (query or "").lower()
            is_news = any(t in q for t in ("новост", "сегодня", "вчера", "завтра",
                                           "последн", "итоги", "результаты матч",
                                           "курс", "доллар", "евро", "нефть", "тренд"))
            if is_news:
                source_kind = "актуальная справка/новость"
                lines.append("")
                lines.append("Данные актуальны на момент обращения (свежая справка).")
            else:
                source_kind = "объяснение/справка"
                lines.append("")
                lines.append("Это справочное объяснение; факты могут меняться — уточняй при важности.")
            result["kind"] = source_kind
            ans = "\n".join(lines)
        return ans

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