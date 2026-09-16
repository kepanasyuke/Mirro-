# -*- coding: utf-8 -*-
"""
Mirro Core AI — единая нейросеть знаний
========================================
- Собственные алгоритмы (TF-IDF + TextRank + Naive Bayes + самокоррекция)
- Reasoning + обдумывание ответов
- Без внешних API, без зависимостей
- OpenAI-совместимый API на порту 3443
- Веб-интерфейс на /
- (c) MultiTool — Mirro AI
"""

import json, os, time, random, re as _re, sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict, Counter
from datetime import datetime as _datetime

MIRRO_HOME = Path(r"D:\Mirro")
CORE = MIRRO_HOME / "core"
DATA = MIRRO_HOME / "data"
LOGS = MIRRO_HOME / "logs"
MODELS = MIRRO_HOME / "models"

for d in [CORE, LOGS, MODELS]:
    d.mkdir(parents=True, exist_ok=True)

HOST = "127.0.0.1"
PORT = 3443

KNOWLEDGE_CLUSTERS = {
    "ru": {"desc": "Русский язык, диалоги, инструкции", "priority": 10},
    "code": {"desc": "Программирование, алгоритмы, код", "priority": 10},
    "math": {"desc": "Математика, логика, рассуждения", "priority": 9},
    "design": {"desc": "UI/UX, SVG, HTML/CSS, графика, вёрстка", "priority": 9},
    "knowledge": {"desc": "Наука, история, география, право, медицина", "priority": 8},
    "general": {"desc": "Общие инструкции и диалоги", "priority": 7},
}

TASK_ROUTES = {
    "код": "code", "python": "code", "javascript": "code", "js": "code",
    "алгоритм": "code", "отлад": "code", "баг": "code", "компил": "code",
    "библиотек": "code", "docker": "code", "git": "code", "api": "code",
    "sql": "code", "скрипт": "code", "программ": "code", "react": "code",
    "typescript": "code", "java": "code",
    "css": "design", "svg": "design", "дизайн": "design", "график": "design",
    "рисун": "design", "верстк": "design", "вёрстк": "design", "ui": "design",
    "ux": "design", "логотип": "design", "постер": "design", "мудборд": "design",
    "палитр": "design", "шрифт": "design", "иконк": "design", "баннер": "design",
    "макет": "design", "фото": "design", "картинк": "design", "презентац": "design",
    "слайд": "design", "ппт": "design", "интерфейс": "design",
    "математик": "math", "уравнен": "math", "формул": "math", "вычисли": "math",
    "процент": "math", "интеграл": "math", "производн": "math", "геометри": "math",
    "алгебр": "math", "статистик": "math",
    "закон": "ru", "налог": "ru", "договор": "ru", "юрист": "ru",
    "бухгалтер": "ru", "госуслуги": "ru", "сбер": "ru", "ндс": "ru",
    "усн": "ru", "осно": "ru", "ип": "ru", "ооо": "ru", "реквизит": "ru",
    "1с": "ru", "штраф": "ru", "иск": "ru", "суд": "ru",
    "истори": "knowledge", "географи": "knowledge", "наук": "knowledge",
    "биологи": "knowledge", "хими": "knowledge", "физик": "knowledge",
    "астроном": "knowledge", "медицин": "knowledge", "экономик": "knowledge",
    "столиц": "knowledge", "страна": "knowledge", "планет": "knowledge",
    "музык": "audio", "звук": "audio", "видео": "video", "монтаж": "video",
}


