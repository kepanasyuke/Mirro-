# -*- coding: utf-8 -*-
import json, os, socket, time, random, re as _re, sys
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from collections import defaultdict, Counter
from datetime import datetime as _datetime

MIRRO_HOME = Path(__file__).resolve().parent.parent
CORE = MIRRO_HOME / "core"
DATA = MIRRO_HOME / "data"
LOGS = MIRRO_HOME / "logs"
MODELS = MIRRO_HOME / "models"
for d in [CORE, LOGS, MODELS]: d.mkdir(parents=True, exist_ok=True)
# Хост/порт настраиваются через env. По умолчанию — 127.0.0.1 (только локально).
# Для доступа по локальной сети (WiFi/модем): $env:MIRRO_HOST="0.0.0.0"
HOST = os.environ.get("MIRRO_HOST", "127.0.0.1")
PORT = int(os.environ.get("MIRRO_PORT", "3443"))
# Авторизация для публичного доступа. Если MIRRO_TOKEN задан (непустой),
# все запросы должны нести его (заголовок Authorization: Bearer <token> или
# query-параметр ?token=), иначе — 401. Пока токен пуст — локальный режим без
# пароля (как раньше). Безопасность публичного режима держится на этом токене.
AUTH_TOKEN = os.environ.get("MIRRO_TOKEN", "").strip()

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

def _append_call_log(prompt, cluster, provider, latency_ms, success, tokens=0):
    """Одна строка аудита вызова в logs/calls.jsonl. Ошибка записи не должна
    ронять запрос клиента — только пропускаем лог. Один return: None."""
    entry = {"ts": _utc_now_iso(), "cluster": cluster, "provider": provider,
             "latency_ms": latency_ms, "success": success, "tokens": tokens,
             "prompt_len": len(prompt or "")}
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        _write_call_line(LOGS / "calls.jsonl", json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return None


def _content_length(headers):
    """Content-Length без падения на мусоре: отрицательное и нечисловое → 0.
    Один return: int."""
    length = 0
    try:
        length = max(0, int(headers.get("Content-Length", 0) or 0))
    except (TypeError, ValueError):
        length = 0
    return length


def _write_call_line(path, line):
    """Дописывает строку в файл лога вызовов. Один return: None."""
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line)
    return None


def _utc_now_iso():
    """Отметка времени UTC в ISO 8601 (utcnow устарел в Python 3.12+).
    Один return: str."""
    stamp = ""
    try:
        from datetime import timezone
        stamp = _datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    except Exception:
        stamp = ""
    return stamp


class MirroCore:
    def __init__(self):
        self.processed_dir = DATA / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        self.stats = self._load_json(CORE / "stats.json") or {"calls": 0, "clusters_used": Counter(), "sources_count": 0, "total_examples": 0}
        self.knowledge_base = defaultdict(list)
        self.knowledge_counts = {}
        self._load_knowledge()
    def _load_json(self, path):
        value = None
        try:
            value = json.loads(path.read_text("utf-8"))
        except Exception:
            value = None
        return value
    def _save_json(self, path, data): path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    def _load_knowledge(self):
        # Считаем строки, а не разбираем JSON: содержимое этой базы нигде не читается,
        # нужны только количества по файлам. Экономит ~1.5 ГБ RAM и десятки секунд старта.
        # Счётчики кэшируем по размеру и mtime файла: повторный старт не перечитывает 1.47 ГБ.
        _lite = os.environ.get("MIRRO_LITE", "").strip().lower() in ("1", "true", "yes", "on")
        cap = 100_000 if _lite else None
        cache_path = MODELS / "knowledge_counts.json"
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
        changed = False
        for f in self.processed_dir.glob("*.jsonl"):
            try:
                st = f.stat()
            except OSError:
                continue
            key = "%s|%s" % (f.name, cap)
            hit = cache.get(key)
            if (hit and hit[0] == st.st_size and abs(hit[1] - st.st_mtime) < 1
                    and len(hit) > 2 and isinstance(hit[2], int)):
                self.knowledge_counts[f.stem] = hit[2]
                continue
            n = 0
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        n += 1
                        if cap and n >= cap:
                            break
            self.knowledge_counts[f.stem] = n
            cache[key] = [st.st_size, st.st_mtime, n]
            changed = True
        self.stats["total_examples"] = sum(self.knowledge_counts.values())
        if changed:
            try:
                cache_path.write_text(json.dumps(cache), encoding="utf-8")
            except Exception:
                pass
    def classify_task(self, prompt):
        prompt_lower = prompt.lower(); scores = defaultdict(float)
        for keyword, cluster in TASK_ROUTES.items():
            c = prompt_lower.count(keyword)
            if c: scores[cluster] += c * KNOWLEDGE_CLUSTERS.get(cluster, {}).get("priority", 1)
        for cl in scores: scores[cl] += self.stats["clusters_used"].get(cl, 0) * 0.01
        cluster = "general"
        if scores:
            cluster = max(scores, key=scores.get)
        else:
            ru_chars = sum(1 for c in prompt if '\u0400' <= c <= '\u04FF')
            if ru_chars > 3:
                cluster = "ru"
            elif any(c in prompt for c in "{}[]();=<>"):
                cluster = "code"
        return cluster
    def log_call(self, prompt, cluster, provider, latency_ms, success, tokens=0):
        self.stats["calls"] += 1
        self.stats["clusters_used"][cluster] = self.stats["clusters_used"].get(cluster, 0) + 1
        _append_call_log(prompt, cluster, provider, latency_ms, success, tokens)
        # ТОП-вопросов: считаем нормализованные запросы (ТОП-30)
        self.stats.setdefault("top_questions", {})
        q = " ".join(prompt.split())[:60].lower()
        if q:
            self.stats["top_questions"][q] = self.stats["top_questions"].get(q, 0) + 1
            # держим не более 30 ключей — отсекаем самый редкий
            if len(self.stats["top_questions"]) > 30:
                rare = min(self.stats["top_questions"], key=self.stats["top_questions"].get)
                self.stats["top_questions"].pop(rare, None)
        try:
            self._save_json(CORE / "stats.json", dict(self.stats))
        except Exception:
            pass
        return None
    def get_cluster_info(self):
        return {name: {**info, "examples": self.knowledge_counts.get(name, 0), "calls": self.stats["clusters_used"].get(name, 0)} for name, info in KNOWLEDGE_CLUSTERS.items()}
    def status(self):
        try:
            sys.path.insert(0, str(MIRRO_HOME))
            from scripts.providers import status as _pv_status
            prov = _pv_status()
        except Exception:
            prov = {}
        # статус отказоустойчивости: свежий ли бэкап, есть ли восстанавливаемые данные
        backup_info = {}
        try:
            bdir = MIRRO_HOME / "backups"
            if bdir.is_dir():
                dirs = [d for d in bdir.iterdir() if d.is_dir() and d.name.startswith("model_")]
                if dirs:
                    latest = max(dirs, key=lambda d: d.name)
                    backup_info = {"latest": latest.name, "dirs": len(dirs)}
        except Exception:
            backup_info = {}
        # статус модерации: сколько раз фильтр отклонил запрос/ответ (из журнала)
        moderation = {"rejected_input": 0, "rejected_output": 0}
        try:
            mlog = MIRRO_HOME / "data" / "moderation_log.jsonl"
            if mlog.is_file():
                for line in mlog.read_text("utf-8", errors="replace").splitlines()[-400:]:
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    if rec.get("kind") == "input":
                        moderation["rejected_input"] = moderation.get("rejected_input", 0) + 1
                    elif rec.get("kind") == "output":
                        moderation["rejected_output"] = moderation.get("rejected_output", 0) + 1
        except Exception:
            moderation = {"rejected_input": 0, "rejected_output": 0}
        return {"name": "Mirro", "version": "0.3", "total_calls": self.stats["calls"], "total_examples": self.stats["total_examples"], "providers": prov, "clusters": self.get_cluster_info(), "backup": backup_info, "moderation": moderation, "api": f"http://{HOST}:{PORT}/v1/chat/completions"}
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


def _combinatoric_pair():
    """Самая стабильная комбинаторная пара концептов из живого графа.
    Один return: tuple (pair|None, chaos|999.0)."""
    pair = None
    chaos = 999.0
    try:
        from algos.knowledge_graph import kg as _kg
        from algos.combinatorics import evaluate_best_logical_tree
        if _kg.nodes:
            avail = sorted(_kg.nodes)[:40]
            pair, chaos = evaluate_best_logical_tree(_kg, avail, chaos_target=0.5)
    except Exception:
        pair, chaos = None, 999.0
    return pair, chaos


def _quantum_context_note():
    """Квантово-комбинаторная сноска для reasoning_content ответа.

    Собирает из реальных модулей: физический PINN-loss графа, число узлов в
    квантовой суперпозиции, среднюю размерность понимания и самую стабильную
    комбинаторную пару концептов. Тихий — на ошибке возвращает пустую строку.
    Единственный return: str."""
    note = ""
    try:
        from algos.knowledge_graph import kg as _kg
        from algos.zero_dimensional import dimension_of_understanding as _dimen
        from algos.quantum_graph import init_quantum_states
        from algos.neural_electric import calculate_physics_loss
        if _kg.nodes:
            pinn = calculate_physics_loss(_kg, 0.55)
            dim = _dimen(_kg)
            sup = len(init_quantum_states(_kg).states)
            pair, chaos = _combinatoric_pair()
            pair_txt = (pair[0] + "↔" + pair[1]) if pair else "нет устойчивой пары"
            note = (f"PINN Loss: {pinn:.4f}; суперпозиция: {sup} концептов; "
                    f"размерность понимания: {dim}/3; комбинаторный путь: {pair_txt} "
                    f"(хаос {chaos:.4f}).")
    except Exception:
        note = ""
    return note

def try_create_encrypted_backup(graph, backup_dir=None):
    """Сериализует граф, шифрует десятичным поточным шифром и сохраняет слепок.

    backup_dir — путь к папке бэкапов (по умолчанию MIRRO_HOME/backups/).
    Ключ берётся из keys/secret.key (генерируется, если нет). Файл: backup_<ts>.
    Единственный return: dict {status, path}."""
    status = {"status": "error", "path": ""}
    try:
        import pickle as _pkl, time as _time
        from scripts.cipher import try_load_secure_key, transform_bytes_to_cipher
        from algos import knowledge_graph
        key = try_load_secure_key()
        # сериализуем ПОЛНЫЙ граф как dict {nodes, edges, experience} — согласовано
        # с KnowledgeGraph.save(), чтобы restore мог восстановить всё без потерь.
        if hasattr(graph, "nodes") and hasattr(graph, "edges"):
            snapshot = {
                "nodes": graph.nodes,
                "edges": graph.edges,
                "experience": getattr(graph, "experience", []),
            }
        else:
            snapshot = graph
        raw = _pkl.dumps(snapshot)
        enc = transform_bytes_to_cipher(raw, key, decrypt=False)
        bdir = backup_dir or (MIRRO_HOME / "backups")
        if isinstance(bdir, str):
            bdir = Path(bdir)
        bdir.mkdir(parents=True, exist_ok=True)
        ts = int(_time.time())
        fpath = bdir / f"backup_{ts}.mirro.enc"
        Path(fpath).write_bytes(enc)
        status = {"status": "success", "path": str(fpath)}
    except Exception as e:
        status = {"status": "error", "message": str(e)}
    return status


def try_optimize_memory_buffer(graph):
    """Свёртывающая кристаллизация опыта graph.experience (экономия RAM).
    Возвращает строку-отчёт. Один return: str."""
    before = len(getattr(graph, "experience", None) or [])
    after = before
    try:
        from algos.memory_crystallization import try_crystallize_experience
        after = try_crystallize_experience(graph, similarity_threshold=0.92)
    except Exception:
        after = before
    return f"Память оптимизирована: {before} -> {after} паттернов (кристаллов)."


def autonomous_learning_loop(interval_sec=3600):
    import threading
    def _loop():
        while True:
            try:
                algo = _grab_algo(); n = algo.autonomous_learn(cycles=30)
                print(f"  [автообучение] усвоила {n} примеров")
                # если база опыта обновилась — сначала кристаллизуем опыт (экономия RAM),
                # затем делаем зашифрованный слепок графа
                if n and n > 0:
                    try:
                        opt = try_optimize_memory_buffer(algo)
                        print(f"  [автообучение] {opt}")
                    except Exception:
                        pass
                    try:
                        bres = try_create_encrypted_backup(algo)
                        if bres.get("status") == "success":
                            print(f"  [автообучение] зашифрованный бэкап: {bres['path']}")
                    except Exception:
                        pass
                try:
                    # Не затирать trainer-метрики (trainer_cycles/accuracy/clusters):
                    # читаем текущее состояние и обновляем только авто-поля.
                    prev = {}
                    if MODEL_STATE_FILE.exists():
                        try: prev = json.loads(MODEL_STATE_FILE.read_text("utf-8"))
                        except Exception: prev = {}
                    merged = dict(prev)
                    merged["perceptron_weights"] = algo.perceptron_weights
                    merged["perceptron_bias"] = algo.perceptron_bias
                    merged["perceptron_trained"] = algo.perceptron_trained
                    merged["auto_learned"] = (prev.get("auto_learned") or 0) + (n or 0)
                    merged["updated"] = _utc_now_iso()
                    MODEL_STATE_FILE.write_text(json.dumps(merged, ensure_ascii=False), "utf-8")
                except: pass
                # периодический самоконтроль: прогон QA-пар (вопрос → ответ)
                # ловит «рваные» ответы и регрессии, пишет историю в data/qa_report.jsonl
                try:
                    import subprocess as _sp, sys as _sys
                    _sp.run([_sys.executable, str(MIRRO_HOME / "scripts" / "run_qa.py")],
                            timeout=180, capture_output=True)
                    print("  [автообучение] QA-самоконтроль выполнен")
                except Exception as _qae:
                    print(f"  [автообучение] QA-самоконтроль: {_qae}")
            except Exception as e: print(f"  [автообучение] ошибка: {e}")
            time.sleep(interval_sec)
    t = threading.Thread(target=_loop, daemon=True); t.start(); return t


def mindstream_loop(interval_sec=1800):
    """Фоновая «внутренняя речь»: Mirro сама, без вопроса, выбирает тему и
    размышляет над ней (пишет поток мыслей в data/mindstream/thoughts.jsonl)."""
    import threading
    def _loop():
        from algos.mindstream import mind
        while True:
            try:
                r = mind.think()
                if r.get("written"):
                    print(f"  [медитация] тема: {r.get('topic')!r} → {r.get('thought')[:90]}")
            except Exception as e:
                print(f"  [медитация] ошибка: {e}")
            time.sleep(interval_sec)
    t = threading.Thread(target=_loop, daemon=True); t.start(); return t

# ========== REASONING ENGINE ==========
# Чистая логика вынесена в scripts/reasoning_engine.py (легко тестировать без
# построения индекса в память). Здесь только аккуратный локальный импорт.
def _reasoning():
    sys.path.insert(0, str(MIRRO_HOME))
    from scripts.reasoning_engine import score_candidate, choose_best, _tokenize
    return score_candidate, choose_best, _tokenize

def _word_in(text, word):
    """Есть ли слово целиком: «пока» не должно ловиться внутри «покажи».
    Один return: bool."""
    return bool(_re.search(r"(?<![а-яёa-z])" + _re.escape(word) + r"(?![а-яёa-z])", text))


def try_greetings(query):
    q = query.lower().strip()
    ans = None
    if len(q) <= 40 and "спасибо" in q:
        ans = "Пожалуйста! Рада помочь."
    elif len(q) <= 40 and any(g in q for g in ["привет","здравств","добрый"]):
        ans = "Привет! Я Mirro. Спрашивай что угодно — отвечу из своих знаний или найду в интернете."
    elif len(q) <= 40 and q.strip(" !.?,") in ("hi", "hello", "hey", "good morning", "good evening"):
        ans = "Привет! Я Mirro. Спрашивай что угодно — отвечу из своих знаний или найду в интернете."
    elif len(q) <= 40 and any(g in q for g in ["как дела","как ты","как жизнь","как у тебя","как настроение","как твои"]):
        ans = "Привет! У меня всё хорошо, я постоянно учусь и становлюсь умнее. А у тебя как дела?"
    elif len(q) <= 40 and (q == "2+2"):
        ans = "4"
    return ans

def try_learn(query):
    q = query.lower().strip()
    # если речь про импульс/электричество по графу — это задача neural_electric, не try_learn
    is_graph_question = any(t in q for t in ["импульс", "электричеств"])
    answer = None
    if not is_graph_question:
        wants_learn = any(t in q for t in ["научи", "обучи", "запомн", "запиши", "сохрани это",
                                           "добавь в базу", "выучи", "запомни что"])
        if wants_learn:
            answer = ("Я учусь! Чтобы научить меня:\n1. Напиши вопрос и правильный ответ\n2. Отметь ответ\n\n"
                      "Или просто задай вопрос — я найду ответ в базе или в интернете.")
    return answer

def try_algos_think(query):
    ans = None
    try:
        from algos.think import think as mirro_think
        thought = mirro_think(query)
        if thought and thought.get("answer") is not None and thought.get("category") != "unknown":
            ans = thought.get("explanation") or str(thought.get("answer"))
    except Exception:
        ans = None
    return ans

