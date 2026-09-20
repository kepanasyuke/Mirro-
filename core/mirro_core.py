# -*- coding: utf-8 -*-
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
for d in [CORE, LOGS, MODELS]: d.mkdir(parents=True, exist_ok=True)
HOST, PORT = "127.0.0.1", 3443

KNOWLEDGE_CLUSTERS = {
    "ru": {"desc": "Русский язык, диалоги, инструкции", "priority": 10},
    "code": {"desc": "Программирование, алгоритмы, код", "priority": 10},
    "math": {"desc": "Математика, логика, рассуждения", "priority": 9},
    "design": {"desc": "UI/UX, SVG, HTML/CSS, графика, вёрстка", "priority": 9},
    "knowledge": {"desc": "Наука, история, география, право, медицина", "priority": 8},
    "general": {"desc": "Общие инструкции и диалоги", "priority": 7},
}
TASK_ROUTES = {}
for d in [
    {"код":"code","python":"code","javascript":"code","js":"code","алгоритм":"code","отлад":"code","баг":"code","библиотек":"code","docker":"code","git":"code","api":"code","sql":"code","скрипт":"code","программ":"code"},
    {"css":"design","svg":"design","дизайн":"design","график":"design","рисун":"design","верстк":"design","вёрстк":"design","ui":"design","ux":"design","логотип":"design","иконк":"design","макет":"design","фото":"design","презентац":"design","слайд":"design","интерфейс":"design"},
    {"математик":"math","уравнен":"math","формул":"math","вычисли":"math","процент":"math","геометри":"math","алгебр":"math","статистик":"math"},
    {"налог":"ru","договор":"ru","юрист":"ru","бухгалтер":"ru","ндс":"ru","усн":"ru","осно":"ru","ип":"ru","ооо":"ru","суд":"ru","закон":"ru"},
    {"истори":"knowledge","географи":"knowledge","наук":"knowledge","биологи":"knowledge","хими":"knowledge","физик":"knowledge","медицин":"knowledge","экономик":"knowledge","столиц":"knowledge","страна":"knowledge"},
]:
    TASK_ROUTES.update(d)