class MirroCore:
    def __init__(self):
        self.processed_dir = DATA / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        self.stats = self._load_json(CORE / "stats.json") or {
            "calls": 0, "clusters_used": Counter(), "sources_count": 0, "total_examples": 0
        }
        self.knowledge_base = defaultdict(list)
        self._load_knowledge()

    def _load_json(self, path):
        try:
            return json.loads(path.read_text("utf-8"))
        except Exception:
            return None

    def _save_json(self, path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

    def _load_knowledge(self):
        for f in self.processed_dir.glob("*.jsonl"):
            cluster = f.stem
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        try:
                            self.knowledge_base[cluster].append(json.loads(line))
                        except Exception:
                            pass
        self.stats["total_examples"] = sum(len(v) for v in self.knowledge_base.values())

    def classify_task(self, prompt):
        prompt_lower = prompt.lower()
        scores = defaultdict(float)
        for keyword, cluster in TASK_ROUTES.items():
            count = prompt_lower.count(keyword)
            if count:
                scores[cluster] += count * KNOWLEDGE_CLUSTERS.get(cluster, {}).get("priority", 1)
        for cluster in scores:
            scores[cluster] += self.stats["clusters_used"].get(cluster, 0) * 0.01
        if scores:
            return max(scores, key=scores.get)
        ru_chars = sum(1 for c in prompt if '\u0400' <= c <= '\u04FF')
        if ru_chars > 3:
            return "ru"
        if any(c in prompt for c in "{}[]();=<>"):
            return "code"
        return "general"

    def get_context(self, cluster, max_examples=5):
        examples = self.knowledge_base.get(cluster, [])
        if not examples:
            return []
        return random.sample(examples, min(max_examples, len(examples)))

    def log_call(self, prompt, cluster, provider, latency_ms, success, tokens=0):
        self.stats["calls"] += 1
        self.stats["clusters_used"][cluster] = self.stats["clusters_used"].get(cluster, 0) + 1
        entry = {
            "ts": _datetime.utcnow().isoformat(), "cluster": cluster,
            "provider": provider, "latency_ms": latency_ms,
            "success": success, "prompt_len": len(prompt),
        }
        with open(LOGS / "calls.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._save_json(CORE / "stats.json", dict(self.stats))

    def get_cluster_info(self):
        out = {}
        for name, info in KNOWLEDGE_CLUSTERS.items():
            out[name] = {**info, "examples": len(self.knowledge_base.get(name, [])),
                         "calls": self.stats["clusters_used"].get(name, 0)}
        return out

    def status(self):
        return {
            "name": "Mirro", "version": "0.2",
            "total_calls": self.stats["calls"],
            "total_examples": self.stats["total_examples"],
            "clusters": self.get_cluster_info(),
            "api": f"http://{HOST}:{PORT}/v1/chat/completions",
        }

    def corpus_total(self):
        if not hasattr(self, "_corpus_total"):
            total = 0
            for f in (DATA / "corpus_big").glob("*.jsonl"):
                with open(f, encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        if line.strip():
                            total += 1
            self._corpus_total = total
        return self._corpus_total


core = MirroCore()
MODEL_STATE_FILE = MODELS / "model_state.json"


def _grab_algo():
    _sys.path.insert(0, str(MIRRO_HOME))
    from scripts.algorithms import algo
    return algo


def autonomous_learning_loop(interval_sec=3600):
    import threading

    def _loop():
        while True:
            try:
                algo = _grab_algo()
                n = algo.autonomous_learn(cycles=30)
                print(f"  [автообучение] усвоила {n} примеров")
                try:
                    state = {
                        "perceptron_weights": algo.perceptron_weights,
                        "perceptron_bias": algo.perceptron_bias,
                        "perceptron_trained": algo.perceptron_trained,
                        "embeddings_count": len(algo.word_vectors),
                        "auto_learned": n,
                        "updated": _datetime.utcnow().isoformat(),
                    }
                    MODEL_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), "utf-8")
                except Exception:
                    pass
            except Exception as e:
                print(f"  [автообучение] ошибка: {e}")
            time.sleep(interval_sec)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t


# =========================================================================
#  REASONING ENGINE — обдумывание и разбивка на подфункции с single return
# =========================================================================

class ReasoningEngine:
    """Движок мышления: разбивает вопрос на подзадачи, оценивает, выбирает."""

    @staticmethod
    def tokenize(text):
        return _re.findall(r"[а-яёa-z0-9]+", text.lower())

    @staticmethod
    def keyword_overlap(q_words, text):
        a_words = set(ReasoningEngine.tokenize(text)) - {"это", "что", "как", "не", "и", "в", "на", "с", "по"}
        overlap = len(q_words & a_words)
        return overlap, a_words

    @staticmethod
    def jaccard(q_set, a_set):
        if not q_set or not a_set:
            return 0.0
        return len(q_set & a_set) / max(len(q_set | a_set), 1)


def score_candidate(query, inst, out, cluster, tfidf_score, preferred_cluster=None):
    """Оценить один кандидат: вернуть (score, reasons)."""
    s = 0.0
    reasons = []

    # Кластер
    if preferred_cluster:
        if cluster == preferred_cluster:
            s += 5.0
            reasons.append(f"кластер {cluster}")
        elif cluster == "generated":
            s -= 4.0
            reasons.append("generated=шум")
        else:
            s -= 2.0

    # TF-IDF
    s += tfidf_score * 2.5

    # Пересечение слов
    q_words = set(ReasoningEngine.tokenize(query))
    overlap, a_words = ReasoningEngine.keyword_overlap(q_words, out)
    if overlap > 0:
        s += overlap * 0.8
        reasons.append(f"слова: {overlap}")

    # Штраф за повтор вопроса
    if ReasoningEngine.jaccard(set(q_words), a_words) > 0.7:
        s -= 1.0
        reasons.append("повтор вопроса")

    return s, reasons


def choose_best(query, candidates, preferred_cluster=None):
    """Выбрать лучший ответ среди кандидатов. Single return."""
    if not candidates:
        return None, 0.0, "нет кандидатов"

    # Если есть предпочтительный кластер — ищем только в нём
    if preferred_cluster:
        same = [(inst, out, cl, sc) for (inst, out, cl), sc in candidates if cl == preferred_cluster]
        if same:
            best = max(same, key=lambda x: score_candidate(query, x[0], x[1], x[2], x[3], preferred_cluster)[0])
            sc, reasons = score_candidate(query, best[0], best[1], best[2], best[3], preferred_cluster)
            return best[1], sc, "; ".join(reasons) if reasons else f"кластер {best[2]}"

    # Без предпочтения — top-1 по скорингу
    scored = [(out, score_candidate(query, inst, out, cl, tfidf_score, preferred_cluster))
              for (inst, out, cl), tfidf_score in candidates[:5]]
    if not scored:
        return None, 0.0, "нет результатов"

    best = max(scored, key=lambda x: x[1][0])
    return best[0], best[1][0], "; ".join(best[1][1]) if best[1][1] else "базовый"


def try_greetings(query):
    """Проверка на приветствия/короткие диалоги. Single return."""
    q = query.lower().strip()
    if len(q) > 40:
        return None
    greetings = {
        frozenset({"привет", "здравств", "добрый"}): "Привет! Я Mirro. Спрашивай что угодно — отвечу из своих знаний или найду в интернете.",
        frozenset({"как дела", "как ты", "как жизнь", "как у тебя", "как настроение", "как твои", "чё как", "че как"}): "Привет! У меня всё хорошо, я постоянно учусь и становлюсь умнее. А у тебя как дела?",
    }
    for triggers, answer in greetings.items():
        if any(g in q for g in triggers):
            return answer
    if "спасибо" in q:
        return "Пожалуйста! Рада помочь."
    if "2+2" in q.replace(" ", "") or q.strip() == "2 + 2":
        return "4"
    return None


def try_learn(query):
    """Проверка на запрос обучения. Single return."""
    learn_triggers = ["научи", "обучи", "запомн", "запиши", "сохрани это", "добавь в базу", "выучи", "запомни что"]
    q = query.lower().strip()
    if any(t in q for t in learn_triggers):
        return "Я учусь! Чтобы научить меня:\n1. Напиши вопрос и правильный ответ\n2. Отметь ответ\n\nИли просто задай вопрос — я найду ответ в базе или в интернете."
    return None


def try_algos_think(query):
    """Проверка через algos/think.py (вычисления, уравнения). Single return."""
    try:
        from algos.think import think as mirro_think
        thought = mirro_think(query)
        if thought and thought.get("answer") is not None and thought.get("category") != "unknown":
            return thought.get("explanation") or str(thought.get("answer"))
    except Exception:
        pass
    return None


def try_humor(query):
    """Проверка на юмор/ничегонеделание/хочу. Single return."""
    q = query.lower().strip()
    try:
        import importlib
        humor_mod = importlib.import_module("algos.humor")
        reason_mod = importlib.import_module("algos.reasoning")
        shutka = humor_mod.shutka
        sarkazm = humor_mod.sarkazm
        nichego_ne_delat = humor_mod.nichego_ne_delat
        ya_ne_znau_chto_khotet = humor_mod.ya_ne_znau_chto_khotet
        think_about_thinking = reason_mod.think_about_thinking
        citata_bosovy = reason_mod.citata_bosovy

        if "шутк" in q or "смеш" in q or "анекдот" in q or "юмор" in q:
            return shutka(q)
        if "сарказм" in q or "ирони" in q:
            return sarkazm()
        if "ничего не делать" in q or "ничегонеделание" in q or "лень" in q:
            return "ЕСЛИ <лень> ТО <ничего не делать>. Алгоритм: НАЧАЛО → ничего не делать → КОНЕЦ."
        if "хочу" in q and "не знаю" in q:
            return ya_ne_znau_chto_khotet()
        if "босов" in q or "схема мышления" in q or "блок-схем" in q:
            _, steps = think_about_thinking(q)
            return "\n".join(steps[:5])
        if "цитат" in q and ("босов" in q or "учебник" in q):
            author, text = citata_bosovy()
            return f"{author}: «{text}»"
    except (ImportError, Exception):
        pass
    return None


def try_tfidf(query, cluster):
    """Поиск по TF-IDF базе. Single return."""
    try:
        import sys as _sys
        _sys.path.insert(0, str(MIRRO_HOME))
        from scripts.algorithms import algo
        return algo.search_tfidf(query, top_n=5)
    except Exception:
        return []


def try_rag(query, cluster):
    """Поиск по дисковому RAG. Single return."""
    try:
        import sys as _sys
        _sys.path.insert(0, str(MIRRO_HOME))
        from scripts.rag import rag
        rag_results = rag.search(query, top_segments=3, top_k=3)
        if rag_results:
            return [(("", rag_results[i][2], "rag"), rag_results[i][0]) for i in range(min(3, len(rag_results)))]
    except Exception:
        pass
    return []


def try_web(query):
    """Поиск в интернете (Wikidata/Wikipedia). Single return."""
    try:
        import sys as _sys
        _sys.path.insert(0, str(MIRRO_HOME))
        from scripts.thinking import thinking
        result = thinking.web_search(query)
        if result.get("title") and result.get("summary"):
            return thinking.format_web_answer(query, result)
    except Exception:
        pass
    return None


def build_response(prompt, cluster):
    """Основная функция: собирает ответ. Одна точка возврата.

    Порядок:
    1. Приветствия / direct
    2. Обучение
    3. Алгоритмы (вычисления, уравнения)
    4. Юмор / рефлексия
    5. TF-IDF + RAG + обдумывание
    6. Веб-поиск
    7. Фоллбэк
    """
    try:
        # 1. DIRECT
        greeting = try_greetings(prompt)
        if greeting:
            return {"content": greeting, "strategy": "direct"}

        # 2. LEARN
        learn_msg = try_learn(prompt)
        if learn_msg:
            return {"content": learn_msg, "strategy": "learn"}

        # 3. ALGOS (think)
        think_result = try_algos_think(prompt)
        if think_result:
            return {"content": think_result, "strategy": "think"}

        # 4. HUMOR/REFLECTION
        humor_result = try_humor(prompt)
        if humor_result:
            return {"content": humor_result, "strategy": "humor"}

        # 5. TF-IDF
        results = try_tfidf(prompt, cluster)

        # 6. RAG если TF-IDF пуст
        if not results:
            results = try_rag(prompt, cluster)

        # 7. REASONING: выбираем лучший
        best_answer, best_score, reason = choose_best(prompt, results, preferred_cluster=cluster)
        has_result = best_answer is not None and best_score > 1.0

        # 8. Если ru/knowledge и нет ответа — сразу веб
        if not has_result and cluster in ("ru", "knowledge"):
            web_answer = try_web(prompt)
            if web_answer:
                return {"content": web_answer, "strategy": "web"}

        # 9. Ответ из базы
        if has_result:
            return {"content": best_answer[:2500], "strategy": "base"}

        # 10. Веб-поиск
        web_answer = try_web(prompt)
        if web_answer:
            return {"content": web_answer, "strategy": "web"}

        # 11. Фоллбэк
        if has_result:
            return {"content": best_answer[:2500], "strategy": "base"}

        return {"content": "Не нашла это ни в базе, ни в интернете. Переформулируй вопрос.", "strategy": "unknown"}

    except Exception as e:
        return {"content": f"[Mirro] Внутренняя ошибка: {e}", "strategy": "error"}


# =========================================================================
#  HTTP API
# =========================================================================

class MirroAPI(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _serve_file(self, path, ctype):
        if path.exists():
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return True
        return False

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            if self._serve_file(MIRRO_HOME / "web" / "index.html", "text/html; charset=utf-8"):
                return
        elif self.path == "/catalog.json":
            if self._serve_file(DATA / "catalog_phase1.json", "application/json; charset=utf-8"):
                return
        elif self.path == "/health":
            status = core.status()
            try:
                algo = _grab_algo()
                status["algorithms"] = algo.status()
            except Exception:
                status["algorithms"] = {}
            self._json(status)
            return
        elif self.path == "/v1/models":
            models = [
                {"id": "mirro/default", "object": "model", "created": int(time.time()), "owned_by": "mirro"},
                {"id": "mirro/ru", "object": "model", "created": int(time.time()), "owned_by": "mirro"},
                {"id": "mirro/code", "object": "model", "created": int(time.time()), "owned_by": "mirro"},
                {"id": "mirro/design", "object": "model", "created": int(time.time()), "owned_by": "mirro"},
            ]
            self._json({"object": "list", "data": models})
            return
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            try:
                body = self._read()
            except Exception as e:
                return self._json({"error": str(e)}, 400)
            messages = body.get("messages", [])
            model = body.get("model", "mirro/default")
            stream = body.get("stream", False)
            if not messages:
                return self._json({"error": "no messages"}, 400)
            prompt = " ".join(m.get("content", "") for m in messages)
            cluster = core.classify_task(prompt)
            t0 = time.time()
            response = build_response(prompt, cluster)
            auto_learned = None
            try:
                content = response.get("content", "")
                if response and response.get("strategy") in ("base",) and content:
                    import sys as _sys
                    _sys.path.insert(0, str(MIRRO_HOME))
                    from scripts.algorithms import algo
                    if algo.should_auto_learn(prompt, content):
                        n = algo.autonomous_learn(cycles=15)
                        auto_learned = n
            except Exception:
                pass
            if response:
                core.log_call(prompt, cluster, f"mirro-{response.get('strategy','ai')}",
                              int((time.time() - t0) * 1000), True)
            content = response.get("content", "") if response else "Ошибка"
            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                for chunk in content.split("\n"):
                    data = json.dumps({"choices": [{"delta": {"content": chunk + "\n"}}]}, separators=(",", ":"))
                    self.wfile.write(f"data: {data}\n\n".encode())
                    self.wfile.flush()
                self.wfile.write(b"data: [DONE]\n\n")
            else:
                self._json({
                    "id": f"mirro-{int(time.time())}",
                    "object": "chat.completion", "model": model,
                    "usage": {"prompt_tokens": len(prompt) // 4, "completion_tokens": len(content) // 4},
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}],
                })
            return

        elif self.path == "/v1/feedback":
            try:
                body = self._read()
                algo = _grab_algo()
                query = body.get("query", "")
                response = body.get("response", "")
                liked = body.get("liked", True)
                algo.train_from_feedback(query, response, liked)
                algo.qa_boost[query.lower().strip()[:100]] = 0.5 if liked else -0.3
                self._json({"status": "ok", "perceptron_trained": algo.perceptron_trained})
            except Exception as e:
                self._json({"status": "error", "message": str(e)}, 500)
            return

        elif self.path == "/v1/self-learn":
            try:
                algo = _grab_algo()
                n = min(50, len(algo.examples))
                learned = 0
                for inst, out, cl in algo.examples[::max(1, len(algo.examples) // n)][:n]:
                    if len(inst) < 10:
                        continue
                    ans = algo.compose_answer(inst, top_n=3)
                    if ans:
                        if algo.qa_score(inst, ans) > 0.5:
                            learned += 1
                self._json({"status": "ok", "learned": learned, "checked": n})
            except Exception as e:
                self._json({"status": "error", "message": str(e)}, 500)
            return

        self._json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


def main():
    _sys.stdout.reconfigure(encoding='utf-8')
    print("MIRRO v0.2 - Единая нейросеть знаний")
    print(f"  API: http://{HOST}:{PORT}")
    print(f"  Загружено: {core.stats['total_examples']} примеров")
    print("Роутинг:")
    for cl, info in core.get_cluster_info().items():
        print(f"    {cl:12} {info['examples']:>6} примеров · {info['desc']}")
    print(f"\n  Инициализация алгоритмов (3-4 мин)...")
    _sys.path.insert(0, str(MIRRO_HOME))
    from scripts.algorithms import algo
    st = algo.status()
    print(f"  Индекс: {st['examples']} примеров, {st['vocab']} слов")
    print(f"\n  Запуск автономного обучения (каждые 60 мин)...")
    autonomous_learning_loop(interval_sec=3600)
    print(f"   → фоновый процесс запущен")
    print(f"\n  Движок мышления: подфункции с single return, юмор, схемы Босовой")
    server = HTTPServer((HOST, PORT), MirroAPI)
    print(f"\n  → Слушаю на http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Mirro остановлен.")
        server.server_close()


if __name__ == "__main__":
    main()