def try_humor(query):
    q = query.lower().strip()
    ans = None
    try:
        from algos.humor import shutka, sarkazm, ya_ne_znau_chto_khotet, o_udache_i_uspehe
        from algos.reasoning import think_about_thinking, citata_bosovy
        if "шутк" in q or "смеш" in q or "анекдот" in q or "юмор" in q:
            ans = shutka(q)
        elif "сарказм" in q or "ирони" in q:
            ans = sarkazm()
        elif "ничего не делать" in q or "ничегонеделание" in q or "лень" in q:
            ans = "ЕСЛИ <лень> ТО <ничего не делать>. Алгоритм: НАЧАЛО → ничего не делать → КОНЕЦ."
        elif "хочу" in q and "не знаю" in q:
            ans = ya_ne_znau_chto_khotet()
        elif "удач" in q or "успех" in q or "успеха" in q or "веришь" in q or "веришь ли" in q:
            ans = o_udache_i_uspehe()
        elif "босов" in q or "блок-схем" in q or "схема мышления" in q:
            _, steps = think_about_thinking(q)
            ans = "\n".join(steps[:6])
        elif "цитат" in q and ("босов" in q or "учебник" in q):
            author, text = citata_bosovy()
            ans = f"{author}: «{text}»"
    except Exception:
        ans = None
    return ans

def try_creative(query):
    """Креативные запросы (стихи, рассказы, загадки) — лёгкая генерация.

    Раньше такие запросы уходили в TF-IDF-поиск и возвращали нерелевантные
    фрагменты базы (пример: «Придумай загадку» -> про код). Перехватываем
    их и генерируем короткий живой ответ на месте.
    """
    q = query.lower().strip()
    topics = {
        ("стихотво", "стих ", "стихи", "стишок", "поэм", "рисуешь"): _gen_poem,
        ("рассказ", "сочин", "историю", "истори", "мини-рассказ"): _gen_story,
        ("загадк", "загадай"): _gen_riddle,
        ("тост", "поздрав", "тостик"): _gen_toast,
    }
    ans = None
    for keys, fn in topics.items():
        if any(k in q for k in keys):
            ans = fn(q)
            break
    return ans

def _gen_poem(query):
    topic = "зиму" if any(w in query.lower() for w in ["зим", "снег", "мороз"]) else \
            "осень" if any(w in query.lower() for w in ["осен", "листья"]) else \
            "весну" if any(w in query.lower() for w in ["весн", "цвет"]) else \
            "ночь" if any(w in query.lower() for w in ["ноч", "лун", "звезд"]) else "мир"
    # Несколько вариантов строк на тему — Mirro не должна повторять
    # одно и то же стихотворение на одинаковый запрос.
    variants = {
        "зиму": [
            ["Зима укрыла белым снегом крыши,", "Мороз рисует на окне узор,", "И день стал тише, вечер — даже тише,", "Снежинки падают наперекор."],
            ["Зима вступила в город на цыпочках,", "Одела в мех дома и провода,", "И всё затихло в белых меховых клочьях,", "А снег всё сыплет — не скупая никогда."],
        ],
        "осень": [
            ["Осень кружит золотые листья,", "Дождик тихо стучит в окно,", "Небо хмурится, ветер свищет,", "Но в душе всё тепло и светло."],
            ["Осень крадётся вдоль мокрых аллей,", "Сбрасывает с крон последний золотой,", "И меж карнизов и фонарных теней", "Шепчет, что скоро придёт покой."],
        ],
        "весну": [
            ["Весна приходит каплями с крыши,", "Ручьи поют, сосульки тают,", "Земля проснулась и всё ближе", "Тот день, когда цветы расцветают."],
            ["Весна стучится в каждое окно,", "Светлеет день, длиннее час рассвета,", "И даже серый камень всё равно", "Готов к зелёному и тёплому ответить."],
        ],
        "ночь": [
            ["Ночь раскрывает звёздные крылья,", "Луна в облаках плывёт,", "Спят города, спят дома и углы,", "И мудрый кто-то стихи читает."],
            ["Ночь опускается тихо на плечи,", "Зажигает далёкий свет,", "И под покровом один только вечер", "Шепчет спокойное «нет»."],
        ],
        "мир": [
            ["В этом мире много чудес,", "Каждый день — как маленькая глава,", "Уходит тьма, звучит свет и лес,", "И начинается новая глава."],
            ["Мир не стоит на месте — он дышит,", "Вращается, светится, ткёт,", "И каждому, кто это услышит,", "Внутри наступает радость его."],
        ],
    }[topic]
    import random as _rnd
    # Не повторять предыдущий вариант подряд (храним последний в модуле),
    # чтобы два одинаковых запроса гарантированно давали разные стихи.
    key = f"poem_{topic}"
    avail = [v for v in variants if v != _LAST_POEM.get(key)]
    lines = _rnd.choice(avail) if avail else _rnd.choice(variants)
    _LAST_POEM[key] = lines
    return "Напишу тебе так:\n" + "\n".join(lines)


_LAST_POEM = {}

def _gen_story(query):
    return ("Коротко придумаю так:\n"
            "Жил-был кот по имени Мирро. Каждый вечер он садился у окна и смотрел, "
            "как город зажигает огни. Однажды на подоконник приземлился светлячок и "
            "пригласил его посмотреть на мир с высоты. Так началось их маленькое "
            "приключение, полное тёплых крыш, добрых людей и вкусной рыбы.")

def _gen_riddle(query):
    return ("Вот тебе загадка:\n"
            "Не лает, не кусает, а в дом не пускает. Что это?\n"
            "… замок. Угадала? Я вся в предсказуемости.")

def _gen_toast(query):
    return ("Ну, наливай!\n"
            "За мир, в котором мы — не просто строки кода, а тёплый свет, "
            "за людей, которые рядом, и за удачу, которая любит смелых. Поднимем!")

def try_jarvis(query):
    """ДЖАРВИС-режим: короткий статусный ответ в его стиле."""
    ans = None
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.voice import try_jarvis as _try_jarvis
        ans = _try_jarvis(query)
    except Exception:
        ans = None
    return ans

_DIALOG_STOPWORDS = {
    "и", "в", "на", "с", "по", "за", "от", "до", "из", "у", "для", "о",
    "не", "ни", "все", "это", "как", "так", "что", "кто", "где", "когда",
    "ну", "во", "же", "бы", "а", "но", "или", "ещё", "про", "при", "просто",
    "расскажи", "напиши", "подробнее", "можно", "мне", "меня", "то", "ли",
    "the", "a", "an", "and", "of", "to", "in", "on", "for", "with",
}

def _tokenize_for_search(text):
    """Токенизация для оценки «есть ли своя тема» и обогащения контекстом."""
    return _re.findall(r"[а-яёa-z0-9]+", (text or "").lower())

_DIALOG_REPLIES = {
    "who": ("Я Mirro — эволюционная нейросеть знаний. Создана в России, живу полностью "
            "на твоём компьютере: у меня своя база примеров, TF-IDF и RAG-поиск, "
            "перцептрон, который я обучаю на твоих оценках, и доступ к веб-поиску."),
    "program": ("Я — компьютерная программа: нейросеть, которая живёт на твоём ПК. "
                "То есть программа, но не «мёртвые команды», а обучающийся алгоритм: "
                "я отвечаю из своей базы знаний, ищу в интернете, учусь на твоих "
                "оценках и со временем становлюсь умнее."),
    "can": ("Что умею: отвечаю на вопросы из своей базы и интернета, считаю и решаю "
            "уравнения, пишу стихи, рассказы и загадки, помогаю по коду, налогам, "
            "фактам. Ещё учусь сама: коплю примеры и улучшаю свои веса. Спрашивай — "
            "что угодно."),
    "learn": ("Учусь каждый день: автономно перебираю свою базу, генерирую вопросы и "
             "проверяю, насколько хорошо отвечаю; запоминаю отклик на твои лайки и "
             "дизлайки, пере-игрываю их (replay buffer) и постепенно пополняю знания из "
             "открытых источников."),
    "howami": ("У меня всё хорошо! Я постоянно расту: сегодня в моей базе уже больше "
               "миллиона примеров, и я становлюсь умнее с каждым запуском."),
    "status": ("Всё в порядке: сервер работает, знания на месте. Спрашивай, что "
               "интересно — отвечу."),
    "language": ("Конечно! Я отлично говорю по-русски — спрашивай на любом "
                 "русском можно. А если напишешь на другом языке — тоже постараюсь "
                 "понять и отвечу."),
    "news": ("Недавние обновления: я улучшила отбор ответов (стал смысловее, без "
             "случайных фрагментов), добавила поддержку разговоров — отвечаю на "
             "«что ты умеешь», «как учишься» и т.п., научилась вести диалог после "
             "первого сообщения и запоминать контекст. Технических новостей из мира "
             "не знаю — я офлайн-нейросеть, но могу найти актуальное в интернете, "
             "если спросишь конкретно."),
    "thanks": ("Пожалуйста! Рада помочь. Если захочешь ещё что-то — я здесь."),
    "bye": ("До встречи! Буду рада снова с тобой пообщаться."),
    "quality": ("Понимаю, мой ответ мог не понравиться. Я ещё учусь и улучшаюсь — "
                "попробую ответить иначе и понятнее. Переформулируй вопрос по-другому, "
                "и я постараюсь дать более живой и точный ответ."),
    "not_answering": ("Справедливо, извиняюсь — отвечу прямо. Ты спрашивал(а) про меня: "
                      "я Mirro, локальная обучающаяся нейросеть. Живу на твоём ПК, у меня "
                      "своя база знаний и поиск, я учусь на твоих оценках. Задай вопрос "
                      "ещё раз — отвечу по существу."),
    "advice": ("Я могу дать направление, но решать тебе. Начни с малого: определись, "
               "что ближе — писать продукты, обслуживать системы или делать удобный "
               "интерфейс. Потом выбери один путь, пройди бесплатный курс по шагам и "
               "собери 2-3 своих проекта. Фриланс и работа в команде не исключают друг "
               "друга — можно пробовать. Главное — постоянная практика, я в этом сама "
               "разбираюсь, потому что каждый день учусь."),
    "about": ("Я Mirro — эволюционная нейросеть знаний, созданная в России. Работаю "
              "полностью локально на твоём компьютере: у меня своя база из миллионов "
              "примеров, TF-IDF и RAG-поиск, перцептрон на оценках и доступ к веб-поиску. "
              "Отвечаю на вопросы, помогаю по коду, считаю, пишу стихи — и каждый день "
              "учусь на твоих откликах."),
    "name": ("Меня зовут Mirro. Я эволюционная нейросеть знаний — отвечаю на вопросы, "
             "ищу информацию и обучаюсь, чтобы становиться умнее. Чем могу помочь?"),
    "help": ("Конечно, помогу! Расскажи, что нужно: найти факт, разобраться в коде или "
             "алгоритме, посчитать что-то, составить текст или разобраться в вопросе — "
             "спрашивай конкретнее, и я отвечу по сути."),
}

def _is_news_query(q):
    # «что нового?», «новости», «какие новости», «что произошло» и т.п. —
    # это разговорный вопрос, а НЕ технический запрос по «новостям» в софте.
    phrase_hit = any(w in q for w in ["что нового", "что новенького", "какие новости",
                                      "что происходит", "что произошло", "расскажи новости",
                                      "новости на сегодня", "есть что новое", "есть новое"])
    exact_hit = q.strip() in ("новости", "новость", "новостей", "что новое?", "что нового")
    return phrase_hit or exact_hit

def try_dialog(query):
    """Разговорные реплики, которые НЕ должны идти в TF-IDF поиск.

    Ключевая проблема: «Что ты умеешь?», «Как учишься?» и т.п. уходили в поиск
    и возвращали случайные фрагменты базы (напр. «Агата Кристи» на вопрос про
    алгоритмы). Перехватываем их здесь и отвечаем осмысленно.
    """
    q = query.lower().strip()
    ans = None
    if any(w in q for w in ["кто ты", "что ты такое", "ты кто", "представься", "твоё имя"]):
        ans = _DIALOG_REPLIES["who"]
    elif any(w in q for w in ["ты программа", "ты бот", "ты компьютерная программа",
                              "ты живая", "ты настоящая", "ты робот", "ты искусственный интеллект",
                              "ты нейросеть"]):
        ans = _DIALOG_REPLIES["program"]
    elif q.strip() in ("программа", "программу", "что такое программа"):
        ans = _DIALOG_REPLIES["program"]
    elif any(w in q for w in ["что ты умеешь", "что умеешь", "твои возможности", "на что способна"]):
        ans = _DIALOG_REPLIES["can"]
    elif any(w in q for w in ["как ты учишься", "как учишься", "как обучаешься", "как запоминаешь"]):
        ans = _DIALOG_REPLIES["learn"]
    elif any(w in q for w in ["как ты", "как твои дела", "как настроение", "ты в порядке"]):
        ans = _DIALOG_REPLIES["howami"]
    elif any(w in q for w in ["статус", "всё ли в порядке", "ты работаешь"]):
        ans = _DIALOG_REPLIES["status"]
    elif _is_news_query(q):
        ans = _DIALOG_REPLIES["news"]
    elif any(w in q for w in ["ответишь на русском", "говори по-русски", "по русски",
                              "на русском", "русский язык", "по-русски"]):
        ans = _DIALOG_REPLIES["language"]
    elif any(w in q for w in ["меня не устраивает твой ответ", "ответ как человек",
                              "как бы ответил человек", "ответь нормально", "ответь по-человечески",
                              "ответь как человек", "не то", "не то ответил", "плохой ответ", "ерунда", "не понравился твой ответ"]):
        ans = _DIALOG_REPLIES["quality"]
    elif any(w in q for w in ["не отвечаешь на вопрос", "не ответил", "не отвечаешь",
                              "не отвечаешь про себя", "игнорируешь мой вопрос",
                              "отвечай на вопрос", "не отвечаешь на мой вопрос"]):
        ans = _DIALOG_REPLIES["not_answering"]
    elif any(w in q for w in ["стоит ли", "какой выбрать", "что выбрать", "подскажи как",
                              "посоветуй", "совет по", "как начать", "с чего начать",
                              "лучше для", "чем заниматься", "идти в разработку",
                              "работать на себя", "фриланс или", "учиться на"]):
        ans = _DIALOG_REPLIES["advice"]
    elif q.startswith("какой ") and "лучше" in q:
        ans = _DIALOG_REPLIES["advice"]
    elif any(w in q for w in ["спасибо", "благодарю", "спс"]):
        ans = _DIALOG_REPLIES["thanks"]
    elif any(w in q for w in ["расскажи о себе", "расскажи о тебе", "кто ты такой"]):
        ans = _DIALOG_REPLIES["about"]
    elif any(w in q for w in ["как тебя зовут", "какое у тебя имя", "твоё имя",
                              "как тебя называть"]):
        ans = _DIALOG_REPLIES["name"]
    elif any(w in q for w in ["помоги мне", "помоги", "поможешь", "подскажешь",
                              "нужна помощь"]):
        ans = _DIALOG_REPLIES["help"]
    elif (any(w in q for w in ["до свидания", "до встречи", "прощай"])
          or _word_in(q, "пока")):
        ans = _DIALOG_REPLIES["bye"]
    return ans

def try_tfidf(query, cluster):
    ans = []
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.algorithms import algo
        ans = algo.search_tfidf(query, top_n=5)
    except Exception:
        ans = []
    return ans


def _semantic_expand(query):
    """Смысловое расширение запроса: ассоциированные термины из корпусной
    матрицы со-встречаемости (query_expansion) + близкие понятия графа.
    Один return: строка — исходный запрос + добавленные термины."""
    q = (query or "").strip()
    extra = []
    if not q:
        return q
    # 1) корпусные ассоциации (синонимы/со-встречаемые термины)
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.algorithms import algo
        extra += algo.query_expansion(q, top_terms=4)
    except Exception:
        extra = extra
    # 2) близкие понятия графа (смысловая схожесть окрестностей)
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from algos.knowledge_graph import kg as _kg
        for w in _tokenize_for_search(q)[:6]:
            close = _kg.closest_concepts(w, top_n=2, min_sim=0.05)
            extra += [c for c, _sim in close]
    except Exception:
        pass
    expanded = q
    if extra:
        seen = set(_tokenize_for_search(q))
        # не добавляем слишком короткие термины и ограничиваем 8 уникальных расширений
        candidates = []
        for t in extra:
            if t not in seen and len(t) >= 3:
                seen.add(t)
                if len(candidates) < 8:
                    candidates.append(t)
        add = " ".join(candidates)[:360]
        if add:
            expanded = (q + " " + add).strip()
    return expanded


def _asks_english_description(prompt):
    """Просьба «X по-английски»: корпус цепляется за слово «английский» и отвечает
    случайным абзацем («flesh по-английски» → про RESET). Один return: bool."""
    q = (prompt or "").lower()
    hit = False
    if "по-англ" in q:
        try:
            from algos.english_kb import _EN_KB
            tokens = {t.strip(".,!?;:'\"()") for t in q.replace("-", " ").split()}
            hit = any(isinstance(t, str) and t and t in tokens for t in _EN_KB)
        except Exception:
            hit = False
    return hit