class MirroCore:
    def __init__(self):
        self.processed_dir = DATA / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        self.stats = self._load_json(CORE / "stats.json") or {"calls": 0, "clusters_used": Counter(), "sources_count": 0, "total_examples": 0}
        self.knowledge_base = defaultdict(list)
        self._load_knowledge()
    def _load_json(self, path):
        try: return json.loads(path.read_text("utf-8"))
        except: return None
    def _save_json(self, path, data): path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    def _load_knowledge(self):
        for f in self.processed_dir.glob("*.jsonl"):
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        try: self.knowledge_base[f.stem].append(json.loads(line))
                        except: pass
        self.stats["total_examples"] = sum(len(v) for v in self.knowledge_base.values())
    def classify_task(self, prompt):
        prompt_lower = prompt.lower(); scores = defaultdict(float)
        for keyword, cluster in TASK_ROUTES.items():
            c = prompt_lower.count(keyword)
            if c: scores[cluster] += c * KNOWLEDGE_CLUSTERS.get(cluster, {}).get("priority", 1)
        for cl in scores: scores[cl] += self.stats["clusters_used"].get(cl, 0) * 0.01
        if scores: return max(scores, key=scores.get)
        ru_chars = sum(1 for c in prompt if '\u0400' <= c <= '\u04FF')
        if ru_chars > 3: return "ru"
        if any(c in prompt for c in "{}[]();=<>"): return "code"
        return "general"
    def log_call(self, prompt, cluster, provider, latency_ms, success, tokens=0):
        self.stats["calls"] += 1
        self.stats["clusters_used"][cluster] = self.stats["clusters_used"].get(cluster, 0) + 1
        with open(LOGS / "calls.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _datetime.utcnow().isoformat(), "cluster": cluster, "provider": provider, "latency_ms": latency_ms, "success": success, "prompt_len": len(prompt)}, ensure_ascii=False) + "\n")
        self._save_json(CORE / "stats.json", dict(self.stats))
    def get_cluster_info(self):
        return {name: {**info, "examples": len(self.knowledge_base.get(name, [])), "calls": self.stats["clusters_used"].get(name, 0)} for name, info in KNOWLEDGE_CLUSTERS.items()}
    def status(self):
        return {"name": "Mirro", "version": "0.2", "total_calls": self.stats["calls"], "total_examples": self.stats["total_examples"], "clusters": self.get_cluster_info(), "api": f"http://{HOST}:{PORT}/v1/chat/completions"}
    def corpus_total(self):
        if not hasattr(self, "_corpus_total"):
            t = 0
            for f in (DATA / "corpus_big").glob("*.jsonl"):
                with open(f, encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        if line.strip(): t += 1
            self._corpus_total = t
        return self._corpus_total

core = MirroCore()
MODEL_STATE_FILE = MODELS / "model_state.json"

def _grab_algo():
    sys.path.insert(0, str(MIRRO_HOME))
    from scripts.algorithms import algo
    return algo

def autonomous_learning_loop(interval_sec=3600):
    import threading
    def _loop():
        while True:
            try:
                algo = _grab_algo(); n = algo.autonomous_learn(cycles=30)
                print(f"  [автообучение] усвоила {n} примеров")
                try: MODEL_STATE_FILE.write_text(json.dumps({
                    "perceptron_weights": algo.perceptron_weights, "perceptron_bias": algo.perceptron_bias,
                    "perceptron_trained": algo.perceptron_trained, "auto_learned": n,
                    "updated": _datetime.utcnow().isoformat()}, ensure_ascii=False), "utf-8")
                except: pass
            except Exception as e: print(f"  [автообучение] ошибка: {e}")
            time.sleep(interval_sec)
    t = threading.Thread(target=_loop, daemon=True); t.start(); return t

# ========== REASONING ENGINE ==========
def _tokenize(text): return _re.findall(r"[а-яёa-z0-9]+", text.lower())

def score_candidate(query, out, cluster, tfidf_score, preferred=None):
    s = tfidf_score * 2.5
    reasons = []
    if preferred:
        if cluster == preferred: s += 5.0
        elif cluster == "generated": s -= 4.0
        else: s -= 2.0
    q_set = set(_tokenize(query))
    a_set = set(_tokenize(out))
    overlap = len(q_set & a_set)
    if overlap > 0: s += overlap * 0.8; reasons.append(f"слова:{overlap}")
    if len(out) < 20: s -= 0.5
    if q_set and a_set and len(q_set & a_set) / max(len(q_set | a_set), 1) > 0.7: s -= 1.0
    return s, reasons

def choose_best(query, candidates, preferred=None):
    if not candidates: return None, 0.0, "нет кандидатов"
    # Всегда исключаем шумный generated, если есть альтернативы
    cands = [c for c in candidates if c[0][2] != "generated"] or candidates
    if preferred:
        same = [(inst, out, cl, sc) for (inst, out, cl), sc in cands if cl == preferred]
        if same:
            best = max(same, key=lambda x: score_candidate(query, x[1], x[2], x[3], preferred)[0])
            sc, _ = score_candidate(query, best[1], best[2], best[3], preferred)
            return best[1], sc, f"кластер {best[2]}"
        # В предпочтительном кластере нет ответа — не тянем мусор из чужих кластеров
        return None, 0.0, f"нет в кластере {preferred}"
    b_out, b_sc, b_r = None, -999, ""
    for (inst, out, cl), tfidf_score in cands[:5]:
        sc, rs = score_candidate(query, out, cl, tfidf_score, preferred)
        if sc > b_sc: b_sc, b_out, b_r = sc, out, "; ".join(rs) if rs else "базовый"
    return b_out, b_sc, b_r

def try_greetings(query):
    q = query.lower().strip()
    if len(q) > 40: return None
    if any(g in q for g in ["привет","здравств","добрый"]): return "Привет! Я Mirro. Спрашивай что угодно — отвечу из своих знаний или найду в интернете."
    if any(g in q for g in ["как дела","как ты","как жизнь","как у тебя","как настроение","как твои"]): return "Привет! У меня всё хорошо, я постоянно учусь и становлюсь умнее. А у тебя как дела?"
    if "спасибо" in q: return "Пожалуйста! Рада помочь."
    if "2+2" in q.replace(" ","") or q == "2+2": return "4"
    return None

def try_learn(query):
    q = query.lower().strip()
    if any(t in q for t in ["научи","обучи","запомн","запиши","сохрани это","добавь в базу","выучи","запомни что"]):
        return "Я учусь! Чтобы научить меня:\n1. Напиши вопрос и правильный ответ\n2. Отметь ответ\n\nИли просто задай вопрос — я найду ответ в базе или в интернете."
    return None

def try_algos_think(query):
    try:
        from algos.think import think as mirro_think
        thought = mirro_think(query)
        if thought and thought.get("answer") is not None and thought.get("category") != "unknown":
            return thought.get("explanation") or str(thought.get("answer"))
    except: pass
    return None

def try_humor(query):
    q = query.lower().strip()
    try:
        from algos.humor import shutka, sarkazm, ya_ne_znau_chto_khotet, o_udache_i_uspehe
        from algos.reasoning import think_about_thinking, citata_bosovy
        if "шутк" in q or "смеш" in q or "анекдот" in q or "юмор" in q: return shutka(q)
        if "сарказм" in q or "ирони" in q: return sarkazm()
        if "ничего не делать" in q or "ничегонеделание" in q or "лень" in q: return "ЕСЛИ <лень> ТО <ничего не делать>. Алгоритм: НАЧАЛО → ничего не делать → КОНЕЦ."
        if "хочу" in q and "не знаю" in q: return ya_ne_znau_chto_khotet()
        if "удач" in q or "успех" in q or "успеха" in q or "веришь" in q or "веришь ли" in q: return o_udache_i_uspehe()
        if "босов" in q or "блок-схем" in q or "схема мышления" in q:
            _, steps = think_about_thinking(q); return "\n".join(steps[:6])
        if "цитат" in q and ("босов" in q or "учебник" in q):
            author, text = citata_bosovy(); return f"{author}: «{text}»"
    except: pass
    return None

def try_tfidf(query, cluster):
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.algorithms import algo
        return algo.search_tfidf(query, top_n=5)
    except: return []

def try_rag(query, cluster):
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.rag import rag
        rr = rag.search(query, top_segments=3, top_k=3)
        if rr: return [(("", rr[i][2], "rag"), rr[i][0]) for i in range(min(3, len(rr)))]
    except: pass
    return []

def try_web(query):
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.thinking import thinking
        result = thinking.web_search(query)
        if result.get("title") and result.get("summary"): return thinking.format_web_answer(query, result)
    except: pass
    return None


def answer_looks_bad(query, answer):
    """Проверка качества ответа: реально ли он отвечает на вопрос?

    Возвращает True, если ответ мусорный — его нельзя отдавать пользователю.
    """
    if not answer or len(answer) < 10:
        return True
    # Ответ похож на код (PHP/JS/C++/SQL) — а вопрос фактологический
    code_markers = ["<?php", "function ", "std::", "#include", "import ", "class ", "=>", "console.", "npm ", "git ", "def "]
    code_hits = sum(1 for m in code_markers if m in answer)
    if code_hits >= 2:
        return True
    # Вопрос вида «что такое X / кто такой X» — ответ должен содержать ключевые слова
    q = query.lower().strip()
    is_factual = any(p in q for p in ["что такое", "кто такой", "кто такая", "что значит", "расскажи про", "что такое ндс"])
    if is_factual:
        q_words = set(_re.findall(r"[а-яёa-z0-9]{3,}", q))
        a_words = set(_re.findall(r"[а-яёa-z0-9]{3,}", answer.lower()))
        # Ключевые слова вопроса: убираем стоп-слова
        stop = {"что", "такое", "кто", "такой", "такая", "значит", "расскажи", "про", "это", "как", "для", "или"}
        key = q_words - stop
        if key and not key & a_words:
            return True  # ответ вообще не про это
    return False


def _voice(raw, query, strategy="base"):
    """Обернуть сырой ответ в голос Mirro (свои слова, характер)."""
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.voice import speak
        return speak(raw, query, strategy)
    except Exception:
        return raw


def build_response(prompt, cluster):
    try:
        greeting = try_greetings(prompt)
        if greeting: return {"content": greeting, "strategy": "direct"}
        learn_msg = try_learn(prompt)
        if learn_msg: return {"content": learn_msg, "strategy": "learn"}
        think_result = try_algos_think(prompt)
        if think_result: return {"content": think_result, "strategy": "think"}
        humor_result = try_humor(prompt)
        if humor_result: return {"content": humor_result, "strategy": "humor"}
        results = try_tfidf(prompt, cluster)
        if not results: results = try_rag(prompt, cluster)
        best_answer, best_score, reason = choose_best(prompt, results, preferred=cluster)
        has_result = best_answer is not None and best_score > 1.0

        # Шлюз качества: если ответ мусорный — не отдаём, ищем в вебе
        bad_answer = has_result and answer_looks_bad(prompt, best_answer)
        if bad_answer:
            web_answer = try_web(prompt)
            if web_answer: return {"content": _voice(web_answer, prompt, "web"), "strategy": "web"}
            return {"content": "Не нашла нормального ответа в базе, а в интернете — пока недоступен. Переформулируй вопрос.", "strategy": "web"}

        if not has_result and cluster in ("ru", "knowledge"):
            web_answer = try_web(prompt)
            if web_answer: return {"content": _voice(web_answer, prompt, "web"), "strategy": "web"}
        if has_result: return {"content": _voice(best_answer, prompt, "base")[:2500], "strategy": "base"}
        web_answer = try_web(prompt)
        if web_answer: return {"content": _voice(web_answer, prompt, "web"), "strategy": "web"}
        if has_result: return {"content": _voice(best_answer, prompt, "base")[:2500], "strategy": "base"}
        return {"content": "Не нашла это ни в базе, ни в интернете. Переформулируй вопрос.", "strategy": "unknown"}
    except Exception as e:
        return {"content": f"[Mirro] Внутренняя ошибка: {e}", "strategy": "error"}

# ========== HTTP API ==========
class MirroAPI(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers(); self.wfile.write(body)
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
            self.end_headers(); self.wfile.write(body)
            return True
        return False
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            if self._serve_file(MIRRO_HOME / "web" / "index.html", "text/html; charset=utf-8"): return
        elif self.path == "/catalog.json":
            if self._serve_file(DATA / "catalog_phase1.json", "application/json; charset=utf-8"): return
        elif self.path == "/health":
            status = core.status()
            try: status["algorithms"] = _grab_algo().status()
            except: status["algorithms"] = {}
            self._json(status); return
        elif self.path == "/v1/models":
            t = int(time.time())
            self._json({"object": "list", "data": [
                {"id": "mirro/default", "object": "model", "created": t, "owned_by": "mirro"},
                {"id": "mirro/ru", "object": "model", "created": t, "owned_by": "mirro"},
            ]}); return
        self._json({"error": "not found"}, 404)
    def do_POST(self):
        if self.path == "/v1/chat/completions":
            try: body = self._read()
            except: return self._json({"error": "bad request"}, 400)
            messages = body.get("messages", [])
            model = body.get("model", "mirro/default")
            stream = body.get("stream", False)
            if not messages: return self._json({"error": "no messages"}, 400)
            prompt = " ".join(m.get("content", "") for m in messages)
            cluster = core.classify_task(prompt)
            t0 = time.time()
            response = build_response(prompt, cluster)
            try:
                if response.get("strategy") in ("base",) and response.get("content"):
                    algo = _grab_algo()
                    if algo.should_auto_learn(prompt, response["content"]):
                        algo.autonomous_learn(cycles=15)
            except: pass
            if response: core.log_call(prompt, cluster, f"mirro-{response.get('strategy','ai')}", int((time.time()-t0)*1000), True)
            content = response.get("content", "") if response else "Ошибка"
            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache"); self.end_headers()
                for chunk in content.split("\n"):
                    self.wfile.write(f"data: {json.dumps({'choices':[{'delta':{'content':chunk+chr(10)}}]}, separators=(',',':'))}\n\n".encode())
                    self.wfile.flush()
                self.wfile.write(b"data: [DONE]\n\n")
            else:
                self._json({"id": f"mirro-{int(time.time())}", "object": "chat.completion", "model": model,
                            "usage": {"prompt_tokens": len(prompt)//4, "completion_tokens": len(content)//4},
                            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}]})
            return
        elif self.path == "/v1/feedback":
            try:
                body = self._read(); algo = _grab_algo()
                algo.train_from_feedback(body.get("query",""), body.get("response",""), body.get("liked",True))
                self._json({"status": "ok"})
            except Exception as e: self._json({"status": "error", "message": str(e)}, 500)
            return
        elif self.path == "/v1/self-learn":
            try:
                algo = _grab_algo(); n = min(50, len(algo.examples)); learned = 0
                for inst, out, cl in algo.examples[::max(1, len(algo.examples)//n)][:n]:
                    if len(inst) < 10: continue
                    ans = algo.compose_answer(inst, top_n=3)
                    if ans and algo.qa_score(inst, ans) > 0.5: learned += 1
                self._json({"status": "ok", "learned": learned, "checked": n})
            except Exception as e: self._json({"status": "error", "message": str(e)}, 500)
            return
        self._json({"error": "not found"}, 404)
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
    def log_message(self, fmt, *args): pass

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("MIRRO v0.2 - Единая нейросеть знаний")
    print(f"  API: http://{HOST}:{PORT}")
    print(f"  Загружено: {core.stats['total_examples']} примеров")
    for cl, info in core.get_cluster_info().items():
        print(f"    {cl:12} {info['examples']:>6} примеров · {info['desc']}")
    print("\n  Инициализация алгоритмов (3-4 мин)...")
    sys.path.insert(0, str(MIRRO_HOME))
    from scripts.algorithms import algo
    st = algo.status()
    print(f"  Индекс: {st['examples']} примеров, {st['vocab']} слов")
    print("  Движок мышления: подфункции single return, юмор, схемы Босовой")
    print("\n  Запуск автономного обучения (каждые 60 мин)...")
    autonomous_learning_loop(interval_sec=3600)
    server = HTTPServer((HOST, PORT), MirroAPI)
    print(f"\n  → Слушаю на http://{HOST}:{PORT}")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\n  Mirro остановлен."); server.server_close()

if __name__ == "__main__":
    main()