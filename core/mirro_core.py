# -*- coding: utf-8 -*-
import json, os, time, random, re as _re, sys
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
        _lite = os.environ.get("MIRRO_LITE", "").strip().lower() in ("1", "true", "yes", "on")
        cap = 100_000 if _lite else None
        for f in self.processed_dir.glob("*.jsonl"):
            n = 0
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        try: self.knowledge_base[f.stem].append(json.loads(line))
                        except: pass
                        n += 1
                        if cap and n >= cap:
                            break
        self.stats["total_examples"] = sum(len(v) for v in self.knowledge_base.values())
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
        with open(LOGS / "calls.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _datetime.utcnow().isoformat(), "cluster": cluster, "provider": provider, "latency_ms": latency_ms, "success": success, "prompt_len": len(prompt)}, ensure_ascii=False) + "\n")
        # ТОП-вопросов: считаем нормализованные запросы (ТОП-30)
        self.stats.setdefault("top_questions", {})
        q = " ".join(prompt.split())[:60].lower()
        if q:
            self.stats["top_questions"][q] = self.stats["top_questions"].get(q, 0) + 1
            # держим не более 30 ключей — отсекаем самый редкий
            if len(self.stats["top_questions"]) > 30:
                rare = min(self.stats["top_questions"], key=self.stats["top_questions"].get)
                self.stats["top_questions"].pop(rare, None)
        self._save_json(CORE / "stats.json", dict(self.stats))
    def get_cluster_info(self):
        return {name: {**info, "examples": len(self.knowledge_base.get(name, [])), "calls": self.stats["clusters_used"].get(name, 0)} for name, info in KNOWLEDGE_CLUSTERS.items()}
    def status(self):
        try:
            sys.path.insert(0, str(MIRRO_HOME))
            from scripts.providers import status as _pv_status
            prov = _pv_status()
        except Exception:
            prov = {}
        return {"name": "Mirro", "version": "0.3", "total_calls": self.stats["calls"], "total_examples": self.stats["total_examples"], "providers": prov, "clusters": self.get_cluster_info(), "api": f"http://{HOST}:{PORT}/v1/chat/completions"}
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
                    merged["updated"] = _datetime.utcnow().isoformat()
                    MODEL_STATE_FILE.write_text(json.dumps(merged, ensure_ascii=False), "utf-8")
                except: pass
            except Exception as e: print(f"  [автообучение] ошибка: {e}")
            time.sleep(interval_sec)
    t = threading.Thread(target=_loop, daemon=True); t.start(); return t

# ========== REASONING ENGINE ==========
# Чистая логика вынесена в scripts/reasoning_engine.py (легко тестировать без
# построения индекса в память). Здесь только аккуратный локальный импорт.
def _reasoning():
    sys.path.insert(0, str(MIRRO_HOME))
    from scripts.reasoning_engine import score_candidate, choose_best, _tokenize
    return score_candidate, choose_best, _tokenize

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
    for keys, fn in topics.items():
        if any(k in q for k in keys):
            return fn(q)
    return None

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
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.voice import try_jarvis as _try_jarvis
        return _try_jarvis(query)
    except Exception:
        return None

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
    if any(w in q for w in ["кто ты", "что ты такое", "ты кто", "представься", "твоё имя"]):
        return _DIALOG_REPLIES["who"]
    if any(w in q for w in ["ты программа", "ты бот", "ты компьютерная программа",
                            "ты живая", "ты настоящая", "ты робот", "ты искусственный интеллект",
                            "ты нейросеть"]):
        return _DIALOG_REPLIES["program"]
    if q.strip() in ("программа", "программу", "что такое программа"):
        return _DIALOG_REPLIES["program"]
    if any(w in q for w in ["что ты умеешь", "что умеешь", "твои возможности", "на что способна"]):
        return _DIALOG_REPLIES["can"]
    if any(w in q for w in ["как ты учишься", "как учишься", "как обучаешься", "как запоминаешь"]):
        return _DIALOG_REPLIES["learn"]
    if any(w in q for w in ["как ты", "как твои дела", "как настроение", "ты в порядке"]):
        return _DIALOG_REPLIES["howami"]
    if any(w in q for w in ["статус", "всё ли в порядке", "ты работаешь"]):
        return _DIALOG_REPLIES["status"]
    if _is_news_query(q):
        return _DIALOG_REPLIES["news"]
    if any(w in q for w in ["ответишь на русском", "говори по-русски", "по русски",
                            "на русском", "русский язык", "по-русски"]):
        return _DIALOG_REPLIES["language"]
    if any(w in q for w in ["меня не устраивает твой ответ", "ответ как человек",
                            "как бы ответил человек", "ответь нормально", "ответь по-человечески",
                            "ответь как человек", "не то", "не то ответил", "плохой ответ", "ерунда", "не понравился твой ответ"]):
        return _DIALOG_REPLIES["quality"]
    if any(w in q for w in ["не отвечаешь на вопрос", "не ответил", "не отвечаешь",
                            "не отвечаешь про себя", "игнорируешь мой вопрос",
                            "отвечай на вопрос", "не отвечаешь на мой вопрос"]):
        return _DIALOG_REPLIES["not_answering"]
    # Советы о карьере/выборе/работе — это разговор, а не технический запрос о
    # фрилансе/конторе как теме из базы. Отвечаем осмысленно, а не фрагментом.
    if any(w in q for w in ["стоит ли", "какой выбрать", "что выбрать", "подскажи как",
                            "посоветуй", "совет по", "как начать", "с чего начать",
                            "лучше для", "чем заниматься", "идти в разработку",
                            "работать на себя", "фриланс или", "учиться на"]):
        return _DIALOG_REPLIES["advice"]
    if q.startswith("какой ") and "лучше" in q:
        return _DIALOG_REPLIES["advice"]
    if any(w in q for w in ["спасибо", "благодарю", "спс"]):
        return _DIALOG_REPLIES["thanks"]
    if any(w in q for w in ["пока", "до свидания", "до встречи", "прощай"]):
        return _DIALOG_REPLIES["bye"]
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

def try_provider(query, context=""):
    """Финальный фоллбэк: внешний ИИ-провайдер (DeepSeek и др.), если всё остальное не ответило.

    context — история диалога; провайдеру передаётся, чтобы он учитывал
    предыдущие реплики и не терял нить разговора.
    """
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.providers import fallback
        return fallback(query, system=context or None)
    except: pass
    return None


def answer_looks_bad(query, answer):
    """True, если ответ мусорный — его нельзя отдавать пользователю.
    Один return: bool."""
    bad = False
    if not answer or len(answer) < 10:
        bad = True
    else:
        # Ответ похож на код (PHP/JS/C++/SQL) — а вопрос фактологический
        code_markers = ["<?php", "function ", "std::", "#include", "import ", "class ", "=>", "console.", "npm ", "git ", "def "]
        code_hits = sum(1 for m in code_markers if m in answer)
        if code_hits >= 2:
            bad = True
        else:
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
                    bad = True  # ответ вообще не про это
    return bad


def _provider_help_hint():
    """Подсказка, когда внешний провайдер недоступен (нет ключа)."""
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.providers import status as _pv_status
        if any(_pv_status().values()):
            return ""  # провайдер настроен — не морочим голову
    except Exception:
        pass
    return (" Подсказка: чтобы я отвечала на такие вопросы, добавь ключ DeepSeek. "
            "Положить его сюда: core/providers_secret.json "
            '(формат {"deepseek": "sk-..."}) или задать переменную DEEPSEEK_API_KEY.)')


def _voice(raw, query, strategy="base"):
    """Обернуть сырой ответ в голос Mirro (свои слова, характер)."""
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from scripts.voice import speak
        return speak(raw, query, strategy)
    except Exception:
        return raw


def try_bosova_engine(prompt):
    """Выполнимые алгоритмы по правилам Босовой: арифметика по конструкциям
    ЕСЛИ/ТО/ЦИКЛ ПОКА, схемы мышления, тройственное рассуждение «нейрон-нигде».
    Возвращает готовый ответ или None, если вопрос не подходит."""
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from algos.bosova_engine import применить
        res = применить(prompt)
        if not res:
            return None
        return res["answer"]
    except Exception:
        return None


def _try_direct_handlers(prompt):
    """Перебирает быстрые стратегии (приветствие, обучение, мышление, юмор,
    творчество, Джарвис, диалог, босовские алгоритмы) и возвращает первый
    подошедший ответ. Единственный return: dict-ответ или None."""
    # Ленивые импорты новых граф/память/вывод-модулей (как принято в этом файле)
    import sys as _sys
    if str(MIRRO_HOME) not in _sys.path:
        _sys.path.insert(0, str(MIRRO_HOME))
    def try_knowledge_graph(q):
        try:
            from algos.knowledge_graph import try_knowledge_graph as _f
            return _f(q)
        except Exception:
            return None
    def try_graph_infer(q):
        try:
            from algos.graph_infer import try_graph_infer as _f
            return _f(q)
        except Exception:
            return None
    def try_dialogue_memory(q):
        try:
            from algos.dialogue_memory import try_dialogue_memory as _f
            return _f(q)
        except Exception:
            return None
    def try_zero_dim(q):
        try:
            from algos.zero_dimensional import try_zero_dim as _f
            return _f(q)
        except Exception:
            return None
    def try_growth(q):
        try:
            from algos.zero_dimensional import try_growth as _f
            return _f(q)
        except Exception:
            return None
    def try_neuromod(q):
        try:
            from algos.neuromodulators import try_neuromod as _f
            return _f(q)
        except Exception:
            return None
    def try_enrich(q):
        try:
            from algos.knowledge_graph import try_enrich as _f
            return _f(q)
        except Exception:
            return None
    def try_what_links(q):
        try:
            from algos.knowledge_graph import try_what_links as _f
            return _f(q)
        except Exception:
            return None
    def try_similar(q):
        try:
            from algos.knowledge_graph import try_similar as _f
            return _f(q)
        except Exception:
            return None
    def try_function_knowledge(q):
        try:
            from algos.module_knowledge import try_function_knowledge as _f
            return _f(q)
        except Exception:
            return None
    def try_evo(q):
        try:
            from algos.evolve import try_evolve as _f
            return _f(q)
        except Exception:
            return None
    def try_neural_elec(q):
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
            return ans
        except Exception:
            return None
    handlers = [
        ("greeting", try_greetings),
        ("learn", try_learn),
        ("think", try_algos_think),
        ("humor", try_humor),
        ("creative", try_creative),
        ("direct", try_jarvis),
        ("dialog", try_dialog),
        ("algo", try_bosova_engine),
        ("ai_history", try_ai_history),
        ("knowledge_graph", try_knowledge_graph),
        ("graph_infer", try_graph_infer),
        ("enrich", try_enrich),
        ("what_links", try_what_links),
        ("similar", try_similar),
        ("func_kb", try_function_knowledge),
        ("evolve", try_evo),
        ("dialogue_memory", try_dialogue_memory),
        ("zero_dim", try_zero_dim),
        ("growth", try_growth),
        ("neuromod", try_neuromod),
        ("neural_elec", try_neural_elec),
    ]
    result = None
    for strategy, fn in handlers:
        try:
            msg = fn(prompt)
        except Exception:
            msg = None
        if msg is not None:
            result = {"content": msg, "strategy": strategy}
            break
    return result


def _enrich_followup(prompt, context):
    """Если реплика слишком короткая и без своей темы, обогащает её словами из
    истории диалога, чтобы поиск не ушёл в мусор. Единственный return: str."""
    q_words = set(_tokenize_for_search(prompt))
    content_words = {w for w in q_words if w not in _DIALOG_STOPWORDS}
    enriched = prompt
    if len(content_words) < 2 and context:
        hist_words = set()
        for line in context.split("\n"):
            for w in _tokenize_for_search(line.replace("Пользователь:", " ").replace("Mirro:", " ")):
                if w not in _DIALOG_STOPWORDS:
                    hist_words.add(w)
        enrichment = " ".join(sorted(hist_words)[:60])
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
            web_first = try_web(prompt)
            if web_first:
                result = {"content": _voice(web_first, prompt, "web"), "strategy": "web"}
    except Exception:
        result = None
    return result


def _search_best(prompt, cluster):
    """TF-IDF → RAG → выбор лучшего кандидата по кластеру.
    Единственный return: кортеж (best_answer, best_score, has_result)."""
    results = try_tfidf(prompt, cluster)
    if not results:
        results = try_rag(prompt, cluster)
    _, choose_best, _ = _reasoning()
    best_answer, best_score, _reason = choose_best(prompt, results, preferred=cluster)
    has_result = best_answer is not None and best_score > 1.0
    return best_answer, best_score, has_result


def _voice_or_none(raw, prompt, strategy):
    """Оборачивает ответ в голос Мирро. Единственный return: dict-ответ или None."""
    result = None
    if raw:
        result = {"content": _voice(raw, prompt, strategy), "strategy": strategy}
    return result


def _fallback_chain(prompt):
    """Финальная цепочка: веб → провайдер → подсказка. Единственный return: dict."""
    web_answer = try_web(prompt)
    if web_answer:
        result = {"content": _voice(web_answer, prompt, "web"), "strategy": "web"}
    else:
        provider_answer = try_provider(prompt)
        if provider_answer:
            result = {"content": provider_answer[:2500], "strategy": "provider"}
        else:
            hint = _provider_help_hint()
            result = {"content": "Не нашла это ни в базе, ни в интернете. Переформулируй вопрос." + hint, "strategy": "unknown"}
    return result


def build_response(prompt, cluster, context=""):
    """Построить ответ. prompt — актуальный вопрос, context — история диалога.
    Единственный return: dict-ответ."""
    result = {"content": f"[Mirro] Внутренняя ошибка: произошла ошибка", "strategy": "error"}
    try:
        direct = _try_direct_handlers(prompt)
        if direct is not None:
            result = direct
            result["workspace"] = "сознание: локальный триггер (рабочее пространство = одна память)"
        else:
            prompt = _enrich_followup(prompt, context)
            web_first = _try_web_first(prompt)
            if web_first is not None:
                result = web_first
                result["workspace"] = "сознание: веб-триггер свежести (GNWT: свежая внешняя трансляция)"
            else:
                best_answer, best_score, has_result = _search_best(prompt, cluster)
                if has_result and answer_looks_bad(prompt, best_answer):
                    bad_web = try_web(prompt)
                    if bad_web:
                        result = _voice_or_none(bad_web, prompt, "web")
                        result["workspace"] = "сознание: база мусорная → веб (GNWT: смена рабочего пространства)"
                    else:
                        result = {"content": "Не нашла нормального ответа в базе, а в интернете — пока недоступен. Переформулируй вопрос.", "strategy": "web"}
                        result["workspace"] = "сознание: пустое рабочее пространство (ни база, ни веб)"
                elif not has_result and cluster in ("ru", "knowledge"):
                    cl_web = try_web(prompt)
                    result = _voice_or_none(cl_web, prompt, "web") or _fallback_chain(prompt)
                    result["workspace"] = "сознание: нет в базе — переход к вебу/провайдеру (GNWT: расширение пространства)"
                elif has_result:
                    result = {"content": _voice(best_answer, prompt, "base")[:2500], "strategy": "base"}
                    result["workspace"] = f"сознание: база знаний (рабочее пространство кластера {cluster}, IIT-связность)"
                else:
                    result = _fallback_chain(prompt)
                    result["workspace"] = result.get("strategy", "unknown") + ": сознание — финальный резерв (провайдер/веб)"
    except Exception as e:
        result = {"content": f"[Mirro] Внутренняя ошибка: {e}", "strategy": "error"}
    return result

def try_ai_history(prompt):
    """Справочник «рост понимания: нейрочеловек и ИИ» (Тьюринг, Шеннон, Питтс,
    Хебб, Розенблатт, IIT, GNWT и др.) — с авторами в записях. Один return:
    str-ответ или None."""
    try:
        sys.path.insert(0, str(MIRRO_HOME))
        from algos.knowledge_ai_history import применить as _ai_hist
        return _ai_hist(prompt)
    except Exception:
        return None


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
    def _authorized(self):
        """Проверяет токен доступа. Один return: bool.

        Пропускает, если AUTH_TOKEN пуст (локальный режим). Иначе сверяет
        заголовок Authorization: Bearer <token> или query-параметр ?token=.
        """
        if not AUTH_TOKEN:
            return True
        supplied = ""
        auth = self.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            supplied = auth[7:].strip()
        if not supplied:
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            supplied = (qs.get("token") or [""])[0]
        return supplied == AUTH_TOKEN
    def _require_auth(self):
        """Если токен неверен — пишет 401. Один return: bool (разрешено)."""
        if self._authorized():
            return True
        self._json({"error": "unauthorized"}, 401)
        return False
    def _route_path(self):
        """Путь без query-параметров (для маршрутизации). Один return: str."""
        try:
            from urllib.parse import urlsplit
            return urlsplit(self.path).path or "/"
        except Exception:
            return self.path.split("?", 1)[0]
    def do_GET(self):
        if not self._require_auth():
            return
        route = self._route_path()
        if route in ("/", "/index.html"):
            if self._serve_file(MIRRO_HOME / "web" / "index.html", "text/html; charset=utf-8"): return
        elif route == "/meysto-neiroset.html":
            if self._serve_file(MIRRO_HOME / "web" / "meysto-neiroset.html", "text/html; charset=utf-8"): return
        elif route == "/mirro-evolve.html":
            if self._serve_file(MIRRO_HOME / "web" / "mirro-evolve.html", "text/html; charset=utf-8"): return
        elif route == "/catalog.json":
            if self._serve_file(DATA / "catalog_phase1.json", "application/json; charset=utf-8"): return
        elif route == "/health":
            status = core.status()
            try: status["algorithms"] = _grab_algo().status()
            except: status["algorithms"] = {}
            # нейро: медиаторы + граф знаний для дашборда
            try:
                from algos.neuromodulators import nm as _nm
                from algos.knowledge_graph import kg as _kg
                from algos.zero_dimensional import dimension_of_understanding as _dimen
                st = status.get("algorithms", {})
                st["neuromodulators"] = dict(_nm.level)
                st["neuromodulators"]["rhythm"] = _nm.rhythm_state()
                st["knowledge_graph"] = {
                    "nodes": len(_kg.nodes), "edges": len(_kg.edges),
                    "avg_dimension": _dimen(_kg),
                }
                status["algorithms"] = st
            except Exception:
                pass
            self._json(status); return
        elif route == "/v1/models":
            t = int(time.time())
            self._json({"object": "list", "data": [
                {"id": "mirro/default", "object": "model", "created": t, "owned_by": "mirro"},
                {"id": "mirro/ru", "object": "model", "created": t, "owned_by": "mirro"},
            ]}); return
        elif route == "/v1/top-questions":
            top = core.stats.get("top_questions", {})
            ranked = sorted(top.items(), key=lambda x: -x[1])[:15]
            self._json({"questions": [{"q": q, "count": c} for q, c in ranked]}); return
        elif route == "/v1/evolve":
            # Эволюционный отбор: шаг нейроэволюции популяции графов
            try:
                from algos.evolve import get_evolver, _default_A, _default_X, report
                ev = get_evolver()
                from urllib.parse import parse_qs, urlsplit
                pq = parse_qs(urlsplit(self.path).query)
                steps = int(pq.get("steps", ["1"])[0])
                rr = None
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
                           "report": report()}
                self._json(payload); return
            except Exception as e:
                self._json({"error": str(e)}, 500); return
        elif route == "/v1/learn-report":
            self._json(self._learn_report()); return
        elif route == "/v1/knowledge":
            # Умные запросы знаниевого графа: enrich / what_links / similarity
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
                    payload["answer"] = _fk(query) if query else f"база знаний по функциям: готова"
                else:
                    payload["answer"] = []
                self._json(payload); return
            except Exception as e:
                self._json({"error": str(e)}, 500); return
        self._json({"error": "not found"}, 404)

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
        # Соответствие весов формату «Мозг Мирро» в Мейсто (f0..f3) — если MLP,
        # отдаём и выходные h*_out, и плоские f* для простого предсказания.
        return report
    def _chat_payload(self, messages, model, response, prompt):
        """Формирует итоговый JSON-ответ (не-SSE). Единственный return: dict."""
        content = response.get("content", "") if response else "Ошибка"
        return {"id": f"mirro-{int(time.time())}", "object": "chat.completion", "model": model,
                "usage": {"prompt_tokens": len(prompt)//4, "completion_tokens": len(content)//4},
                "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}]}

    def _handle_chat(self, body):
        """Обрабатывает POST /v1/chat/completions. Единственный return: None.

        Пишет ответ клиенту (SSE или JSON) внутри. Не возвращает значение."""
        messages = body.get("messages", [])
        model = body.get("model", "mirro/default")
        stream = body.get("stream", False)
        if not messages:
            self._json({"error": "no messages"}, 400)
            return None
        conversation = []
        last_user = ""
        for m in messages:
            role = (m.get("role") or "").lower()
            content = (m.get("content") or "").strip()
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
        except: pass
        if response:
            core.log_call(prompt, cluster, f"mirro-{response.get('strategy','ai')}", int((time.time()-t0)*1000), True)
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
            payload = self._chat_payload(messages, model, response, prompt)
            self._json(payload)
        return None

    def do_POST(self):
        if not self._require_auth():
            return
        route = self._route_path()
        if route == "/v1/chat/completions":
            try: body = self._read()
            except: return self._json({"error": "bad request"}, 400)
            self._handle_chat(body)
            return
        elif route == "/v1/feedback":
            try:
                body = self._read(); algo = _grab_algo()
                algo.train_from_feedback(body.get("query",""), body.get("response",""), body.get("liked",True))
                # Обучение знаниевого графа из отклика: усиливаем/ослабляем связи понятий
                kg_note = ""
                try:
                    from algos.knowledge_graph import kg as _kg, _clean_q, _pair_from
                    q = _clean_q(body.get("query",""))
                    a, b = _pair_from(q)
                    if a and b:
                        if body.get("liked", True):
                            n = _kg.reward(a, b, 0.25)
                        else:
                            n = _kg.punish(a, b, 0.25)
                        if n:
                            _kg.save(MODELS / "knowledge_graph.pkl")
                            kg_note = f", graph_grown={n}"
                except Exception:
                    kg_note = ""
                self._json({"status": "ok" + kg_note})
            except Exception as e: self._json({"status": "error", "message": str(e)}, 500)
            return
        elif route == "/v1/self-learn":
            try:
                algo = _grab_algo(); n = min(50, len(algo.examples)); learned = 0
                for inst, out, cl in algo.examples[::max(1, len(algo.examples)//n)][:n]:
                    if len(inst) < 10: continue
                    ans = algo.compose_answer(inst, top_n=3)
                    if ans and algo.qa_score(inst, ans) > 0.5: learned += 1
                self._json({"status": "ok", "learned": learned, "checked": n})
            except Exception as e: self._json({"status": "error", "message": str(e)}, 500)
            return
        elif route == "/v1/brain-eval":
            # Оценка паспорта/пары на НАСТОЯЩЕМ MLP-перцептроне Мирро
            # (в отличие от локальной заглушки весов в браузере).
            try:
                body = self._read(); algo = _grab_algo()
                q = body.get("query", "") or ""; c = body.get("candidate", "") or ""
                if not c: c = body.get("candidate", "")
                score = algo.perceptron_predict(q, c) if (q or c) else 0.5
                self._json({"status": "ok", "score": round(float(score), 4),
                            "trained": bool(getattr(algo, "perceptron_trained", False))})
            except Exception as e: self._json({"status": "error", "message": str(e)}, 500)
            return
        self._json({"error": "not found"}, 404)
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
    if HOST in ("0.0.0.0", ""):
        lan = _lan_ip()
        return (f"Локально:  http://127.0.0.1:{PORT}\n"
                f"По сети (WiFi/модем): http://{lan}:{PORT}")
    return f"Только локально: http://127.0.0.1:{PORT}"

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
    try:
        with open(str(path), "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(limit)
    except Exception:
        return ""


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


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("MIRRO v0.3 - Единая нейросеть знаний")
    print(f"  API: http://{HOST}:{PORT}")
    print(f"  Загружено: {core.stats['total_examples']} примеров")
    for cl, info in core.get_cluster_info().items():
        print(f"    {cl:12} {info['examples']:>6} примеров · {info['desc']}")
    print("\n  Инициализация алгоритмов (3-4 мин)...")
    sys.path.insert(0, str(MIRRO_HOME))
    from scripts.algorithms import algo
    st = algo.status()
    print(f"  Индекс: {st['examples']} примеров, {st['vocab']} слов")
    # Автонаполнение знаниевого графа: маленькие кластеры + self_learned + история ИИ
    _seed_knowledge_graph()
    print("  Движок мышления: подфункции single return, юмор, схемы Босовой, граф знаний")
    print("\n  Запуск автономного обучения (каждые 60 мин)...")
    autonomous_learning_loop(interval_sec=3600)
    server = ThreadingHTTPServer((HOST, PORT), MirroAPI)
    print(f"\n  → Слушаю на http://{HOST}:{PORT}")
    print("  → Доступ:\n" + _access_addresses())
    try: server.serve_forever()
    except KeyboardInterrupt: print("\n  Mirro остановлен."); server.server_close()

if __name__ == "__main__":
    main()