def _search_best(prompt, cluster):
    """TF-IDF → RAG → выбор лучшего кандидата по кластеру.
    Пользуется семантическим реранком для кандидатов обоих источников.
    Единственный return: кортеж (best_answer, best_score, has_result)."""
    if _asks_english_description(prompt):
        # отдать ответ обработчику english: он знает тему, корпус — нет
        return None, 0.0, False
    q = _semantic_expand(prompt)
    results = try_tfidf(q, cluster)
    if not results:
        results = try_rag(q, cluster)
    # семантический реранк по охвату темы — улучшает выбор и для RAG-кандидатов
    results = _semantic_rerank_results(prompt, results)
    _, choose_best, _ = _reasoning()
    best_answer, best_score, _reason = choose_best(prompt, results, preferred=cluster)
    has_result = best_answer is not None and best_score > 1.0
    return best_answer, best_score, has_result


def _semantic_rerank_results(query, results):
    """Перезачоняет кандидатов по покрытию темы вопроса (когда доступен algo).
    results: list ((inst, out, cl), score). Возвращает тот же формат, отсортированный.
    Тихий: при любой ошибке возвращает исходный список. Один return: list."""
    out = results
    try:
        from scripts.algorithms import algo
        if not results:
            return out
        q_tokens = set(algo.tokenize(query))
        if not q_tokens:
            return out
        scored = []
        for (inst, ans, cl), sc in results:
            if not ans:
                continue
            a_set = set(algo.tokenize(ans))
            cov = len(q_tokens & a_set) / max(len(q_tokens), 1) if a_set else 0.0
            # мягкий реранк: 0.7 старый score + 0.3 покрытие темы
            combined = sc * 0.7 + cov * 3.0
            scored.append((combined, (inst, ans, cl), sc))
        scored.sort(key=lambda x: -x[0])
        out = [(item, sc) for _c, item, sc in scored]
    except Exception:
        out = results
    return out

def _rag_worthy(query):
    """Есть ли в запросе слово, по которому вообще стоит искать в корпусе.
    Короткие вопросы вида «что такое иит» давали в RAG случайные примеры.
    Один return: bool."""
    words = [word for word in _re.findall(r"[а-яёa-z]+", (query or "").lower())
             if len(word) >= 4 and word not in
             ("что", "такое", "это", "как", "такой", "такая", "зачем", "почему", "чем")]
    return bool(words)


def try_rag(query, cluster):
    ans = []
    if not _rag_worthy(query):
        return ans
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.rag import rag
        # сквозной квантово-комбинаторный контур влияет на выбор дисковых сегментов:
        # если комбинаторное ядро нашло стабильную пару концептов — направляем поиск.
        pair, _chaos = _combinatoric_pair()
        if pair:
            rr = rag.run_quantum_guided_rag(query, pair, top_k=3)
        else:
            rr = rag.search(query, top_segments=3, top_k=3)
        if rr:
            ans = [(("", rr[i][2], "rag"), rr[i][0]) for i in range(min(3, len(rr)))]
    except Exception:
        ans = []
    return ans

def try_web(query):
    ans = None
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.thinking import thinking
        result = thinking.web_search(query)
        if result.get("title") and result.get("summary"):
            ans = thinking.format_web_answer(query, result)
    except Exception:
        ans = None
    return ans

def _mentions_query(query, text):
    """Есть ли в ответе слова вопроса. Один return: bool."""
    words = [word for word in _tokenize_for_search(query) if len(word) >= 4]
    low = (text or "").lower()
    return any(word in low for word in words)


def _web_answer(query):
    """Веб-ответ, только если он по теме вопроса. Один return: str/None.

    Веб-источник иногда отдаёт совсем другое понятие (на «кварковый резонатор»
    приходил ответ про НДС). Такой ответ хуже честного молчания: без него
    цепочка идёт к базе и фолбэку.
    """
    answer = try_web(query)
    return answer if answer and _mentions_query(query, answer) else None


def try_provider(query, context=""):
    """Финальный фоллбэк: внешний ИИ-провайдер (DeepSeek и др.), если всё остальное не ответило.

    context — история диалога; провайдеру передаётся, чтобы он учитывал
    предыдущие реплики и не терял нить разговора.
    """
    ans = None
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.providers import fallback
        ans = fallback(query, system=context or None)
    except Exception:
        ans = None
    return ans


_COMPARE_STOP_ROOTS = {"отли", "похо", "сход", "обще", "чем", "межд", "сравн"}
_COMPARE_MARKERS = ("отлича", "в отличие", "разница", "различ", "тогда как",
                    "по сравнению", "оба", "общее", "общего", "как и", "так и")


def _word_roots(text):
    """Основы слов (первые 4 буквы) — чтобы сравнивать словоформы.
    Один return: set."""
    return {word[:4] for word in _re.findall(r"[а-яёa-z]{3,}", (text or "").lower())}


def _asks_compare(query):
    """Вопрос про сравнение двух понятий. Один return: bool.
    Метки ищем как слова: «превосходство» содержит «сходств», но это
    не вопрос «что общего»."""
    q = (query or "").lower()
    if "что общего" in q:
        return True
    return bool(_re.search(r"(?<![а-яёa-z])(похож|подоб|сходств|отлича|сравн)",
                           q))


def _concept_alias_words(query):
    """Слова имён и алиасов понятия из вопроса.

    Ответ вправе называть тему синонимом: на вопрос «что такое двоичный
    поиск» правильный ответ начинается с «Бинарный поиск — …», и гейт
    не должен считать это чужим ответом.
    """
    words = set()
    try:
        from algos import lookup
        concept = (lookup.find(query) or {}).get("concept") or {}
        names = list(concept.get("aliases") or ()) + [concept.get("name") or ""]
        for name in names:
            words.update(_re.findall(r"[а-яёa-z0-9]{3,}", str(name).lower()))
    except Exception:
        words = set()
    return words


def _needs_final_gate(query):
    """Нужен ли финальный контроль для вопроса о сравнении понятий.
    Один return: bool."""
    return _asks_compare(query)


def answer_looks_bad(query, answer):
    """True, если ответ мусорный — его нельзя отдавать пользователю.
    Один return: bool."""
    bad = False
    if not answer or len(answer) < 10:
        bad = True
    else:
        # Ответ — служебная ошибка / дамп трассировки / JSON-нуб — это не ответ
        _sl = (answer or "").lower()
        error_markers = ["traceback", "file \"", "syntaxerror", "internalerror",
                         "не удалось связаться", "[mirro]", "500 internal", "500 server",
                         # служебные метки графа и корпуса в ответ попадать не должны
                         "использует_понятие", "про_понятие", "_понятие", "(вес ",
                         "справочное об", "machine-learning", "связано_с", "связано с такое"]
        if any(m in _sl for m in error_markers):
            bad = True
        elif _re.search(r"\{['\"](content|error|choices)['\"]\s*:", _sl):
            bad = True  # сырой JSON вместо текста
        else:
            # Ответ похож на код (PHP/JS/C++/SQL) — а вопрос фактологический
            code_markers = ["<?php", "#include", "std::", "import ", "console.", "npm ", "function ", "=>",
                            # строки shell и конфигов — тоже не ответ на «что такое X»
                            "$ ", "sudo ", "curl ", "git push", "git commit", "docker run",
                            "location ", "include proxy", "def ", "SELECT "]
            code_hits = sum(1 for m in code_markers if m in answer)
            latin_words = len(_re.findall(r"[A-Za-z]{3,}", answer))
            cyr_words = len(_re.findall(r"[а-яёА-ЯЁ]{3,}", answer))
            # Английский абзац в ответ на русский вопрос — это чужой текст из
            # корпуса, а не ответ. Но английский вопрос вправе получить
            # английский ответ: правило смотрит на язык самого вопроса
            # явная просьба «по-английски»: английский ответ — то, что просили
            asks_english = "по-англ" in (query or "").lower()
            asks_russian = (len(_re.findall(r"[а-яёА-ЯЁ]{3,}", query or ""))
                            >= len(_re.findall(r"[A-Za-z]{3,}", query or "")))
            asks_russian = asks_russian and not asks_english
            if asks_russian and latin_words > cyr_words and latin_words >= 8:
                bad = True
            elif code_hits >= 2:
                bad = True
            else:
                # Вопрос вида «что такое X / кто такой X / как работает X» — ответ
                # должен содержать ключевые слова вопроса (иначе «как работает
                # внимание» отвечает случайной строкой про VPN)
                q = query.lower().strip()
                is_factual = any(p in q for p in ["что такое", "кто такой", "кто такая",
                                                  "что значит", "расскажи про",
                                                  "как работает", "как устроен",
                                                  "как устроена", "принцип работы",
                                                  "как происходит", "как действует"])
                # Сравнение двух понятий: ответ обязан говорить хоть об одном из них,
                # иначе это случайная строка из корпуса («что общего у кошка и собака»)
                is_compare = _asks_compare(q)
                if is_factual or is_compare:
                    q_words = set(_re.findall(r"[а-яёa-z0-9]{3,}", q))
                    a_words = set(_re.findall(r"[а-яёa-z0-9]{3,}", answer.lower()))
                    # Ответ может называть тему синонимом: «двоичный поиск» —
                    # «Бинарный поиск». Засчитываем только те имена понятия,
                    # которые в ответе действительно есть: иначе собственное
                    # имя вопроса само себя подтверждает и гейт пропускает
                    # чужой ответ («что такое нейросеть» → «Сегодня погода»)
                    a_words |= _concept_alias_words(query) & set(
                        _re.findall(r"[а-яёa-z0-9]{3,}", answer.lower()))
                    # Ключевые слова вопроса: убираем стоп-слова
                    stop = {"что", "такое", "кто", "такой", "такая", "значит", "расскажи", "про", "это", "как", "для", "или",
                            "общего", "похож", "похожи", "похожа", "подобны", "подобна", "сходства", "сходство", "отличаются", "отлича", "чем"}
                    key = q_words - stop
                    # сверяем по основам, а не по словоформам: «дружбы» в вопросе
                    # и «дружба» в ответе — одно и то же слово
                    # сравниваем по трём первым буквам: «санки» и «сани» —
                    # одна тема, а «колесо» и «лес» по-прежнему разные слова.
                    # Латиницу приводим к кириллице: «ИИТ» и «IIT» — одно слово.
                    a_roots = {w[:3] for w in a_words}
                    try:
                        from algos.bilingual import transliterate as _translit
                        a_roots |= {_translit(w)[:3] for w in a_words}
                    except Exception:
                        a_roots = a_roots
                    # латинский термин не сверить с русским ответом надёжно:
                    # «hamming» и «Хэмминга» дают разные основы, и верный ответ
                    # бракуется. Для таких вопросов проверку пропускаем
                    latin_key = key and all(
                        not any("а" <= char <= "я" or char == "ё" for char in word)
                        for word in key)
                    if key and not latin_key and not {w[:3] for w in key} & a_roots:
                        bad = True  # ответ вообще не про это
                    # «семиотический трансформер»: два слова в вопросе, а ответ
                    # говорит только об одном, причём пропущено прилагательное-
                    # определитель. Значит, спрашивали не про то, что в базе.
                    if (not bad and is_factual and len(key) >= 2
                            and len({w[:3] for w in key} & a_roots) == 1):
                        _qual = [w for w in key if w[:3] not in a_roots]
                        # «двоичный поиск» → «Бинарный поиск»: пропущенное
                        # слово — другое имя того же понятия, и ответ его
                        # называет. Это не чужой ответ.
                        _alias = _concept_alias_words(query)
                        _alias_seen = bool(
                            _alias & set(_re.findall(r"[а-яёa-z0-9]{3,}",
                                                     answer.lower())))
                        _covered = _alias_seen and all(w in _alias for w in _qual)
                        if any(len(w) >= 6 and w.endswith(
                                ("ий", "ый", "ая", "ое", "ые", "ой")) for w in _qual) \
                                and not _covered:
                            bad = True
                # Сравнение: ответ обязан назвать оба понятия и сравнивать их,
                # иначе это просто текст, где встретилось одно из слов
                if not bad and is_compare:
                    asked = [w for w in _re.findall(r"[а-яёa-z]{4,}", q)
                             if w[:4] not in _COMPARE_STOP_ROOTS]
                    roots = _word_roots(answer)
                    if any(w[:4] not in roots for w in asked[:3]):
                        bad = True
                    elif not any(marker in answer.lower() for marker in _COMPARE_MARKERS):
                        bad = True
                    # «красный флаг»: длинный ответ почти без значащих слов
                    if not bad and a_words and len(a_words) < 2:
                        bad = True
                # «почему/зачем» требует причинного ответа, а не описания картинки
                is_causal = q.startswith("почему") or q.startswith("зачем") or "почему" in q[:12]
                if not bad and is_causal:
                    causal_markers = ("потому", "поэтому", "из-за", "так как", "причин",
                                      "обуслов", "следствие", "рассеив", "приводит к", "ведёт к")
                    if not any(marker in answer.lower() for marker in causal_markers):
                        bad = True
                # самопроверка: тавтология / «вода» — ответ почти целиком повторяет вопрос
                if not bad:
                    q_tokens = _re.findall(r"[а-яёa-z]{3,}", q.lower())
                    a_tokens = _re.findall(r"[а-яёa-z]{3,}", answer.lower())
                    if q_tokens and a_tokens:
                        q_set = set(q_tokens)
                        a_set = set(a_tokens)
                        overlap = len(q_set & a_set)
                        if len(q_set) >= 2 and overlap >= 0.7 * len(q_set) and len(a_set) <= len(q_set) + 1:
                            bad = True  # ответ буквально пересказывает вопрос, новой инфы нет
                # ответ — одно и то же слово много раз («дадада…» / «нейроннейрон»)
                if not bad and a_tokens and len(set(a_tokens)) == 1 and len(a_tokens) >= 4:
                    bad = True
                # ответ — почти без гласных (нечитаемый «жздрфт»)
                if not bad and answer:
                    letters = [c for c in answer.lower() if 'а' <= c <= 'я' or c == 'ё']
                    vowels = [c for c in letters if c in "аеёиоуыэюя"]
                    if letters and len(vowels) / max(len(letters), 1) < 0.12 and len(letters) >= 8:
                        bad = True
                # длинный ответ без единого предложения/точки
                if not bad and len(answer) > 200 and not _re.search(r"[.!?]", answer):
                    bad = True
    return bad


def _provider_help_hint():
    """Подсказка, когда внешний провайдер недоступен (нет ключа)."""
    hint = (" Подсказка: чтобы я отвечала на такие вопросы, добавь ключ DeepSeek. "
            "Положить его сюда: core/providers_secret.json "
            '(формат {"deepseek": "sk-..."}) или задать переменную DEEPSEEK_API_KEY.)')
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.providers import status as _pv_status
        if any(_pv_status().values()):
            hint = ""  # провайдер настроен — не морочим голову
    except Exception:
        hint = hint
    return hint


def _voice(raw, query, strategy="base"):
    """Обернуть сырой ответ в голос Mirro (свои слова, характер)."""
    ans = raw
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.voice import speak
        ans = speak(raw, query, strategy)
    except Exception:
        ans = raw
    return ans


def try_stylize_generated_output(raw_text, chemistry=None):
    """Стилизует итоговый текст под текущий био-темперамент графа.
    chemistry — уровни нейромедиаторов (по умолчанию из neuromodulators).
    Возвращает (stylized_text, temperament). Один return: tuple."""
    temper = "сбалансированный"
    text = raw_text or ""
    try:
        from algos.voice_temperament import determine_voice_temperament, try_apply_temperament_filters
        chem = chemistry
        if chem is None:
            from algos.neuromodulators import nm as _nm
            chem = getattr(_nm, "level", {})
        temper = determine_voice_temperament(chem)
        filtered = try_apply_temperament_filters(text.split(" "), temper)
        styled = " ".join(filtered)
        if styled and len(styled) >= 20:
            text = styled
    except Exception:
        text = raw_text or ""
    return text, temper


def try_bosova_engine(prompt):
    """Выполнимые алгоритмы по правилам Босовой: арифметика по конструкциям
    ЕСЛИ/ТО/ЦИКЛ ПОКА, схемы мышления, тройственное рассуждение «нейрон-нигде».
    Возвращает готовый ответ или None, если вопрос не подходит."""
    ans = None
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from algos.bosova_engine import применить
        res = применить(prompt)
        if res:
            ans = res["answer"]
    except Exception:
        ans = None
    return ans


def _bridge_knows(prompt):
    """Знает ли русский мост определение для этого вопроса. Один return: bool."""
    known = False
    # точная глосса важнее моста: иначе «машинное обучение» отвечало про машину
    try:
        from algos.module_knowledge import _precise_topic
        if _precise_topic(prompt):
            return False
    except Exception:
        pass
    try:
        from algos import ru_bridge
        found = ru_bridge.bridge(prompt)
        content = str((found or {}).get("content") or "")
        # английский абзац из корпуса — не ответ моста
        cyr = len(_re.findall(r"[а-яёА-ЯЁ]", content))
        lat = len(_re.findall(r"[A-Za-z]", content))
        known = bool(content) and cyr > lat
    except Exception:
        known = False
    return known


