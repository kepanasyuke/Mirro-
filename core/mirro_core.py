#!/usr/bin/env python3
"""
Mirro Core AI — единая нейросеть знаний
========================================
- Собственные алгоритмы (TF-IDF + TextRank + Naive Bayes + самокоррекция)
- Без внешних API, без зависимостей
- OpenAI-совместимый API на порту 3443
- Веб-интерфейс на /
"""

import json, os, time, random, re as _re
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict, Counter
from datetime import datetime

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
    """Ядро Mirro — хранилище знаний, роутинг, статистика."""

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
            "ts": datetime.utcnow().isoformat(), "cluster": cluster,
            "provider": provider, "latency_ms": latency_ms,
            "success": success, "prompt_len": len(prompt),
        }
        with open(LOGS / "calls.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._save_json(CORE / "stats.json", dict(self.stats))

    def get_cluster_info(self):
        out = {}
        for name, info in KNOWLEDGE_CLUSTERS.items():
            out[name] = {
                **info,
                "examples": len(self.knowledge_base.get(name, [])),
                "calls": self.stats["clusters_used"].get(name, 0),
            }
        return out

    def status(self):
        return {
            "name": "Mirro", "version": "0.2",
            "total_calls": self.stats["calls"],
            "total_examples": self.stats["total_examples"],
            "corpus_examples": self.corpus_total(),
            "clusters": self.get_cluster_info(),
            "api": f"http://{HOST}:{PORT}/v1/chat/completions",
        }

    def corpus_total(self):
        """Количество примеров в большом корпусе на диске (corpus_big)."""
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

# =====================================================
#  АВТОНОМНОЕ ОБУЧЕНИЕ — планировщик каждые 60 мин
# =====================================================
def _grab_algo():
    import sys as _sys
    _sys.path.insert(0, str(MIRRO_HOME))
    from scripts.algorithms import algo
    return algo

def autonomous_learning_loop(interval_sec=3600):
    """Фоновый поток: каждые interval_sec Mirro учится сама."""
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
                        "updated": datetime.utcnow().isoformat(),
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


class MirroAPI(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _get_thinking(self):
        """Получить движок алгоритмов включения."""
        import sys as _sys
        _sys.path.insert(0, str(MIRRO_HOME))
        from scripts.thinking import thinking
        return thinking

    def _reason(self, query, candidates, preferred_cluster=None):
        if not candidates:
            return None, 0.0, "Нет кандидатов"

        q_words = set()
        import re as _re
        for w in _re.findall(r"[а-яёa-z0-9]+", query.lower()):
            if len(w) > 2:
                q_words.add(w)

        def _score(inst, out, cl):
            s = 0.0
            a_words = set()
            for w in _re.findall(r"[а-яёa-z0-9]+", out.lower()):
                if len(w) > 2:
                    a_words.add(w)
            overlap = len(q_words & a_words)
            if overlap > 0:
                s += overlap * 0.8
            if len(out) > 100:
                s += 0.3
            elif len(out) < 20:
                s -= 0.5
            q_set = set(q_words)
            a_set = set(a_words)
            if q_set and a_set:
                jaccard = len(q_set & a_set) / max(len(q_set | a_set), 1)
                if jaccard > 0.7:
                    s -= 1.0
            return s

        # Если есть preferred_cluster — оцениваем только кандидатов из него
        if preferred_cluster:
            same = [(inst, out, cl, sc) for (inst, out, cl), sc in candidates if cl == preferred_cluster]
            if same:
                best = max(same, key=lambda x: _score(x[0], x[1], x[2]) + x[3] * 2.5)
                inst, out, cl, tfidf_sc = best
                best_score = _score(inst, out, cl) + tfidf_sc * 2.5
                return out, best_score, f"кластер {cl}"

        best = None
        best_score = 0.0
        reason = ""
        for (inst, out, cl), tfidf_score in candidates[:5]:
            score = _score(inst, out, cl) + tfidf_score * 2.5
            if score > best_score:
                best_score = score
                best = out
                reason = "совпадение по словам"
        return best, best_score, reason

    def _call_smart(self, prompt, cluster):
        """
        Умный пайплайн: алгоритм включения + обдумывание.
        """
        try:
            import sys as _sys
            _sys.path.insert(0, str(MIRRO_HOME))
            from scripts.thinking import thinking

            q = prompt.lower().strip()

            # 0. DIRECT: приветствия, спасибо — сразу, без поисков
            if any(g in q for g in ["привет", "здравств", "добрый"]) and len(q) < 40:
                return {"content": "Привет! Я Mirro. Спрашивай что угодно — отвечу из своих знаний или найду в интернете.", "strategy": "direct"}
            if any(g in q for g in ["как дела", "как ты", "как жизнь", "как у тебя", "как настроение", "как твои дела", "как твои", "чё как", "че как", "как сам", "как сама"]) and len(q) < 40:
                return {"content": "Привет! У меня всё хорошо, я постоянно учусь и становлюсь умнее. А у тебя как дела?", "strategy": "direct"}
            if "2+2" in q or q.strip() == "2 + 2":
                return {"content": "4", "strategy": "direct"}
            if "спасибо" in q and len(q) < 20:
                return {"content": "Пожалуйста! Рада помочь.", "strategy": "direct"}

            # 0b. LEARN
            if any(t in q for t in thinking.LEARN_TRIGGERS):
                return {"content": (
                    "Я учусь! Чтобы научить меня:\n"
                    "1. Напиши вопрос и правильный ответ\n"
                    "2. Отметь ответ\n\n"
                    "Или просто задай вопрос — я найду ответ в базе или в интернете."
                ), "strategy": "learn"}

            # 1. Думаем алгоритмами (вычисления, уравнения, НОД и т.п.)
            try:
                from algos.think import think as mirro_think
                thought = mirro_think(prompt)
                if thought and thought.get("answer") is not None and thought.get("category") != "unknown":
                    expl = thought.get("explanation") or ""
                    if not expl:
                        expl = str(thought.get("answer"))
                    return {"content": expl, "strategy": "think"}
            except Exception:
                pass

            # 2. TF-IDF база знаний
            algo = self._get_ai()
            try:
                results = algo.search_tfidf(prompt, top_n=5)
            except Exception:
                results = []

            # 3. RAG 
            rag_tried = False
            if not results:
                try:
                    from scripts.rag import rag
                    rag_results = rag.search(prompt, top_segments=3, top_k=3)
                    if rag_results:
                        results = [(("", rag_results[i][2], "rag"), rag_results[i][0]) for i in range(min(3, len(rag_results)))]
                except Exception:
                    pass

            # 4. Обдумывание: выбираем лучший кандидат с учётом кластера
            best_answer, best_score, reason = self._reason(prompt, results, preferred_cluster=cluster)
            has_result = best_answer is not None and best_score > 1.0
            confidence = min(1.0, best_score / 4.0)
            strategy = thinking.decide(prompt, base_confidence=confidence, has_base_result=has_result)

            if has_result and strategy in ("base", "base+web", "direct"):
                return {"content": best_answer[:2500], "strategy": strategy}

            try:
                web_result = thinking.web_search(prompt)
                if web_result.get("title") and web_result.get("summary"):
                    return {"content": thinking.format_web_answer(prompt, web_result), "strategy": "web"}
            except Exception:
                pass

            if has_result:
                return {"content": best_answer[:2500], "strategy": "base"}

            return {"content": "Не нашла это ни в базе, ни в интернете. Переформулируй вопрос.", "strategy": "unknown"}

        except Exception as e:
            return {"content": f"[Mirro] Внутренняя ошибка: {e}", "strategy": "error"}

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

    def _get_ai(self):
        import sys as _sys
        _sys.path.insert(0, str(MIRRO_HOME))
        from scripts.algorithms import algo
        return algo

    def _call_ai(self, messages, cluster):
        """Генерация ответа через собственные алгоритмы Mirro."""
        prompt = " ".join(m.get("content", "") for m in messages)
        try:
            algo = self._get_ai()
            content = algo.compose_answer(prompt)
            if content and len(content) > 30:
                return {"content": content}
        except Exception:
            pass
        ctx = core.get_context(cluster, 3)
        if ctx:
            for ex in ctx:
                out = ex.get("output", ex.get("assistant", ""))
                if out and len(out) > 30:
                    return {"content": out[:2000]}
        return {"content": f"[Mirro/{cluster}] Я ещё учусь. Задай вопрос иначе."}

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            if self._serve_file(MIRRO_HOME / "web" / "index.html", "text/html; charset=utf-8"):
                return
        elif self.path == "/catalog.json":
            if self._serve_file(DATA / "catalog_phase1.json", "application/json; charset=utf-8"):
                return
        elif self.path == "/health":
            status = core.status()
            try:
                algo = self._get_ai()
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
            try:
                response = self._call_smart(prompt, cluster)
            except Exception as e:
                # Сервер никогда не должен падать
                response = {"content": f"[исключение] {e}", "strategy": "error"}

            # ===== АВТООБУЧАЛКА =====
            # Mirro сама запускает дообучение, если ответ слабый
            auto_learned = None
            try:
                content = response.get("content", "") if response else ""
                if response and response.get("strategy") in ("base", "base+web") and content:
                    import sys as _sys
                    _sys.path.insert(0, str(MIRRO_HOME))
                    from scripts.algorithms import algo
                    if algo.should_auto_learn(prompt, content):
                        n = algo.autonomous_learn(cycles=15)
                        auto_learned = n
            except Exception:
                pass

            if response:
                core.log_call(prompt, cluster, f"mirro-{response.get('strategy','ai')}", int((time.time() - t0) * 1000), True)
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
                algo = self._get_ai()
                query = body.get("query", "")
                response = body.get("response", "")
                liked = body.get("liked", True)
                # Обучаем перцептрон на feedback
                algo.train_from_feedback(query, response, liked)
                # Также сохраняем boost
                algo.qa_boost[query.lower().strip()[:100]] = 0.5 if liked else -0.3
                self._json({"status": "ok", "perceptron_trained": algo.perceptron_trained})
            except Exception as e:
                self._json({"status": "error", "message": str(e)}, 500)
            return

        elif self.path == "/v1/self-learn":
            try:
                algo = self._get_ai()
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
    # Принудительно переключаем stdout на UTF-8 (иначе cp1251 ломает unicode)
    import sys as _sys
    _sys.stdout.reconfigure(encoding='utf-8')
    print("MIRRO v0.2 - Единая нейросеть знаний")
    print(f"  API: http://{HOST}:{PORT}")
    print(f"  Загружено: {core.stats['total_examples']} примеров")
    print("Роутинг:")
    for cl, info in core.get_cluster_info().items():
        print(f"    {cl:12} {info['examples']:>6} примеров · {info['desc']}")

    print(f"\n  Инициализация алгоритмов (3-4 мин)...")
    import sys as _sys
    _sys.path.insert(0, str(MIRRO_HOME))
    from scripts.algorithms import algo
    st = algo.status()
    print(f"  Индекс: {st['examples']} примеров, {st['vocab']} слов")

    # Запуск автономного обучения
    print(f"\n  Запуск автономного обучения (каждые 60 мин)...")
    autonomous_learning_loop(interval_sec=3600)
    print(f"   → фоновый процесс запущен")

    server = HTTPServer((HOST, PORT), MirroAPI)
    print(f"\n  → Слушаю на http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Mirro остановлен.")
        server.server_close()


if __name__ == "__main__":
    main()