def _unknown_compound(prompt):
    """Сложное слово через дефис, которого нет в базе: «хеш-функция».

    Обработчики ниже ищут тему по частям и отвечают про «функцию» вообще,
    хотя спрашивали не о ней. Лучше честно уйти в запасную цепочку.
    """
    low = (prompt or "").lower()
    if "-" not in low:
        return None
    if not any(marker in low for marker in ("что такое", "что значит", "what is",
                                            "определение", "означает")):
        return None
    found = None
    try:
        from algos import lookup
        for word in _re.findall(r"[а-яёa-z]{3,}(?:-[а-яёa-z]{3,})+", low):
            if lookup.find(word) is None:
                found = word
                break
    except Exception:
        found = None
    return found


def _try_direct_handlers(prompt):
    """Перебирает быстрые стратегии (приветствие, обучение, мышление, юмор,
    творчество, Джарвис, диалог, босовские алгоритмы) и возвращает первый
    подошедший ответ. Единственный return: dict-ответ или None."""
    # Ленивые импорты новых граф/память/вывод-модулей (как принято в этом файле)
    import sys as _sys
    if str(MIRRO_HOME) not in _sys.path:
        _sys.path.insert(0, str(MIRRO_HOME))
    def try_knowledge_graph(q):
        ans = None
        try:
            from algos.knowledge_graph import try_knowledge_graph as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_graph_infer(q):
        ans = None
        try:
            from algos.graph_infer import try_graph_infer as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_dialogue_memory(q):
        ans = None
        try:
            from algos.dialogue_memory import try_dialogue_memory as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_zero_dim(q):
        ans = None
        try:
            from algos.zero_dimensional import try_zero_dim as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_metacognition(q):
        ans = None
        try:
            from algos.mindstream import try_metacognition as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_growth(q):
        ans = None
        try:
            from algos.zero_dimensional import try_growth as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_neuromod(q):
        ans = None
        try:
            from algos.neuromodulators import try_neuromod as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_enrich(q):
        ans = None
        try:
            from algos.knowledge_graph import try_enrich as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_definition(q):
        ans = None
        try:
            from algos.module_knowledge import try_definition as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans

    def try_concept_special(q):
        ans = None
        try:
            from algos.plan_router import answer_special as _special
            ans = _special(q)
        except Exception:
            ans = None
        return ans

    def try_concept(q):
        ans = None
        try:
            from algos.plan_router import answer_text as _router
            from algos.neuro_answer import answer_by_plan as _plan, answer as _direct
            ans = _router(q) or _plan(q) or _direct(q)
        except Exception:
            ans = None
        return ans

    def try_full_explanation(q):
        ans = None
        try:
            from algos.knowledge_graph import try_full_explanation as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_what_links(q):
        ans = None
        try:
            from algos.knowledge_graph import try_what_links as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_similar(q):
        ans = None
        try:
            from algos.knowledge_graph import try_similar as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_relation(q):
        ans = None
        try:
            from algos.knowledge_graph import try_relation as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_why(q):
        ans = None
        try:
            from algos.knowledge_graph import try_why as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_function_knowledge(q):
        ans = None
        try:
            from algos.module_knowledge import try_function_knowledge as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_evo(q):
        ans = None
        try:
            from algos.evolve import try_evolve as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_quantum_graph(q):
        ans = None
        # точная глосса важнее отчёта о состояниях: «что такое квантовая
        # запутанность» — определение, а не «0 узлов в суперпозиции»
        try:
            from algos.module_knowledge import _precise_topic, try_definition
            if _precise_topic(q):
                ans = try_definition(q)
        except Exception:
            ans = None
        if ans:
            return ans
        try:
            from algos.quantum_graph import try_quantum as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_neural_elec(q):
        ans = None
        try:
            from algos.neural_electric import try_neural_electric as _f
            from algos.knowledge_graph import kg as _kg
            ans = _f(q, kg=_kg)
            # если был запрос на обучение — сразу сохраняем изменённые веса графа
            if ans and any(w in q.lower() for w in ["обуч", "выучи", "запомн", "укрепи"]):
                try:
                    _kg.save(MODELS / "knowledge_graph.pkl")
                except Exception:
                    pass
        except Exception:
            ans = None
        return ans
    def try_user_profile(q):
        ans = None
        try:
            from algos.user_profile import try_user_profile as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_english(q):
        ans = None
        try:
            from algos.english_kb import try_english as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_bilingual(q):
        ans = None
        try:
            from algos.bilingual import try_bilingual as _f
            ans = _f(q)
        except Exception:
            ans = None
        return ans
    def try_router(q):
        ans = None
        try:
            from algos.answer_router import choose as _choose
            found = _choose(q, threshold=0.7)
            ans = found["content"] if found else None
        except Exception:
            ans = None
        return ans
    def try_empathy(q):
        ans = None
        try:
            from algos.empathy import observe
            observe(q)  # молча обновляем настроение диалога
        except Exception:
            pass
        return ans
    def try_steps(q):
        ans = None
        try:
            from algos.reasoning import list_schemes
            ql = q.lower()
            wants_steps = any(w in ql for w in ("по шагам", "пошагово", "что мне делать",
                                                "как сделать", "с чего начать", "составь план",
                                                "разбей на шаги", "поэтапно"))
            if wants_steps:
                # собираем пошаговый план: применяем шаги к КОНКРЕТНЫМ данным вопроса,
                # а не показываем абстракцию. Из вопроса вытаскиваем тему и элементы.
                import re as _re_s
                words = [w for w in _re_s.findall(r"[а-яёa-z]{4,}", ql)
                         if w not in ("чтобы", "как", "что", "это", "мне", "делать",
                                      "сделать", "начать", "шаги", "план", "можно",
                                      "нужно", "составь", "объясни", "разбей", "поэтапно")]
                topic = "этой задаче"
                if words:
                    topic = words[-1]
                # ищем числа/факты, чтобы шаги ссылались на реальные данные
                nums = _re_s.findall(r"\d+[,\s]?\d*", ql)
                data_note = ""
                if nums:
                    data_note = f" (вижу данные: {', '.join(n.strip() for n in nums[:3])})"
                then_steps = [
                    f"Шаг 1. Возьми тему «{topic}»{data_note} — исходные данные на руках.",
                    "Шаг 2. Разбей на части: главное действие и подготовка к нему.",
                    "Шаг 3. Выполни последовательно: сделай первый шаг, затем следующий.",
                    "Шаг 4. Проверь: сходится ли результат с тем, что просили.",
                    f"Шаг 5. Итог по «{topic}»: зафиксируй ответ и что делать дальше.",
                ]
                ans = "Сделаю и применю к твоему вопросу:\n" + "\n".join(then_steps)
        except Exception:
            ans = None
        return ans
    handlers = [
        ("greeting", try_greetings),
        ("learn", try_learn),
        ("think", try_algos_think),
        ("humor", try_humor),
        ("creative", try_creative),
        ("direct", try_jarvis),
        ("dialog", try_dialog),
        # сравнение, связи, причина, подсчёт и статистика — до общего определения,
        # иначе ответ на любое упоминание темы съедает их
        ("concept_special", try_concept_special),
        # определение раньше роутера: если русская база знает само слово, это точнее
        # ответа по английской теме через синоним («связь» → bond → «узы»)
        ("definition", try_definition),
        # роутер выше понятий: он умеет сравнивать два понятия, а обработчик
        # одного понятия на такой вопрос отвечает половиной ответа
        ("router", try_router),
        ("concept", try_concept),
        # английский ответ — запасной: если база знает тему, она отвечает
        # по-русски раньше, чем сработает «я обучен в основном по-русски»
        ("english", try_english),
        ("relation", try_relation),
        ("why", try_why),
        ("steps", try_steps),
        ("algo", try_bosova_engine),
        ("ai_history", try_ai_history),
        ("bilingual", try_bilingual),
        ("func_kb", try_function_knowledge),
        ("knowledge_graph", try_knowledge_graph),
        ("graph_infer", try_graph_infer),
        ("full_explanation", try_full_explanation),
        ("enrich", try_enrich),
        ("what_links", try_what_links),
        ("similar", try_similar),
        ("metacognition", try_metacognition),
        ("evolve", try_evo),
        ("quantum", try_quantum_graph),
        ("dialogue_memory", try_dialogue_memory),
        ("zero_dim", try_zero_dim),
        ("growth", try_growth),
        ("neuromod", try_neuromod),
        ("neural_elec", try_neural_elec),
        ("user_profile", try_user_profile),
        ("empathy_observe", try_empathy),
    ]
    result = None
    # «что такое хеш-функция»: слова-части в базе есть, а самого понятия нет —
    # тогда любой обработчик ответит про «функцию» и соврёт
    unknown = _unknown_compound(prompt)
    if unknown:
        return None
    for strategy, fn in handlers:
        try:
            msg = fn(prompt)
        except Exception:
            msg = None
        # ответ, который не отвечает на заданный вопрос («что такое колесо» →
        # «Лес — это…» из-за совпадения подстроки), пропускаем: пусть ответит
        # следующий обработчик, который знает толк в этом слове.
        # Гейт не применяем к «особым» ответам: сравнение, связи, причины и
        # подсчёт собираются по плану из базы, их формулировка не повторяет
        # вопрос и эвристика «ответ не про это» рубит их зря
        if msg is not None and strategy == "definition" and _bridge_knows(prompt):
            # словарь понятий из модулей иногда берёт не тот смысл («что такое
            # язык» → «Язык программирования Python»); русская база точнее
            msg = None
        # «что такое лень / удача / программа»: шутка, самоописание или диалог
        # перехватывают толкование слова, которое русская база знает точно
        _ql = (prompt or "").lower()
        _asks_word = any(p in _ql for p in ("что такое", "кто такой", "кто такая",
                                            "что значит"))
        if (msg is not None and _asks_word
                and strategy in ("humor", "dialog", "direct", "creative")
                and _bridge_knows(prompt)):
            msg = None
        if msg is not None and (strategy == "concept_special"
                               or not answer_looks_bad(prompt, msg)):
            result = {"content": msg, "strategy": strategy}
            break
    return result


def _split_multipart(prompt, max_parts=4):
    """Разбивает вопрос на несколько подзапросов, если он многочастный.
    Разделители: 'и как', 'и почему', 'и зачем', 'а ещё', 'а как', '; ',
    ' а также', перечисления. НЕ режет простые вопросы с одним глаголом.
    Возвращает список строк (1 элемент = вопрос простой). Один return: list."""
    q = (prompt or "").strip()
    if not q:
        return [q]
    q_low = q.lower()
    has_marker = any(m in q for m in (" а ещё ", " и одновременно ", " а также ", "; "))
    has_phrase = any(p in q_low for p in ("и как ", "и почему ", "и зачем ", "а как ", "а зачем "))
    # простой вопрос без маркеров и без повторённого вопросительного слова — не режем
    if not has_marker and not has_phrase:
        return [q]
    parts = []
    # явные разрывы на несколько вопросов
    sep_markers = [" а ещё ", " и одновременно ", " а также ", "; "]
    for marker in sep_markers:
        if marker in q:
            left, _, right = q.partition(marker)
            parts = [left.strip(), right.strip()]
            break
    if not parts:
        # «как X и как Y» / «почему A и почему B»
        for phrase in ("и как", "и почему", "и зачем", "а как", "а зачем"):
            if phrase in q_low:
                idx = q_low.find(phrase)
                parts = [q[:idx].strip(), q[idx + len("и "):].strip()]
                break
    if not parts:
        return [q]
    # фильтр: части должны быть непустыми и несли достаточный смысл
    clean = []
    for p in parts:
        wc = [w for w in _re.findall(r"[а-яёa-z]{3,}", p.lower())]
        if p and len(wc) >= 2:
            clean.append(p)
    if len(clean) >= 2 and len(clean) <= max_parts:
        return clean
    return [q]


def _enrich_followup(prompt, context):
    """Если реплика слишком короткая и без своей темы, обогащает её словами из
    истории диалога, чтобы поиск не ушёл в мусор. Также подхватывает «продолжение
    темы» (а это…, про это…, дальше…) из последней реплики. Единственный return: str."""
    q_words = set(_tokenize_for_search(prompt))
    content_words = {w for w in q_words if w not in _DIALOG_STOPWORDS}
    enriched = prompt
    continuation = any(w in prompt.lower() for w in ("это", "её", "его", "этих",
                                                  "дальше", "продолж", "ещё",
                                                  "а теперь", "и ещё", "такая же"))
    if (len(content_words) < 2 or continuation) and context:
        lines = [l for l in context.split("\n") if l.strip()]
        hist_words = set()
        # для связности многоходовых тем всегда берём слова из ПОСЛЕДНЕГО
        # вопроса Пользователя (предыдущая тема), а не только при короткой реплике
        user_lines = [l for l in lines if l.startswith("Пользователь:")]
        source = user_lines[-1] if user_lines else (lines[-1] if lines else "")
        for w in _tokenize_for_search(source.replace("Пользователь:", " ").replace("Mirro:", " ")):
            if w not in _DIALOG_STOPWORDS:
                hist_words.add(w)
        # если это явное «продолжение» — добавляем и всю историю как фон
        if continuation:
            for line in user_lines[-3:]:
                for w in _tokenize_for_search(line.replace("Пользователь:", " ")):
                    if w not in _DIALOG_STOPWORDS:
                        hist_words.add(w)
        enrichment = " ".join(sorted(hist_words)[:40])
        enriched = (prompt + " " + enrichment).strip()
    return enriched


def _try_web_first(prompt):
    """Если запрос содержит триггеры «свежести», сразу отвечает веб-поиском.
    Единственный return: dict-ответ или None."""
    result = None
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.thinking import thinking as _th
        web_hits = sum(1 for t in _th.WEB_TRIGGERS if t in prompt.lower())
        if web_hits > 0:
            web_first = _web_answer(prompt)
            if web_first:
                result = {"content": _voice(web_first, prompt, "web"), "strategy": "web",
                          "confidence": 0.45}  # веб-ответ — уверенность умеренная
    except Exception:
        result = None
    return result


def _voice_or_none(raw, prompt, strategy):
    """Оборачивает ответ в голос Мирро. Единственный return: dict-ответ или None."""
    result = None
    if raw:
        voiced = _voice(raw, prompt, strategy)
        if voiced:
            result = {"content": voiced, "strategy": strategy}
    return result


def _clarify_guess(prompt):
    """Если запрос неоднозначен/слишком широк (без конкретики), возвращает
    уточняющий вопрос — чтобы найти точный ответ, а не гадать. Один return:
    dict-ответ или None (вопрос конкретный — продолжаем)."""
    result = None
    try:
        q = (prompt or "").strip().lower()
        # признаки неоднозначности: явно широкая фраза БЕЗ конкретной темы,
        # или очень короткий запрос с пустым смыслом
        words = [w for w in _re.findall(r"[а-яёa-z]{4,}", q)]
        broad = any(b in q for b in ("расскажи что-нибудь", "расскажи обо всём",
                                     "что-нибудь интересное", "чем заняться",
                                     "дай совет", "подскажи что", "не знаю что спросить"))
        no_topic = (q in ("что это", "объясни это", "объясни", "расскажи", "подробнее")
                    or (len(words) == 0 and q))
        if (broad or no_topic):
            sample = " ".join(words[:2]) if words else "эту тему"
            result = {
                "content": ("Уточни, пожалуйста: ты про «" + sample + "»? "
                            "Скажи подробнее — какую именно сторону раскрыть?"),
                "strategy": "clarify",
            }
    except Exception:
        result = None
    return result


def _moderation_gate(prompt):
    """Проверяет вход на нежелательный контент; если он опасен — возвращает
    безопасный отказ. Иначе None (продолжать). Один return: dict|None."""
    result = None
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from algos.moderation import moderate_input
        m = moderate_input(prompt)
        if not m.get("ok"):
            result = {"content": m.get("reply", "Эта тема вне моей компетенции."),
                      "strategy": "moderated"}
    except Exception:
        result = None
    return result


def _graph_infer_unknown(prompt):
    """Вывод знаний из графа для неизвестных вопросов (нет прямого ответа в базе).
    Если в вопросе есть узлы графа и по ним строятся цепочки — возвращает связный
    «вывод», иначе None. Один return: dict-ответ или None."""
    result = None
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from algos.graph_infer import try_infer_unknown
        from algos.knowledge_graph import kg as _kg
        raw = try_infer_unknown(_kg, prompt)
        if raw:
            result = _voice_or_none(raw, prompt, "graph_infer")
    except Exception:
        result = None
    return result


def _dedupe_answer(text, min_note_chars=25):
    """Сжимает ответ: убирает повторяющиеся абзацы И дублирующие предложения
    внутри абзаца (дедуп по нормализованному фрагменту). Один return: str."""
    t = (text or "").strip()
    if not t:
        return t
    # 1) дедуп предложений внутри каждого абзаца
    blocks = [b.strip() for b in _re.split(r"\n{2,}", t) if b.strip()] or [t]
    dedup_blocks = []
    changed = False
    for b in blocks:
        sents = [s.strip() for s in _re.split(r"(?<=[.!?])\s+", b) if s.strip()]
        if len(sents) > 1:
            seen_s = set()
            kept = []
            for s in sents:
                key = _re.sub(r"[^а-яёa-z0-9]+", " ", s.lower())[:55]
                if key not in seen_s:
                    seen_s.add(key)
                    kept.append(s)
                else:
                    changed = True
            if len(kept) != len(sents):
                b = " ".join(kept)
        if b.strip():
            dedup_blocks.append(b.strip())
    # 2) дедуп абзацев между собой
    seen_p = set()
    keep = []
    for b in dedup_blocks:
        if len(b) < min_note_chars:
            keep.append(b)
            continue
        key = _re.sub(r"[^а-яёa-z0-9]+", " ", b.lower())[:60]
        if key not in seen_p:
            seen_p.add(key)
            keep.append(b)
        else:
            changed = True
    if changed and keep:
        return "\n\n".join(keep) if len(keep) > 1 else keep[0]
    return t


def _part_lead(i, total):
    """Дружелюбная связка для i-й части (из total) — естественные союзы вместо
    сухих номеров «1. 2.». Один return: str."""
    if total <= 2:
        leads = {1: "Во-первых,", 2: "А во-вторых,"}
        return leads.get(i, "Кроме того,")
    seq = {1: "Во-первых,", 2: "Во-вторых,", 3: "В-третьих,",
           4: "Затем,", 5: "Далее,"}
    return seq.get(i, "И ещё:")


def _multipart_answer(parts, cluster, context=""):
    """Отвечает связно по каждой части многочастного вопроса и склеивает ответ.
    Возвращает dict-ответ или None, если хотя бы по одной части нет ответа.
    Один return: dict|None."""
    segments = []
    ok_all = True
    for i, part in enumerate(parts, 1):
        p2 = _enrich_followup(part, context)
        web_first = _try_web_first(p2)
        if web_first is not None:
            segments.append(_part_lead(i, len(parts)) + " " + web_first['content'].strip())
            continue
        best_answer, best_score, has_result = _search_best(p2, cluster)
        if has_result and not answer_looks_bad(p2, best_answer):
            segments.append(_part_lead(i, len(parts)) + " " + _voice(best_answer, p2, "base")[:700].strip())
        else:
            ginf = _graph_infer_unknown(p2)
            if ginf is not None:
                segments.append(_part_lead(i, len(parts)) + " " + ginf['content'].strip())
            elif segments:
                ok_all = False
                break
        if len(" ".join(segments)) > 1800:
            break
    if len(segments) < 2 or not ok_all:
        return None
    # оценка полноты: если на некоторые части вопрос был разбит, но ответ на них
    # не нашёлся (или ответ по частям оборвался), честно указываем, что охвачено
    covered = len(segments)
    note = ""
    if covered < len(parts):
        note = "\n\nОтметила: не по всем частям вопроса нашёлся точный ответ — " \
               "скажи, если нужно раскрыть какую-то часть подробнее."
    return {"content": "\n".join(segments) + note,
            "strategy": "multi", "parts_total": len(parts), "parts_covered": covered}


def _mark_unsure_web_result(result):
    """Помечает веб/провайдер-ответ раздела фолбэка низкой уверенностью.
    Нужна, потому что вызывающий код ожидает строку-ответ, а не None.
    Один return: dict (тот же объект, для цепочек)."""
    if result.get("strategy") in ("web", "provider"):
        result.setdefault("confidence", 0.45)
    return result


def _fallback_chain(prompt):
    """Финальная цепочка: веб → граф-вывод → провайдер → подсказка. Единственный return: dict."""
    web_answer = _web_answer(prompt)
    if web_answer:
        result = {"content": _voice(web_answer, prompt, "web"), "strategy": "web",
                  "confidence": 0.45}
    else:
        # веб пуст — пробуем вывести знания из графа по связям до сдачи
        ginf = _graph_infer_unknown(prompt)
        if ginf is not None:
            result = ginf
            result["workspace"] = "сознание: веб пуст → вывод знаний из графа (рассуждение по связям)"
        else:
            provider_answer = try_provider(prompt)
            if provider_answer:
                result = {"content": provider_answer[:2500], "strategy": "provider"}
            else:
                hint = _provider_help_hint()
                result = {"content": "Не нашла это ни в базе, ни в интернете. Переформулируй вопрос." + hint, "strategy": "unknown"}
    _mark_unsure_web_result(result)
    return result


def _guarded_first_stage(prompt):
    """Первая стадия ответа: уточнение и модерация. Любое исключение внутри
    (или None вместо dict) не должно ронять ответ — тогда возвращается None,
    и цепочка идёт дальше. Один return: dict-ответ или None."""
    result = None
    try:
        result = _pick_clarify_or_gate()
    except Exception:
        result = None
    return result


def _pick_clarify_or_gate(prompt):
    """Уточняющий вопрос важнее модерации: он не запускает фильтр и не тратит
    работу. Поле workspace объясняет, какая стадия сработала.
    Один return: dict-ответ или None."""
    result = None
    clarify = _clarify_guess(prompt)
    chosen = clarify if clarify is not None else _moderation_gate(prompt)
    if isinstance(chosen, dict) and chosen.get("content"):
        result = chosen
        result["workspace"] = ("сознание: уточняющий вопрос (запрос неоднозначен — нужна конкретика)"
                               if clarify is not None
                               else "сознание: безопасность (запрос отсечён фильтром модерации)")
    return result


def _try_web_first_guard(prompt):
    """`_try_web_first` не должен рвать цепочку ни исключением, ни пустым
    контентом. Один return: dict-ответ или None."""
    result = None
    try:
        candidate = _try_web_first(prompt)
        if isinstance(candidate, dict) and candidate.get("content"):
            result = candidate
    except Exception:
        result = None
    return result


def _answer_by_search_stages(prompt, cluster, context, current=None):
    """Стадии поиска после прямых обработчиков: многочастный разбор, веб-триггер
    свежести, база → веб, вывод из графа, фолбэк. Если `current` уже содержит
    ответ, он сохраняется: поиск не перекрывает уже найденное.
    Один return: tuple(str-промпт, dict-ответ)."""
    found = current if isinstance(current, dict) and current.get("content") else None
    try:
        alive_prompt = _enrich_followup(prompt, context) or prompt
        multi = _multipart_from_parts(prompt, cluster, context)
        result = multi if found is None and multi is not None else found
        result = result if result is not None else _search_answer(alive_prompt, cluster)
    except Exception:
        alive_prompt = prompt
        result = found if found is not None else _fallback_chain(prompt)
    # пустой ответ не отдаём: голос мог отказаться озвучивать чужой текст
    if not (result or {}).get("content"):
        result = result or {}
        result["content"] = ("Не нашла нормального ответа в базе, а в интернете — пока недоступен. "
                             "Переформулируй вопрос.")
    return alive_prompt, result


def _multipart_from_parts(prompt, cluster, context):
    """Многочастный вопрос: ответ по каждой части и склейка. Один return: dict или None."""
    result = None
    parts = _split_multipart(prompt)
    multi = _multipart_answer(parts, cluster, context) if len(parts) > 1 else None
    if isinstance(multi, dict) and multi.get("content"):
        result = multi
        result["workspace"] = "сознание: многочастный запрос разбит и отвечен по частям"
    return result


def _search_answer(prompt, cluster):
    """Локальный поиск по базе с честным переходом к вебу и графу.
    Один return: dict-ответ (никогда не None)."""
    result = None
    try:
        web_first = _try_web_first_guard(prompt)
        if web_first is not None:
            result = web_first
            result["workspace"] = "сознание: веб-триггер свежести (GNWT: свежая внешняя трансляция)"
        else:
            result = _search_answer_by_database(prompt, cluster)
    except Exception:
        result = None
    return result if result is not None else _fallback_chain(prompt)


def _definition_first(prompt):
    """Точная глосса словаря раньше поиска по базе: «что такое банк» не должно
    отвечать про банку из-за совпадения основы. Один return: dict-ответ|None."""
    q = (prompt or "").lower()
    if not any(m in q for m in ("что такое", "что значит", "кто такой",
                                "кто такая", "определение")):
        return None
    try:
        from algos.module_knowledge import try_definition
        text = (try_definition(prompt) or "").strip()
    except Exception:
        return None
    if not text:
        return None
    # глосса полезна, только если называет слово, о котором спросили
    head = text.split("—")[0].strip().lower()
    if head and (head in q or (len(head) > 4 and head[:5] in q)):
        return {"content": text, "strategy": "definition", "score": 1.0}
    return None


def _search_answer_by_database(prompt, cluster):
    """База → веб → граф → финальный резерв. Один return: dict-ответ или None
    (None — если стадия не смогла выбрать стратегию)."""
    gloss = _definition_first(prompt)
    if gloss is not None:
        return gloss
    best_answer, best_score, has_result = _search_best(prompt, cluster)
    if has_result and answer_looks_bad(prompt, best_answer):
        result = _answer_base_is_garbage(prompt)
    elif not has_result and cluster in ("ru", "knowledge"):
        result = _answer_from_graph_or_web(prompt)
    elif has_result:
        result = _answer_from_base(best_answer, best_score, prompt, cluster)
    else:
        result = _fallback_chain(prompt)
        result["workspace"] = result.get("strategy", "unknown") + ": сознание — финальный резерв (провайдер/веб)"
    return result


def _answer_base_is_garbage(prompt):
    """База дала мусор: пробуем веб, иначе честно говорим об этом.
    Один return: dict-ответ."""
    result = {"content": "Не нашла нормального ответа в базе, а в интернете — пока недоступен. Переформулируй вопрос.",
              "strategy": "web"}
    try:
        bad_web = _web_answer(prompt)
        voiced = _voice_or_none(bad_web, prompt, "web") if bad_web else None
        if voiced is not None:
            result = voiced
            result["confidence"] = 0.45
            result["workspace"] = "сознание: база мусорная → веб (GNWT: смена рабочего пространства)"
        else:
            result["workspace"] = "сознание: пустое рабочее пространство (ни база, ни веб)"
    except Exception:
        result["workspace"] = "сознание: пустое рабочее пространство (ни база, ни веб)"
    return result


def _answer_from_graph_or_web(prompt):
    """Нет прямого ответа в кластере ru/knowledge: граф по связям, затем веб,
    затем финальный резерв. Один return: dict-ответ (не None)."""
    ginf = _graph_infer_unknown(prompt)
    if isinstance(ginf, dict) and ginf.get("content"):
        result = ginf
        result["workspace"] = "сознание: прямой ответ не найден → вывод знаний из графа (рассуждение по связям)"
    else:
        cl_web = _web_answer(prompt)
        result = _voice_or_none(cl_web, prompt, "web") if cl_web else None
        if result is None:
            result = _fallback_chain(prompt)
        if result.get("strategy") == "web":
            result["confidence"] = 0.45
        result["workspace"] = "сознание: нет в базе — переход к вебу/провайдеру (GNWT: расширение пространства)"
    return result


def _answer_from_base(best_answer, best_score, prompt, cluster):
    """Готовый ответ из базы + честная уверенность. Один return: dict-ответ."""
    result = {"content": _voice(best_answer, prompt, "base")[:2500], "strategy": "base"}
    result["workspace"] = f"сознание: база знаний (рабочее пространство кластера {cluster}, IIT-связность)"
    result["content"] = _append_confidence_note(result["content"], best_score, prompt)
    return result


def _append_confidence_note(content, best_score, prompt):
    """Низкая уверенность базы → честная пометка и подсказка, где проверить.
    Один return: str (исходный текст, если уверенность не считается)."""
    text = content
    try:
        from scripts.reasoning_engine import confidence_from_score
        conf = confidence_from_score(best_score, has_result=True)
        if conf < 0.4:
            hint_topic = " ".join(_tokenize_for_search(prompt)[:3]) or "эту тему"
            text = (content
                    + f"\n\nЯ не до конца уверена в этом ответе (уверенность {int(conf*100)}%). "
                    + f"Лучше проверить «{hint_topic}» в других источниках, если это важно.")
        elif content:
            text = content
    except Exception:
        text = content
    return text


def build_response(prompt, cluster, context=""):
    """Построить ответ. prompt — актуальный вопрос, context — история диалога.
    Единственный return: dict-ответ."""
    result = {"content": "[Mirro] Внутренняя ошибка: произошла ошибка", "strategy": "error"}
    try:
        # видимая внутренняя речь: Mirro «прокручивает» шаги рассуждения
        thinking = []
        try:
            from algos.mindstream import mind as _ms
            topic = _ms.extract_topic(prompt)
            _ms.observe(prompt)
            thinking = _ms.reasoning_steps(topic)
        except Exception:
            thinking = []
        result = _guarded_first_stage(prompt)
        direct = _try_direct_handlers(prompt) if result is None else None
        if result is None and direct is not None:
            # диспетчер иногда склеивает слова по основе («банк» → «банка»):
            # точная глосса словаря важнее такого попадания
            try:
                gloss = _definition_first(prompt)
                if gloss and (direct.get("strategy") or "") in ("router", "definition"):
                    said = (direct.get("content") or "").strip().split("—")[0].strip().lower()
                    trust = gloss["content"].split("—")[0].strip().lower()
                    if said and trust and said != trust:
                        direct = gloss
            except Exception:
                pass
            result = direct
            result["workspace"] = "сознание: локальный триггер (рабочее пространство = одна память)"
        else:
            prompt, searched = _answer_by_search_stages(prompt, cluster, context, result)
            result = searched
        # метка источника ответа для ответа-выбора лучшего пути: граф/функции/история ИИ/база/веб
        try:
            s = result.get("strategy", "")
            source_map = {"definition": "мои понятия",
                          "full_explanation": "мои понятия + граф",
                          "ai_history": "история знаний об ИИ",
                          "func_kb": "база функций",
                          "knowledge_graph": "граф знаний",
                          "graph_infer": "вывод из графа",
                          "enrich": "связи графа",
                          "metacognition": "внутреннее состояние",
                          "base": "база знаний",
                          "web": "интернет",
                          "greeting": "диалог",
                          "dialog": "диалог",
                          "provider": "внешний провайдер",
                          "steps": "пошаговый план",
                          "english": "английская база знаний"}
            result["source"] = source_map.get(s, "разные источники")
        except Exception:
            result["source"] = "разные источники"
        # сжатие ответа: убираем повторяющиеся абзацы, чтобы не было «воды» и дублей
        try:
            if result.get("content") and result.get("strategy") not in ("error", "moderated"):
                result["content"] = _dedupe_answer(result.get("content", ""))
        except Exception:
            pass
        # адаптация длины к длине вопроса и кластеру:
        # короткий вопрос -> лаконичнее; код/математика -> короче; рассказ/граф -> развёрнутее
        try:
            if result.get("content") and result.get("strategy") in ("base", "web", "graph_infer"):
                q_len = len(_re.findall(r"[а-яёa-z]{3,}", prompt.lower()))
                content = result.get("content", "")
                # кластер нормирует лимиты: краткие кластеры (code/math) держат короче
                cl_low = cluster.lower()
                is_laconic = cl_low in ("code", "math") or cl_low.startswith("code") or cl_low.startswith("math")
                hard_max = 900 if is_laconic else 1300
                if q_len <= 2 and len(content) > hard_max:
                    # короткий вопрос (и код/математика) — сжимаем до первых 2-3 предложений
                    sents = _re.split(r"(?<=[.!?])\s+", content.strip())
                    keep = 2 if is_laconic else 3
                    if len(sents) > keep:
                        result["content"] = " ".join(sents[:keep]).strip()
                elif q_len >= 8 and len(content) < 400 and result.get("source"):
                    # длинный вопрос — если ответ получился куцый, дополняем
                    result["content"] = content.rstrip() + " Могу раскрыть детальнее — спроси, что именно важно."
        except Exception:
            pass
        # уточнение модерации: проверяем ИСХОДЯЩИЙ ответ после генерации и гасим,
# если он нежелателен (замена на безопасную фразу)
        try:
            if result.get("content"):
                from algos.moderation import moderate_output
                mout = moderate_output(result.get("content", ""))
                if mout.get("cleaned") and result.get("strategy") not in ("moderated",):
                    result["content"] = mout["cleaned"]
                    result["workspace"] = (result.get("workspace", "") + " (исходящий ответ отфильтрован модерацией)").strip()
        except Exception:
            pass
        # персональность: если знаем имя пользователя, обращаемся по имени
        try:
            if result.get("strategy") not in ("greeting", "dialog", "error", "user_profile"):
                from algos.user_profile import greet_name, adapt_style
                result["content"] = greet_name(result.get("content", ""), prompt)
                # адаптация стиля: сжимаем/приглашаем по предпочтению длины в профиле
                result["content"] = adapt_style(result.get("content", ""), prompt)
        except Exception:
            pass
        # эмпатичность: под тон собеседника добавляем тёплую заставку
        try:
            if result.get("strategy") not in ("greeting", "dialog", "error", "user_profile", "empathy_observe"):
                from algos.empathy import apply_empathy, observe
                observe(prompt)
                result["content"] = apply_empathy(prompt, result.get("content", ""))
        except Exception:
            pass
    except Exception as e:
        result = {"content": f"[Mirro] Внутренняя ошибка: {e}", "strategy": "error"}
    result["content"] = _text_of(result)
    # видимая внутренняя речь: добавляем итоговый шаг о выбранной стратегии,
    # чтобы было видно, как именно Mirro пришла к ответу
    try:
        strat = result.get("strategy", "")
        strat_ru = {"definition":"отвечаю своим определением понятия",
                    "ai_history":"восстанавливаю из истории знаний об ИИ",
                    "func_kb":"подбираю подходящий алгоритм из своих функций",
                    "enrich":"собираю родственные связи в графе знаний",
                    "metacognition":"смотрю на собственное внутреннее состояние",
                    "base":"беру готовый ответ из базы знаний",
                    "web":"ищу в интернете свежую информацию",
                    "greeting":"веду обычный приветственный диалог",
                    "dialog":"веду обычный диалог",
                    "similar":"сравниваю понятия по подобию"}.get(strat, "размышляю и подбираю лучший ответ")
        thinking.append(f"Итог: {strat_ru}.")
    except Exception:
        pass
    # агент-план: явные шаги решения + источник, чтобы было видно, откуда ответ
    try:
        plan_text = ("Куда я смотрела: свой словарь понятий → связи в графе знаний → "
                     "база примеров → поиск по интернету (в этом порядке, пока не найду). ")
        plan_text += f"Сработал источник: {result.get('source', 'разные источники')}."
        result["plan"] = plan_text
    except Exception:
        result["plan"] = ""
    result["thinking"] = thinking
    # Пустой ответ не отдаём: честный отказ лучше пустоты, когда все пути
    # промолчали (например, голос отказался озвучивать чужой текст)
    if not (result.get("content") or "").strip():
        result["content"] = ("Не нашла нормального ответа в базе, а в интернете — пока недоступен. "
                             "Переформулируй вопрос.")
        result["strategy"] = "empty_fallback"
    # Финальный гейт для сравнений: ответ обязан сравнивать понятия, иначе это
    # просто текст, где встретились их слова. Проверка стоит в самом конце,
    # потому что часть обработчиков возвращает ответ мимо своих валидаторов.
    if _needs_final_gate(prompt) and answer_looks_bad(prompt, result.get("content") or ""):
        result["content"] = ("Не нашла сравнения этих понятий в своей базе. Уточните, что именно "
                             "сравнить, или спросите отдельно про каждое.")
        result["strategy"] = "quality_gate"
    return result


def _text_of(result):
    """Строковый content ответа; не-строки и None сводятся к "". Один return: str."""
    content = result.get("content", "") if isinstance(result, dict) else ""
    return content if isinstance(content, str) else ("" if content is None else str(content))


def _sse_event(data):
    """Одно SSE-событие: `data: <json>` и пустая строка после него, UTF-8.
    Один return: bytes."""
    line = "data: " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n\n"
    return line.encode("utf-8")


def _health_algorithm_status():
    """Секция algorithms для /health. Не падает, если индекс/граф не прогрет.
    Один return: dict."""
    status = {}
    try:
        status = _grab_algo().status()
        if not isinstance(status, dict):
            status = {}
    except Exception:
        status = {}
    try:
        _health_attach_graph_metrics(status)
    except Exception:
        status = status if isinstance(status, dict) else {}
    return status


def _health_attach_graph_metrics(status):
    """Нейромедиаторы, граф, кванты и иммунитет; каждая часть отдельно безопасна.
    Мутирует status и возвращает его. Один return: dict."""
    from algos.neuromodulators import nm as _nm
    from algos.knowledge_graph import kg as _kg
    status["neuromodulators"] = _health_neuromodulators(_nm)
    status["knowledge_graph"] = _health_graph_summary(_kg)
    status["quantum"] = _health_quantum_summary(_kg)
    status["immunity"] = _health_immunity_summary(_kg)
    return status


def _health_neuromodulators(nm):
    """Уровни медиаторов + текущий ритм. Один return: dict."""
    levels = {}
    try:
        levels = dict(getattr(nm, "level", {}) or {})
        levels["rhythm"] = nm.rhythm_state()
    except Exception:
        levels = levels if isinstance(levels, dict) else {}
    return levels


def _health_graph_summary(kg):
    """Размеры и плотность графа; отдельные метрики падают изолированно.
    Один return: dict."""
    nodes = _safe_len(getattr(kg, "nodes", None))
    edges = _safe_len(getattr(kg, "edges", None))
    summary = {"nodes": nodes, "edges": edges,
               "avg_dimension": 0.0,
               "density": round(edges / max(1, nodes), 3),
               "edges_per_node": round(edges / max(1, nodes), 2),
               "central_nodes": [], "mean_degree": 0.0}
    summary["avg_dimension"] = _safe_avg_dimension(kg) if nodes else 0.0
    if nodes:
        summary["central_nodes"], summary["mean_degree"] = _safe_centrality(kg)
    summary.update(_health_connectivity(kg) if edges else _empty_connectivity())
    return summary


def _safe_len(value):
    """len() без исключения для None/не-контейнеров. Один return: int."""
    size = 0
    try:
        size = len(value) if value is not None else 0
    except Exception:
        size = 0
    return size


def _safe_avg_dimension(kg):
    """Средняя размерность сети; без графа — 0.0. Один return: float."""
    dim = 0.0
    try:
        from algos.zero_dimensional import dimension_of_understanding
        dim = float(dimension_of_understanding(kg))
    except Exception:
        dim = 0.0
    return dim


def _safe_centrality(kg):
    """(топ-узлы, средняя степень) одним проходом. Один возврат: tuple."""
    top, mean = [], 0.0
    try:
        stats = kg.centrality(top_n=5)
        top = [n for n, _d in stats.get("top", [])]
        mean = float(stats.get("mean_degree", 0.0))
    except Exception:
        top, mean = [], 0.0
    return top, mean


def _empty_connectivity():
    """Поля связности для пустого/непрогретого графа. Один return: dict."""
    return {"components": 0, "biggest_component": 0, "isolated": 0, "top_nodes": []}


def _health_connectivity(kg):
    """Связность графа; при сбое — нули. Один return: dict."""
    conn = _empty_connectivity()
    try:
        raw = kg.connectivity(top_n=3)
        conn["components"] = raw.get("components", 0)
        conn["biggest_component"] = raw.get("biggest_component", 0)
        conn["isolated"] = raw.get("isolated", 0)
        conn["top_nodes"] = [n for n, _d in raw.get("top_degree", [])]
    except Exception:
        conn = _empty_connectivity()
    return conn


def _health_quantum_summary(kg):
    """Суперпозиция узлов; пустой граф сразу даёт нули. Один return: dict."""
    summary = {"superposed_nodes": 0, "P_active_sample": []}
    if not _safe_len(getattr(kg, "nodes", None)):
        return summary
    try:
        from algos.quantum_graph import init_quantum_states
        states = init_quantum_states(kg).states
        summary = {"superposed_nodes": len(states),
                   "P_active_sample": [round(a * a, 3) for a, _b in list(states.items())[:8]]}
    except Exception:
        summary = {"superposed_nodes": 0, "P_active_sample": []}
    return summary


def _health_immunity_summary(kg):
    """Иммунный скан только на непустом графе (иначе «0 заражённых» — враньё).
    Один return: dict."""
    summary = {"quarantined": 0, "n_routes": 0, "fatigued_edges": 0}
    if not _safe_len(getattr(kg, "edges", None)):
        return summary
    try:
        from algos.immune_sentinel import run_graph_immune_scan
        from algos.refractory import init_refractory_counters
        _graph, quarantined = run_graph_immune_scan(kg, max_allowed_weight=5.0)
        refr = init_refractory_counters(kg)
        summary = {"quarantined": len(quarantined),
                   "n_routes": len(getattr(kg, "meta_routes", {}) or {}),
                   "fatigued_edges": sum(1 for v in refr.edge_exhaustion.values() if v > 0.0)}
    except Exception:
        summary = {"quarantined": 0, "n_routes": 0, "fatigued_edges": 0}
    return summary


def try_ai_history(prompt):
    """Справочник «рост понимания: нейрочеловек и ИИ» (Тьюринг, Шеннон, Питтс,
    Хебб, Розенблатт, IIT, GNWT и др.) — с авторами в записях. Один return:
    str-ответ или None."""
    ans = None
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from algos.knowledge_ai_history import применить as _ai_hist
        ans = _ai_hist(prompt)
    except Exception:
        ans = None
    return ans


# ========== HTTP API ==========
class MirroAPI(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            # клиент закрыл соединение раньше ответа — это не ошибка сервера
            pass
    def _read(self):
        """Тело POST как dict. Нестандартные длительности сводятся к нулю, битый
        JSON — к None (клиент получает 400), не-UTF8 — к ошибке декодирования.
        Один return: dict или None."""
        data = None
        length = _content_length(self.headers)
        if length:
            raw = self.rfile.read(length) or b""
            data = json.loads(raw.decode("utf-8"))
        return data
    def _serve_file(self, path, ctype):
        served = False
        if path.exists():
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                served = False
            else:
                served = True
        return served
    def _authorized(self):
        """Проверяет токен доступа. Один return: bool.

        Пропускает, если AUTH_TOKEN пуст (локальный режим). Иначе сверяет
        заголовок Authorization: Bearer <token> или query-параметр ?token=.
        """
        ok = True
        if AUTH_TOKEN:
            supplied = ""
            auth = self.headers.get("Authorization", "")
            if auth.lower().startswith("bearer "):
                supplied = auth[7:].strip()
            if not supplied:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                supplied = (qs.get("token") or [""])[0]
            ok = supplied == AUTH_TOKEN
        return ok
    def _require_auth(self):
        """Если токен неверен — пишет 401. Один return: bool (разрешено)."""
        ok = self._authorized()
        if not ok:
            self._json({"error": "unauthorized"}, 401)
        return ok
    def _route_path(self):
        """Путь без query-параметров (для маршрутизации). Один return: str."""
        route = ""
        try:
            from urllib.parse import urlsplit
            route = urlsplit(self.path).path or "/"
        except Exception:
            route = self.path.split("?", 1)[0]
        return route
    def do_GET(self):
        if self._require_auth():
            route = self._route_path()
            served = False
            if route in ("/", "/index.html"):
                served = self._serve_file(MIRRO_HOME / "web" / "index.html", "text/html; charset=utf-8")
            elif route == "/meysto-neiroset.html":
                served = self._serve_file(MIRRO_HOME / "web" / "meysto-neiroset.html", "text/html; charset=utf-8")
            elif route == "/mirro-evolve.html":
                served = self._serve_file(MIRRO_HOME / "web" / "mirro-evolve.html", "text/html; charset=utf-8")
            elif route == "/catalog.json":
                served = self._serve_file(DATA / "catalog_phase1.json", "application/json; charset=utf-8")
            elif not served:
                served = self._route_GET_dispatch(route)
            if not served:
                self._json({"error": "not found"}, 404)

    def _route_GET_dispatch(self, route):
        """Диспетчер не-файловых GET-маршрутов. Один return: bool (обработано)."""
        handled = True
        if route == "/health":
            status = core.status()
            status["algorithms"] = _health_algorithm_status()
            self._json(status)
        elif route == "/v1/models":
            t = int(time.time())
            self._json({"object": "list", "data": [
                {"id": "mirro/default", "object": "model", "created": t, "owned_by": "mirro"},
                {"id": "mirro/ru", "object": "model", "created": t, "owned_by": "mirro"},
            ]})
        elif route == "/v1/top-questions":
            top = core.stats.get("top_questions", {})
            ranked = sorted(top.items(), key=lambda x: -x[1])[:15]
            self._json({"questions": [{"q": q, "count": c} for q, c in ranked]})
        elif route == "/v1/dialogue-summary":
            # резюме длинного диалога (для UI-поля в Аналитике)
            try:
                from algos.dialogue_memory import dm as _dm
                self._json({"summary": _dm.get_summary()})
            except Exception:
                self._json({"summary": ""})
        elif route == "/v1/evolve":
            try:
                from algos.evolve import get_evolver, _default_A, _default_X, report
                ev = get_evolver()
                from urllib.parse import parse_qs, urlsplit
                pq = parse_qs(urlsplit(self.path).query)
                steps = int(pq.get("steps", ["1"])[0])
                for _ in range(min(max(steps, 0), 20)):
                    ev.evolve_step(_default_A(ev.num_nodes), _default_X(ev.num_nodes, ev.input_dim))
                best = ev.best_genome()
                chem = {}
                if best:
                    chem = {"dopamine": round(best.dopamine, 3),
                            "serotonin": round(best.serotonin, 3),
                            "acetylcholine": round(best.acetylcholine, 3),
                            "gsr": round(best.gsr, 3)}
                payload = {"generation": ev.generation,
                           "population": len(ev.population),
                           "experience": len(ev.experience_base),
                           "best_chemistry": chem,
                           "history": list(getattr(ev, "fitness_history", [])[-30:]),
                           "report": report()}
                self._json(payload)
            except Exception as e:
                self._json({"error": str(e)}, 500)
        elif route == "/v1/learn-report":
            self._json(self._learn_report())
        elif route == "/v1/search":
            # внешний поиск по базе знаний: /v1/search?q=...&top=5
            from urllib.parse import parse_qs, urlsplit as _us
            try:
                pq = parse_qs(_us(self.path).query)
                query = pq.get("q", [""])[0]
                top = int(pq.get("top", ["5"])[0])
                if not query:
                    self._json({"error": "no query"}, 400)
                else:
                    from scripts.algorithms import algo as _alg
                    results = _alg.search_tfidf(query, top_n=min(max(top, 1), 20))
                    items = []
                    for (inst, out, cl), sc in results[:min(max(top, 1), 10)]:
                        items.append({"question": inst[:200], "answer": out[:500], "cluster": cl, "score": round(sc, 3)})
                    self._json({"query": query, "results": items, "count": len(items)})
            except Exception as e:
                self._json({"error": str(e)}, 500)
        elif route == "/v1/graph":
            # внешний снимок графа: /v1/graph?concept=X&depth=1
            from urllib.parse import parse_qs, urlsplit as _us2
            try:
                pq = parse_qs(_us2(self.path).query)
                concept = pq.get("concept", [""])[0]
                from algos.knowledge_graph import kg as _kg2
                payload = {"nodes": len(_kg2.nodes), "edges": len(_kg2.edges)}
                if concept:
                    cc = concept.lower().strip()
                    links = _kg2.what_links(cc)[:8]
                    payload["concept"] = cc
                    payload["links"] = links
                else:
                    top = _kg2.centrality(top_n=8)
                    payload["central"] = [n for n, _d in top["top"]]
                # метрики графа: кластеры тем и мосты между областями
                try:
                    tc = _kg2.topic_clusters(max_clusters=5, max_nodes=50)
                    payload["clusters"] = [{"topic": c, "members": m[:8]}
                                           for c, m in tc.get("clusters", [])]
                    payload["bridges"] = tc.get("bridges", [])
                except Exception:
                    payload["clusters"] = []
                    payload["bridges"] = []
                self._json(payload)
            except Exception as e:
                self._json({"error": str(e)}, 500)
        elif route == "/v1/report":
            # сводный отчёт о состоянии Mirro: агрегированная статистика одним эндпоинтом
            try:
                import datetime as _dt_rep
                rep = {"name": "Mirro", "version": "0.3",
                       "calls": core.stats.get("calls", 0),
                       "generated_at": _dt_rep.datetime.now().isoformat(timespec="seconds")}
                # база/индекс
                algo = _grab_algo()
                clusters = {}
                for _i, _o, cl in getattr(algo, "examples", [])[:1]:
                    clusters = {}
                for _i, _o, cl in getattr(algo, "examples", []):
                    clusters[cl] = clusters.get(cl, 0) + 1
                rep["index"] = {"examples": len(getattr(algo, "examples", [])),
                                "vocab": len(getattr(algo, "doc_freq", {})),
                                "clusters": clusters}
                # граф
                from algos.knowledge_graph import kg as _kg_rep
                rep["graph"] = {"nodes": len(_kg_rep.nodes), "edges": len(_kg_rep.edges)}
                try:
                    conn = _kg_rep.connectivity(top_n=3)
                    rep["graph"]["components"] = conn.get("components", 0)
                    rep["graph"]["isolated"] = conn.get("isolated", 0)
                except Exception:
                    pass
                # корпус
                try:
                    rep["corpus_total"] = core.corpus_total()
                except Exception:
                    rep["corpus_total"] = 0
                # бэкап
                rep["backup"] = core.status().get("backup", {})
                # пробелы знаний: слабые темы из corpus_audit (где примеров мало)
                gaps_rep = {"weak_topics": {}, "duplicates": 0}
                try:
                    sys.path.insert(0, str(MIRRO_HOME))
                    import scripts.corpus_audit as _audit_mod
                    arep = _audit_mod.audit(limit_topic_scan=8000)
                    gaps_rep = {"weak_topics": arep.get("weak_topics", {}),
                                "duplicates": arep.get("duplicates", 0),
                                "strong_topics": arep.get("strong_topics", [])}
                except Exception:
                    gaps_rep = {"weak_topics": {}, "duplicates": 0, "strong_topics": []}
                rep["gaps"] = gaps_rep
                # лог рефлексии: сколько раз укрепила связи по времени (из reflection_log)
                reflection = {"total": 0, "recent_24h": 0}
                try:
                    rlog = MIRRO_HOME / "data" / "reflection_log.jsonl"
                    if rlog.is_file():
                        lines = rlog.read_text("utf-8", errors="replace").splitlines()
                        reflection["total"] = len(lines)
                        if lines:
                            import datetime as _dtc
                            from dateutil.parser import parse as _dparse
                            now = _dtc.datetime.now()
                            recent = 0
                            for ln in lines[-50:]:
                                try:
                                    ts_s = (ln.split('"ts": "')[1].split('"')[0])
                                    when = _dparse(ts_s)
                                    if (now - when).total_seconds() < 86400:
                                        recent += 1
                                except Exception:
                                    continue
                            reflection["recent_24h"] = recent
                        else:
                            reflection["recent_24h"] = 0
                except Exception:
                    reflection = {"total": 0, "recent_24h": 0}
                rep["reflection"] = reflection
                self._json(rep)
            except Exception as e:
                self._json({"error": str(e)}, 500)
        elif route == "/v1/knowledge":
            from urllib.parse import parse_qs, urlsplit
            try:
                query = parse_qs(urlsplit(self.path).query).get("q", [""])[0]
                kind = parse_qs(urlsplit(self.path).query).get("kind", ["enrich"])[0]
                from algos.knowledge_graph import kg as _kg
                payload = {"nodes": len(_kg.nodes), "edges": len(_kg.edges)}
                if kind == "enrich":
                    payload["answer"] = _kg.enrich(query, max_hop=2)[:4]
                elif kind == "links":
                    payload["answer"] = _kg.what_links(query)[:6]
                elif kind == "similar":
                    from algos.knowledge_graph import _pair_from
                    a, b = _pair_from(query) if query else (None, None)
                    payload["similarity"] = _kg.similarity(a, b) if (a and b) else None
                elif kind == "function":
                    from algos.module_knowledge import try_function_knowledge as _fk
                    payload["answer"] = _fk(query) if query else "база знаний по функциям: готова"
                else:
                    payload["answer"] = []
                self._json(payload)
            except Exception as e:
                self._json({"error": str(e)}, 500)
        else:
            handled = False
        return handled

    def _graph_growth_history(self, graph, limit=60):
        """Дописывает текущий снимок роста графа (узлы/рёбра + метка времени) в
        data/graph_story.jsonl и возвращает последние <limit> точек для дашборда.
        Один return: list[dict]."""
        import datetime as _dt
        points = []
        try:
            story = MIRRO_HOME / "data" / "graph_story.jsonl"
            try:
                story.parent.mkdir(parents=True, exist_ok=True)
                # топ новых/свежих связей (по весу) для отчёта «что бот сформировал»
                top_edges = []
                try:
                    seen = set()
                    for (s, p, d), w in list(graph.edges.items())[-400:]:
                        small = s if len(s) <= 18 else s[:15]
                        dsmall = d if len(d) <= 18 else d[:15]
                        key = (small, dsmall)
                        if key not in seen:
                            seen.add(key)
                            top_edges.append(f"{small}─{p}→{dsmall}")
                    top_edges = top_edges[-6:]
                except Exception:
                    top_edges = []
                with open(story, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({
                        "ts": _dt.datetime.now().isoformat(timespec="seconds"),
                        "nodes": len(graph.nodes),
                        "edges": len(graph.edges),
                        "new_links": top_edges,
                    }, ensure_ascii=False) + "\n")
            except Exception:
                pass
            if story.exists():
                lines = [l for l in story.read_text("utf-8").splitlines() if l.strip()][-limit:]
                for line in lines:
                    try:
                        points.append(json.loads(line))
                    except Exception:
                        pass
        except Exception:
            points = []
        return points

    def _learn_report(self):
        """Живой отчёт об обучении Mirro: реальные веса MLP, статус, метрики.

        Читается из models/model_state.json (персистентный перцептрон/MLP) и
        core/stats.json (счётчики вызовов/кластеры). Без вызова тяжёлого индекса.
        """
        report = {"weights": {}, "bias": 0, "hidden": {}, "trained": False,
                  "auto_learned": 0, "trainer_cycles": 0, "trainer_accuracy": 0,
                  "clusters": {}, "total_examples": core.stats.get("total_examples", 0),
                  "calls": core.stats.get("calls", 0)}
        try:
            st = {}
            _msf = MODELS / "model_state.json"
            if _msf.exists():
                st = json.loads(_msf.read_text("utf-8"))
            report["weights"] = st.get("perceptron_weights", {}) or {}
            report["bias"] = st.get("perceptron_bias", 0) or 0
            report["hidden"] = st.get("perceptron_hidden", {}) or {}
            report["hidden_bias"] = st.get("perceptron_hidden_bias", {}) or {}
            report["trained"] = bool(st.get("perceptron_trained"))
            report["auto_learned"] = st.get("auto_learned", 0)
            report["trainer_cycles"] = st.get("trainer_cycles", 0)
            report["trainer_accuracy"] = st.get("trainer_accuracy", 0)
            report["trainer_clusters"] = st.get("trainer_clusters", {}) or {}
            report["updated"] = st.get("updated")
        except Exception:
            pass
        report["clusters"] = {k: v.get("examples", 0) for k, v in core.get_cluster_info().items()}
        report["clusters_calls"] = dict(core.stats.get("clusters_used", {}))
        # Рост графа знаний во времени (для дашборда): последние точки узлов/рёбер
        try:
            from algos.knowledge_graph import kg as _kg_page
            report["graph_story"] = self._graph_growth_history(_kg_page)
        except Exception:
            report["graph_story"] = []
        # Соответствие весов формату «Мозг Мирро» в Мейсто (f0..f3) — если MLP,
        # отдаём и выходные h*_out, и плоские f* для простого предсказания.
        return report
    def _chat_payload(self, messages, model, response, prompt):
        """Формирует итоговый JSON-ответ (не-SSE). Единственный return: dict."""
        content = _text_of(response) if response else "Ошибка"
        # видимая внутренняя речь: шаги рассуждения из mindstream, затем квантовая сноска
        thinking = (response.get("thinking") or []) if isinstance(response, dict) else []
        reasoning = ""
        try:
            steps = "\n".join(f"• {s}" for s in thinking)
            reasoning = (steps + "\n" if steps else "") + _quantum_context_note()
        except Exception:
            reasoning = ""
        return {"id": f"mirro-{int(time.time())}", "object": "chat.completion",
                "model": "mirro-evolutionary-v4",
                "usage": {"prompt_tokens": len(prompt)//4, "completion_tokens": len(content)//4},
                "choices": [{"index": 0, "message": {"role": "assistant",
                             "content": content,
                             "reasoning_content": reasoning,
                             "plan": _text_of({"content": response.get("plan", "")}) if isinstance(response, dict) else "",
                             "source": _text_of({"content": response.get("source", "")}) if isinstance(response, dict) else "",
                             "confidence": response.get("confidence", None)}}]}

    def _handle_chat(self, body):
        """Обрабатывает POST /v1/chat/completions. Единственный return: None.

        Пишет ответ клиенту (SSE или JSON) внутри. Не возвращает значение."""
        messages = body.get("messages", []) if isinstance(body, dict) else []
        model = body.get("model", "mirro/default") if isinstance(body, dict) else "mirro/default"
        stream = body.get("stream", False) if isinstance(body, dict) else False
        if not isinstance(messages, list) or not messages:
            self._json({"error": "no messages"}, 400)
        else:
            conversation = []
            last_user = ""
            for m in messages:
                if not isinstance(m, dict):
                    continue
                role = str(m.get("role") or "").lower()
                content = str(m.get("content") or "").strip()
                if content:
                    conversation.append(f"{'Пользователь' if role in ('user','human') else 'Mirro'}: {content}")
                    if role in ("user", "human"):
                        last_user = content
            prompt = last_user or " ".join(m.get("content", "") for m in messages)
            context = "\n".join(conversation)
            cluster = core.classify_task(prompt or context)
            t0 = time.time()
            response = build_response(prompt, cluster, context)
            try:
                if response.get("strategy") in ("base",) and response.get("content"):
                    algo = _grab_algo()
                    if algo.should_auto_learn(prompt, response["content"]):
                        algo.autonomous_learn(cycles=15)
            except Exception:
                pass
            # самообучение на новых темах: новое/свежее в диалоге Mirro запоминает
            # себе в корпус (вопрос → ответ) и фиксирует тему во внутренней речи.
            try:
                if response and response.get("content") and response.get("strategy") != "error":
                    from algos.mindstream import mind as _m2, MindStream as _MS2
                    topic = _MS2.extract_topic(prompt)
                    _m2.observe(prompt)
                    if topic and response.get("strategy") in ("definition", "base", "func_kb", "ai_history"):
                        _m2.learn_new_pair(prompt, response.get("content", ""))
                        # Хебб-усиление: раз ответ удался и у вопроса есть тема,
                        # связываем её с ядром ответа, чтобы связь укреплялась с повтором
                        try:
                            from algos.knowledge_graph import kg as _kg3
                            from algos.mindstream import _STOP as _MS_STOP
                            words = [w for w in _re.findall(r"[а-яёa-z]{3,}",
                                     str(response.get("content", "")).lower()) if w not in _MS_STOP]
                            if topic and words:
                                # усиливаем связь не с первым случайным токеном, а с
                                # узлом графа, реально присутствующим в ответе: тема
                                # привязывается к осмысленному понятию, а не к мусору
                                pick = next((w for w in words if _kg3.get_node(w)), None)
                                _kg3.hebbian_learn(topic, pick or words[0], amount=0.08, depth=3)
                                # персистентно сохраняем обученное ребро, чтобы оно
                                # не терялось между запусками сервера
                                try:
                                    _kg3.save(MODELS / "knowledge_graph.pkl")
                                except Exception:
                                    pass
                        except Exception:
                            pass
            except Exception:
                pass
            if response:
                core.log_call(prompt, cluster, f"mirro-{response.get('strategy','ai')}", int((time.time()-t0)*1000), True)
            content = _text_of(response) or "Ошибка"
            # темпераментный стилизатор: характер «мозга» формирует оформление ответа
            try:
                from algos.voice_temperament import determine_voice_temperament, try_apply_temperament_filters
                from algos.neuromodulators import nm as _nm
                tch = getattr(_nm, "level", {})
                tmp = determine_voice_temperament(tch)
                filtered = try_apply_temperament_filters(content.split(" "), tmp)
                styled = " ".join(filtered)
                if styled and len(styled) >= 20:
                    content = styled
            except Exception:
                pass
            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache"); self.end_headers()
                for chunk in content.split("\n"):
                    self.wfile.write(_sse_event({'choices': [{'delta': {'content': chunk + "\n"}}]}))
                    self.wfile.flush()
                self.wfile.write(b"data: [DONE]\n\n")
            else:
                payload = self._chat_payload(messages, model, response, prompt)
                self._json(payload)
        return None

    def do_POST(self):
        if self._require_auth():
            route = self._route_path()
            if route == "/v1/chat/completions":
                try:
                    body = self._read()
                except Exception:
                    body = None
                if body is not None:
                    self._handle_chat(body)
                else:
                    self._json({"error": "bad request"}, 400)
            elif route == "/v1/feedback":
                self._post_feedback()
            elif route == "/v1/improve":
                self._post_improve()
            elif route == "/v1/self-learn":
                self._post_self_learn()
            elif route == "/v1/brain-eval":
                self._post_brain_eval()
            else:
                self._json({"error": "not found"}, 404)

    def _post_feedback(self):
        try:
            body = self._read(); algo = _grab_algo()
            algo.train_from_feedback(body.get("query",""), body.get("response",""), body.get("liked",True))
            kg_note = ""
            try:
                from algos.knowledge_graph import kg as _kg, _clean_q, _pair_from
                from algos.neural_electric import hebbian_update_path
                liked = body.get("liked", True)
                fb = 1.0 if liked else -1.0
                q = _clean_q(body.get("query",""))
                a, b = _pair_from(q)
                if a and b:
                    _kg.reward_sign(a, b, fb, 0.05)
                path = algo.hebbian_path if hasattr(algo, "hebbian_path") and algo.hebbian_path else None
                if path and len(path) >= 2:
                    r = hebbian_update_path(_kg, path, fb, learning_rate=0.02)
                    if r["updated"]:
                        kg_note = f", routes={r['updated']}(+{r['strengthened']}/-{r['weakened']})"
                _kg.save(MODELS / "knowledge_graph.pkl")
                if a and b and not kg_note:
                    kg_note = f", pair_hebb={fb}"
            except Exception:
                kg_note = ""
            # умное самообучение: при лайке пара (вопрос→ответ) попадает в корпус ТОЛЬКО
            # если она хорошая и не дублируется — Mirro умнеет от лайков, а не копит мусор
            try:
                if body.get("liked", True) and body.get("query") and body.get("response"):
                    from algos.mindstream import mind as _ms_fb
                    _ms_fb.learn_liked_pair(body.get("query", ""), body.get("response", ""))
            except Exception:
                pass
            self._json({"status": "ok" + kg_note})
        except Exception as e:
            self._json({"status": "error", "message": str(e)}, 500)

    def _post_improve(self):
        """Переформулировка ответа по запросу «улучшить»: берёт вопрос и прошлый
        ответ, повторяет поиск с бо́льшим охватом и возвращает альтернативную
        формулировку либо отредактированный вариант. Один return: None."""
        try:
            body = self._read()
            q = (body.get("query") or "").strip()
            prev = (body.get("response") or "").strip()
            if not q:
                self._json({"error": "no query"}, 400)
                return None
            # расширенный поиск: больше кандидатов → другой набор для лучшей фразы
            from scripts.algorithms import algo as _imp_algo
            q2 = _semantic_expand(q)
            results = _imp_algo.search_tfidf(q2, top_n=8)
            _, choose_best, _ = _reasoning()
            best, sc, _r = choose_best(q, results, preferred=None)
            improved = None
            if best and not answer_looks_bad(q, best) and best.strip() != prev.strip():
                improved = _voice(best, q, "base")[:2500]
            if not improved:
                # нет лучшего кандидата — перефразируем прошлый ответ короче и проще
                improved = prev[:1200]
                short = improved[:60].rstrip()
                if short:
                    improved = short + " — если коротко. Хочешь, разложу подробнее?"
            core.log_call(q, core.classify_task(q), "improve", 1, True)
            self._json({"content": improved})
        except Exception as e:
            self._json({"error": str(e)}, 500)
        return None

    def _post_self_learn(self):
        try:
            algo = _grab_algo(); n = min(50, len(algo.examples)); learned = 0
            for inst, out, cl in algo.examples[::max(1, len(algo.examples)//n)][:n]:
                if len(inst) >= 10:
                    ans = algo.compose_answer(inst, top_n=3)
                    if ans and algo.qa_score(inst, ans) > 0.5:
                        learned += 1
            self._json({"status": "ok", "learned": learned, "checked": n})
        except Exception as e:
            self._json({"status": "error", "message": str(e)}, 500)

    def _post_brain_eval(self):
        try:
            body = self._read(); algo = _grab_algo()
            q = body.get("query", "") or ""; c = body.get("candidate", "") or ""
            if not c:
                c = body.get("candidate", "")
            score = algo.perceptron_predict(q, c) if (q or c) else 0.5
            self._json({"status": "ok", "score": round(float(score), 4),
                        "trained": bool(getattr(algo, "perceptron_trained", False))})
        except Exception as e:
            self._json({"status": "error", "message": str(e)}, 500)
    def do_DELETE(self):
        # У Mirro нет изменяемых ресурсов, удаляемых через DELETE —
        # отвечаем JSON-404 единообразно с остальным API (вместо HTML-501).
        self._json({"error": "not found"}, 404)
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
    def log_message(self, fmt, *args): pass

def _lan_ip():
    """Локальный IP машины (для доступа по сети). Один return: str или '127.0.0.1'."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = "127.0.0.1"
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def _access_addresses():
    """Список адресов, по которым доступен сервер. Один return: str."""
    ans = f"Только локально: http://127.0.0.1:{PORT}"
    if HOST in ("0.0.0.0", ""):
        lan = _lan_ip()
        ans = (f"Локально:  http://127.0.0.1:{PORT}\n"
               f"По сети (WiFi/модем): http://{lan}:{PORT}")
    return ans

def _seed_knowledge_graph():
    """Наполняет знаниевый граф при старте: понятия из корпусов + ТТЛ-извлечение
    из маленьких файлов и истории ИИ. Тихий вызов — не роняет сервер при ошибке.
    Единственный return: None."""
    try:
        import sys as _sys
        if str(MIRRO_HOME) not in _sys.path:
            _sys.path.insert(0, str(MIRRO_HOME))
        from algos.knowledge_graph import kg
        from algos.ttl_extract import extract
        # 0) Загружаем сохранённый граф (то, что уже выучили), чтобы не терять при перезапуске
        gpath = MODELS / "knowledge_graph.pkl"
        prev_edges = kg.load(gpath)
        # 1) Базовые понятия (вручную, всегда известные)
        kg.from_triples([
            ("Нейрон", "принадлежит", "мозг"),
            ("Нейрон", "передаёт", "сигнал"),
            ("Сигнал", "формирует", "мысль"),
            ("Мысль", "порождает", "понимание"),
            ("Знание", "строится на", "понимание"),
            ("Внимание", "влияет на", "память"),
            ("Память", "укрепляет", "понимание"),
            ("Граф", "хранит", "связи"),
            ("Алгоритм", "решает", "задачу"),
            # --- осмысленные связи нейросети и машинного обучения ---
            ("Нейросеть", "состоит из", "нейрон"),
            ("Нейросеть", "обучается на", "данные"),
            ("Нейросеть", "находит", "закономерности"),
            ("Нейросеть", "использует", "алгоритм"),
            ("Обучение", "меняет", "веса"),
            ("Веса", "хранят", "знание"),
            ("Знание", "лежит в", "связях"),
            ("Машинное обучение", "изучает", "данные"),
            ("Модель", "обучается на", "данные"),
            ("Интеллект", "растёт через", "обучение"),
            # --- постоянные знания о мире (чтобы граф не был пуст) ---
            ("Вода", "кипит при", "100 градусов"),
            ("Земля", "вращается вокруг", "Солнце"),
            ("Луна", "вращается вокруг", "Земля"),
            ("Люди", "дышат", "кислород"),
            ("Растения", "поглощают", "углекислый газ"),
            ("Растения", "выделяют", "кислород"),
            ("Белки", "состоят из", "аминокислоты"),
            ("ДНК", "хранит", "наследственность"),
            ("Нейрон", "соединён с", "нейрон"),
            ("Мозг", "состоит из", "нейроны"),
            ("Информация", "уменьшает", "неопределённость"),
            ("Энтропия", "измеряет", "неопределённость"),
            ("Память", "сохраняет", "информация"),
            ("Обучение", "изменяет", "память"),
            ("Внимание", "усиливает", "обучение"),
            ("Эмоции", "влияют на", "память"),
            ("Сон", "укрепляет", "память"),
            ("Повторение", "укрепляет", "память"),
            # --- наука и техника ---
            ("Свет", "движется со скоростью", "300000 км/с"),
            ("Звук", "является", "волна"),
            ("Волна", "переносит", "энергия"),
            ("Энергия", "не возникает из", "ничего"),
        ])
        # Дополним постоянными знаниями (наука, техника, математика, природа)
        kg.from_triples([
            ("Гравитация", "притягивает", "массы"),
            ("Планета", "движется по", "орбита"),
            ("Орбита", "определяется", "гравитация"),
            ("Телескоп", "наблюдает", "звёзды"),
            ("Атом", "состоит из", "ядро"),
            ("Ядро", "содержит", "протоны"),
            ("Протон", "имеет", "положительный заряд"),
            ("Электрон", "имеет", "отрицательный заряд"),
            ("Молекула", "состоит из", "атомы"),
            ("Химическая реакция", "изменяет", "вещество"),
            ("Ток", "течёт по", "проводник"),
            ("Проводник", "пропускает", "электричество"),
            ("Напряжение", "движет", "ток"),
            ("Сопротивление", "ограничивает", "ток"),
            ("Компьютер", "выполняет", "программы"),
            ("Программа", "состоит из", "алгоритмы"),
            ("Данные", "обрабатываются", "алгоритм"),
            ("Файл", "хранится в", "память компьютера"),
            ("Сеть", "связывает", "компьютеры"),
            ("Интернет", "объединяет", "сети"),
            ("Браузер", "открывает", "веб-страницы"),
            ("Веб-страница", "написана на", "HTML"),
            ("Хранилище", "сохраняет", "данные"),
            ("База данных", "организует", "информация"),
            ("Шифрование", "защищает", "данные"),
            ("Ключ", "расшифровывает", "шифр"),
            # --- математика ---
            ("Число", "делится на", "множитель"),
            ("Простые числа", "делятся только на", "1 и себя"),
            ("Дробь", "состоит из", "числитель и знаменатель"),
            ("Квадрат", "имеет", "равные стороны"),
            ("Треугольник", "имеет", "три стороны"),
            ("Окружность", "определяется", "радиус"),
            ("Пи", "равно", "3.14159"),
            ("Логарифм", "обратен", "степень"),
            ("Интеграл", "вычисляет", "площадь"),
            ("Производная", "измеряет", "скорость изменения"),
            # --- природа и человек ---
            ("Человек", "обладает", "разум"),
            ("Разум", "пользуется", "логика"),
            ("Логика", "строит", "рассуждения"),
            ("Рассуждения", "ведут к", "вывод"),
            ("Вывод", "рождает", "знание"),
            ("Язык", "выражает", "мысли"),
            ("Слово", "несёт", "значение"),
            ("Значение", "опирается на", "контекст"),
            ("Интуиция", "дополняет", "логика"),
            ("Творчество", "создаёт", "новое"),
            ("Новое", "обогащает", "знание"),
            ("Сердце", "качает", "кровь"),
            ("Лёгкие", "усваивают", "кислород"),
            ("Пища", "даёт", "энергия организму"),
            ("Вода", "необходима для", "жизнь"),
            ("Жизнь", "требует", "энергия"),
            ("Растение", "фотосинтезирует с", "солнечный свет"),
            ("Хлорофилл", "придаёт", "зелёный цвет"),
            # --- экономика и общество ---
            ("Деньги", "являются", "средство обмена"),
            ("Рынок", "определяет", "цена"),
            ("Цена", "зависит от", "спрос и предложение"),
            ("Налог", "пополняет", "бюджет"),
            ("Банк", "хранит", "вклады"),
            ("Кредит", "выдаётся под", "процент"),
            ("Инфляция", "обесценивает", "деньги"),
            ("Труд", "создаёт", "товар"),
            ("Товар", "обменивается на", "деньги"),
            ("Общество", "состоит из", "люди"),
            ("Правила", "регулируют", "общество"),
            ("Закон", "защищает", "права"),
            ("Культура", "передаётся через", "традиции"),
        ])
        # 2) Извлечение триплетов из малых текстовых корпусов (не из .py — код) 
        srcs = []
        for d in (DATA / "self_learned", DATA / "corpus_ready"):
            if d.exists():
                for f in d.glob("*.jsonl"):
                    if f.stat().st_size <= 1_000_000:
                        srcs.append(f)
        # 3) Реальный источник знаний: семплируем все значимые кластеры диалогов
        #     (ru, math, code, general, design) и извлекаем триплеты в граф.
        #     Берём ограниченные выборки — ТТЛ в JSON-форме даёт связи из текстов.
        total = 0
        for db in ("ru.jsonl", "math.jsonl", "code.jsonl", "general.jsonl", "design.jsonl"):
            src = DATA / "processed" / db
            try:
                limit = 50_000_000 if db == "ru.jsonl" else 250_000
                sample = _read_small_head(src, limit)
                if sample:
                    total += kg.from_triples(extract(_jsonl_to_text(sample)))
            except Exception:
                pass
        for f in srcs[:40]:
            try:
                head = _read_small_head(f, 8000)
                if head:
                    total += kg.from_triples(extract(head))
            except Exception:
                pass
        print(f"  Граф знаний готов: {kg.summary()} (извлечено из корпуса: {total}, из кэша: {prev_edges})")
        # Чистим мусор: шумовые предикаты («это/есть/если») и корпусные узлы-фразы,
        # чтобы граф состоял из чистых понятий и осмысленных связей
        try:
            removed = kg.prune_noise()
            if removed:
                print(f"  Убрано мусора из графа: {removed} элементов")
        except Exception:
            pass
        # Стоп-гайд графа: расширенный чёрный список узлов-связок по кластерам
        # (обрывки речи, вводные, личные обращения, интерфейсные шумы), которые
        # не являются понятиями знаний и засоряют связи.
        try:
            stop_nodes = {
                "однако", "затем", "далее", "итак", "во-первых", "во-вторых",
                "в-третьих", "наконец", "короче", "кстати", "впрочем", "хотя",
                "следовательно", "поэтому", "вероятно", "наверное", "конечно",
                "просто", "вообще", "типа", "вроде", "как-то", "ну", "вот",
                "привет", "пока", "спасибо", "пожалуйста", "добрый день",
                "извините", "простите", "давай", "давайте", "будем", "будемте",
                "читатель", "слушатель", "друг", "друзья", "ребята",
                "дальше", "далее", "наверно", "действительно", "безусловно",
                "разумеется", "правда", "в общем", "по сути", "на деле",
            }
            removed_stop = kg.prune_stopwords(stop_nodes)
            if removed_stop:
                print(f"  Стоп-гайд графа: удалено узлов-связок: {removed_stop}")
        except Exception:
            pass
        # Консолидация: зачищаем слабые рёбра и избыточные узлы-фразы, чтобы
        # плотность росла за счёт осмысленных связей, а не шума
        try:
            con_removed = kg.consolidate(min_weight=0.15, max_phrase_words=4)
            if con_removed:
                print(f"  Консолидировано графа: {con_removed} элементов")
        except Exception:
            pass
        # Дедупликация: сливаем узлы-словоформы («граф/графа/графе») в один
        try:
            dedup_removed = kg.dedupe_nodes(top_groups=150)
            if dedup_removed:
                print(f"  Узлов-дублей слито: {dedup_removed} (граф компактнее)")
        except Exception:
            pass
        # Связываем функции базы знаний с графом, чтобы «куча функций» стала
        # частью связей (каждая функция — узел с рёбрами к своим понятиям)
        try:
            from algos.knowledge_graph import build_function_links
            fn_edges = build_function_links()
            if fn_edges:
                print(f"  Связей от функций добавлено: {fn_edges}")
        except Exception:
            pass
        # Достраиваем связи между понятиями из реальных QA-пар корпуса
        try:
            from algos.knowledge_graph import build_concept_links
            cl_edges = build_concept_links(max_pairs=1500, co_min=2)
            if cl_edges:
                print(f"  Связей между понятиями из корпуса добавлено: {cl_edges}")
        except Exception:
            pass
        # Мосты между базовыми понятиями (нейросеть→обучение→алгоритм)
        try:
            from algos.knowledge_graph import build_concept_bridges
            cb_edges = build_concept_bridges()
            if cb_edges:
                print(f"  Мостов между понятиями добавлено: {cb_edges}")
        except Exception:
            pass
        # Связываем изолированные узлы-сироты с ближайшими темами
        try:
            from algos.knowledge_graph import link_orphans
            lo_edges = link_orphans(max_word_len=20, max_edges=1500)
            if lo_edges:
                print(f"  Изолированных узлов связано: {lo_edges}")
        except Exception:
            pass
        # Предсказываем недостающие связи по общим соседям
        try:
            from algos.knowledge_graph import predict_links
            pl_edges = predict_links(min_common=3, max_edges=1500, weight=0.3)
            if pl_edges:
                print(f"  Предсказано недостающих связей: {pl_edges}")
        except Exception:
            pass
        # Семантический мост: сращиваем изолированные узлы с компонентами сети
        try:
            from algos.knowledge_graph import kg as _kgb
            br_edges = _kgb.bridge_components(max_edges=1500, weight=0.25, sample_conn=40000)
            if br_edges:
                print(f"  Семантических мостов к изолированным узлам: {br_edges}")
        except Exception:
            pass
        # Нормализация узлов-фраз: извлекаем чистые понятия, связываем фразы с ними
        try:
            from algos.knowledge_graph import kg as _kgn
            norm_added = _kgn.normalize_nodes(max_phrase_words=4, weight=0.4)
            if norm_added:
                print(f"  Нормализовано узлов в понятия: {norm_added}")
        except Exception:
            pass
        # Сохраняем граф на диск, чтобы знания не терялись при перезапуске
        try:
            kg.save(gpath)
        except Exception:
            pass
        # Связываем нульмерный граф со знаниевым — и печатаем метрику роста понимания
        try:
            from algos.zero_dimensional import set_kg as _zd_set, growth_report
            _zd_set(kg)
            print("  " + growth_report(kg))
        except Exception:
            pass
    except Exception as e:
        print(f"  (граф знаний пропущен: {e})")
    return None


def _read_small_head(path, limit):
    """Читает первые `limit` символов файла (utf-8, с запасом). Один return: str."""
    text = ""
    try:
        with open(str(path), "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read(limit)
    except Exception:
        text = ""
    return text


def _jsonl_to_text(chunk):
    """Превращает кусок JSONL (строки вида {\"instruction\":...}) в чистый текст.
    Из каждого example берём instruction и output, чтобы ТТЛ-извлечение могло
    вытащить триплеты. Один return: str."""
    import json as _json
    parts = []
    for line in chunk.splitlines():
        try:
            ex = _json.loads(line)
            merged = (ex.get("instruction", "") + ". " + ex.get("output", "")).strip()
            if merged:
                parts.append(merged)
        except Exception:
            pass
    return "\n".join(parts)


def _port_is_busy(host, port):
    """Слушает ли кто-то уже этот порт. Один return: bool.

    На Windows две копии Mirro спокойно биндятся на один порт (SO_REUSEADDR)
    и начинают делить запросы: часть висит, часть уходит не туда.
    Поэтому второй экземпляр лучше не запускать вовсе."""
    check_host = "127.0.0.1" if host in ("0.0.0.0", "", None) else host
    try:
        socket.create_connection((check_host, int(port)), timeout=0.5).close()
        is_busy = True
    except OSError:
        is_busy = False
    return is_busy


def _load_algorithms_in_background():
    """Индекс TF-IDF (208 МБ) грузится в фоне: сервер начинает отвечать раньше.
    Запросы, которым индекс реально нужен, дождутся его сами."""
    def _run():
        try:
            # Даём серверу сначала ответить на /health, потом занимаем GIL
            import time as _t
            _t.sleep(10)
            sys.path.insert(0, str(MIRRO_HOME))
            from scripts.algorithms import algo
            stats = algo.status()
            print("  Индекс готов: %s примеров, %s слов" % (stats.get("examples"), stats.get("vocab")),
                  flush=True)
        except Exception:
            pass
    try:
        import threading as _th
        _th.Thread(target=_run, daemon=True, name="mirro-index").start()
    except Exception:
        pass


def _load_graph_only():
    """Поднимает сохранённый граф знаний (быстро), без наполнения. Один return: None."""
    try:
        from algos.knowledge_graph import kg
        kg.load(MODELS / "knowledge_graph.pkl")
    except Exception:
        pass


def _seed_in_background():
    """Наполнение графа — в фоне: 78 с на старте не должен ждать пользователь."""
    def _run():
        try:
            # Индекс стартует через 10 с, наполнение — через 20, чтобы не душили друг друга
            import time as _t
            _t.sleep(20)
            _seed_knowledge_graph()
        except Exception:
            pass
    try:
        import threading as _th
        _th.Thread(target=_run, daemon=True, name="mirro-seed").start()
    except Exception:
        pass


def _warm_imports():
    """Фоновый прогрев тяжёлых импортов: первый вопрос не должен ждать
    разбора english_kb (3 МБ исходника) и русских описаний."""
    def _load():
        import threading, time as _t
        # сервер должен начать отвечать раньше, чем начнётся разбор 3 МБ словаря
        _t.sleep(12)
        try:
            from algos import answer_router, ru_bridge, concepts
            from algos.english_kb import try_english
            from algos.ru_descriptions import RU_TEXT
            concepts.build()
            answer_router.candidates("прогрев")
            ru_bridge.bridge("что такое память")
            try_english("what is memory?")
        except Exception:
            pass
    try:
        import threading as _th
        _th.Thread(target=_load, daemon=True, name="mirro-warmup").start()
    except Exception:
        pass


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if _port_is_busy(HOST, PORT):
        print(f"Порт {PORT} уже занят другим экземпляром Mirro — второй не запускаю.")
        print("  Остановите текущий (mirro_launcher.pyw) или задайте MIRRO_PORT.")
        sys.exit(2)
    print("MIRRO v0.3 - Единая нейросеть знаний")
    print(f"  API: http://{HOST}:{PORT}")
    print(f"  Загружено: {core.stats['total_examples']} примеров")
    for cl, info in core.get_cluster_info().items():
        print(f"    {cl:12} {info['examples']:>6} примеров · {info['desc']}")
    print("\n  Индекс алгоритмов грузится в фоне (208 МБ, не блокирует старт)")
    # Граф поднимаем сразу (2 с), а наполнение уходит в фон: 78 с ожидания
    # у кнопки «запустить» — слишком много
    _load_graph_only()
    print("  Движок мышления: подфункции single return, юмор, схемы Босовой, граф знаний")
    print("\n  Запуск автономного обучения (каждые 60 мин)...")
    autonomous_learning_loop(interval_sec=3600)
    print("  Запуск внутренней речи (mindstream, каждые 30 мин)...")
    try:
        mindstream_loop(interval_sec=1800)
        from algos.mindstream import mind as _mind
        _mind.observe("Mirro запустилась и думает о себе")
    except Exception as _mse:
        print(f"  [медитация] не удалось стартовать: {_mse}")
    server = ThreadingHTTPServer((HOST, PORT), MirroAPI)
    _load_algorithms_in_background()
    _warm_imports()
    _seed_in_background()
    print(f"\n  → Слушаю на http://{HOST}:{PORT}")
    print("  → Доступ:\n" + _access_addresses())
    try: server.serve_forever()
    except KeyboardInterrupt: print("\n  Mirro остановлен."); server.server_close()

if __name__ == "__main__":
    main()