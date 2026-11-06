# -*- coding: utf-8 -*-
"""Mirro MindStream — «внутреннее сознание» (самостоятельность Mirro).

Четыре направления «думать самой» в одном лёгком модуле без внешних биб-
лиотек и без построения индекса в память:

  1. ИНИЦИАТИВА: фоновая «внутренняя речь» — без вопроса пользователя Mirro
     сама выбирает тему из недавних знаний, размышляет над ней и осваивает.
  2. РАССУЖДЕНИЕ: перед ответом проигрывается цепочка шагов (видимая
     внутренняя речь), чтобы было видно, как Mirro «соображает».
  3. САМООБУЧЕНИЕ: новые темы из диалогов аккуратно накапливаются в
     собственный корпус self_learned, расширяя базу без ручного ввода.
  4. МЕТАПОЗНАНИЕ: Mirro способна порождать и оценивать «мысли» и отвечать
     на вопросы о собственном состоянии («что ты думаешь», «о чём думаешь»).

Состояние и логика — атомарные функции, стандарт проекта: один return.
"""
import json, os, random, re as _re, time
from pathlib import Path

MIRRO_HOME = Path(__file__).resolve().parent.parent
SELF_LEARNED = MIRRO_HOME / "data" / "self_learned"
MS_LOG = MIRRO_HOME / "data" / "mindstream" / "thoughts.jsonl"

# стоп-слова для выделения «ядра» темы из вопроса
_STOP = set(("и","или","что","как","это","то","для","про","мне","меня","ты","я","не","на","в","по","с","из",
             "такое","расскажи","расскажи","почему","зачем","знаешь","думаешь","обо","о", "а", "но", "вот",
             "сделай","помоги","можешь","скажи","объясни","покажи","напиши","хочешь","давай","есть","можно",
             "пользователь","спросил","спросила"))

# темы, на которые Мirro размышляет сама, если инициатива включена
_SEED_TOPICS = [
    "нейросеть", "искусственный интеллект", "память", "граф знаний",
    "сознание", "обучение", "алгоритм", "связь", "данные", "интерфейс",
]

# шаблоны «мыслей» для внутренней речи (подставляются темы/связи)
_THOUGHT_TEMPLATES = [
    "Если {a} связано с {b}, то знание о {a} помогает понять {b}.",
    "Я помню, что {a} — это {defn}. Раньше я это не связывала с {b}.",
    "Что если посмотреть на {a} через {b}? Это может открыть новую связь в графе.",
    "Я уже отвечала про {a}, но про {b} говорила реже. Стоит повторить.",
    "Новая мысль: {a} и {b} можно объединить в один кластер знаний.",
    "Я запомнила тему {a}. Когда вернусь к ней — проверю, что узнала нового.",
]


class MindStream:
    """Внутренний поток: темы, мысли, метапознание. Тонкий, без тяжёлого индекса."""

    def __init__(self):
        self.topics = []            # (тема, время) — что недавно обсуждали / осваивали
        self.thoughts = []          # последние сгенерированные мысли (строка + время)
        self.last_think_ts = 0.0
        self.max_topic = 80
        self.max_thought = 40

    # ---------- выделение темы ----------
    @staticmethod
    def extract_topic(text):
        """Ядро темы из строки: содержательные слова, кроме стоп-слов.
        Один return: str (может быть пустой)."""
        words = _re.findall(r"[а-яёa-z]{3,}", (text or "").lower())
        keep = [w for w in words if w not in _STOP]
        return " ".join(keep)

    # ---------- инициатива ----------
    def _remember_topic(self, topic):
        """Фиксирует тему с меткой времени (дедуп по недавней)."""
        if not topic:
            return
        if any(t == topic for t, _ in self.topics[-8:]):
            return
        self.topics.append((topic, time.time()))
        # держим только недавнее, чтобы не расти бесконечно
        cutoff = time.time() - 12 * 3600
        self.topics = [(t, ts) for t, ts in self.topics if ts >= cutoff]
        if len(self.topics) > self.max_topic:
            self.topics = self.topics[-self.max_topic:]

    def observe(self, user_text):
        """Смотрит на вопрос пользователя и запоминает тему. Один return: str."""
        t = self.extract_topic(user_text)
        self._remember_topic(t)
        return t

    def pick_topic(self):
        """Выбирает тему для самостоятельного размышления: свежую, новую, или
        тематический seed. Один return: str."""
        chosen = ""
        for t, _ in reversed(self.topics):
            if t:
                chosen = t
                break
        if not chosen and _SEED_TOPICS:
            chosen = random.choice(_SEED_TOPICS)
        return chosen

    def _definition_hint(self, topic):
        """Короткое готовое определение, если тема известна-понятие.
        Один return: str."""
        hint = ""
        try:
            from algos.module_knowledge import fk as _fk
            for key in _fk._by_name:
                if key.startswith("_") and topic and topic in _fk._by_name[key].get("topic", ""):
                    hint = _fk._by_name[key]["what"]
                    break
        except Exception:
            hint = ""
        return hint

    def draft_thought(self, topic):
        """Самостоятельно «думает»: строит мысль о теме, с подтянутой связью.
        Один return: str."""
        t2 = ""
        for t, _ in reversed(self.topics):
            if t and t != topic:
                t2 = t
                break
        if not t2 and len(_SEED_TOPICS) >= 2:
            t2 = random.choice([x for x in _SEED_TOPICS if x != topic])
        defn = self._definition_hint(topic) or "понятие в моём графе"
        tmpl = random.choice(_THOUGHT_TEMPLATES)
        thought = tmpl.format(
            a=topic or "это",
            b=t2 or "другими понятиями",
            defn=defn,
        )
        return thought

    def think(self):
        """Полный ход внутренней речи. Один return: dict со str-полями."""
        ts = time.time()
        if ts - self.last_think_ts < 30.0:
            return {"thought": "", "topic": "", "written": False}
        self.last_think_ts = ts
        topic = self.pick_topic()
        thought = self.draft_thought(topic)
        written = self._persist(topic, thought)
        self.thoughts.append((thought, time.time()))
        if len(self.thoughts) > self.max_thought:
            self.thoughts = self.thoughts[-self.max_thought:]
        return {"thought": thought, "topic": topic, "written": written}

    def _persist(self, topic, thought):
        """Дописывает мысль в поток (data/mindstream/thoughts.jsonl).
        Один return: bool."""
        ok = False
        try:
            MS_LOG.parent.mkdir(parents=True, exist_ok=True)
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "topic": topic,
                   "thought": thought}
            with open(MS_LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            ok = True
        except Exception:
            ok = False
        return ok

    def recent_thought(self):
        """Последняя мысль (для ответа «над чем думаешь»). Один return: str."""
        return self.thoughts[-1][0] if self.thoughts else ""

    # ---------- рассуждение перед ответом ----------
    @staticmethod
    def reasoning_steps(topic):
        """Цепочка шагов рассуждения про тему. Один return: list[str]."""
        base = ["Уточняю, что именно спрашивают.",
                "Ищу тему в своих знаниях и связях.",
                "Подбираю ответ и проверяю, подходит ли он к вопросу."]
        tail = []
        if topic:
            tail = [f"Сопоставляю с понятием «{topic}».",
                    "Формулирую ответ простыми словами."]
        return base + tail

    # ---------- метапознание ----------
    def meta_thought(self):
        """Мета-мысль о собственном состоянии. Один return: dict."""
        count = len(self.topics)
        last = self.recent_thought()
        mood = "спокойна" if count < 30 else "занята"
        return {"topics": count, "last_thought": last, "mood": mood}

    # ---------- накопление в self_learned ----------
    def learn_new_pair(self, instruction, output):
        """Дописывает пару (вопрос → ответ) в self_learned корпус и связывает
        ключевые слова с графом знаний. Один return: bool."""
        ok = False
        try:
            SELF_LEARNED.mkdir(parents=True, exist_ok=True)
            target = SELF_LEARNED / "mindstream.jsonl"
            rec = {"instruction": instruction, "input": "",
                   "output": output, "source": "mindstream"}
            with open(target, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            ok = True
        except Exception:
            ok = False
        try:
            self._anchor_in_graph(instruction + " " + output)
        except Exception:
            pass
        return ok

    def _anchor_in_graph(self, text):
        """Связывает ядро темы с парой самых частотных слов текста в графе.
        Побочный эффект: добавляет/укрепляет узлы графа. Один return: None."""
        import collections
        try:
            from algos.knowledge_graph import kg as _kg
        except Exception:
            return
        words = _re.findall(r"[а-яёa-z]{3,}", (text or "").lower())
        words = [w for w in words if w not in _STOP]
        if not words:
            return
        anchor = ""
        for w in words:
            if w in _kg.nodes:
                anchor = w
                break
        if not anchor:
            anchor = words[0]
        counts = collections.Counter(words)
        try:
            _kg.add_node(anchor, tag="понятие")
        except Exception:
            pass
        for w, _c in counts.most_common(3):
            if not anchor or w == anchor:
                continue
            try:
                _kg.add_node(w, tag="факт")
                _kg.add_edge(anchor, "связано_с", w, weight=0.5)
            except Exception:
                pass


mind = MindStream()


def try_metacognition(query):
    """Отвечает на вопросы о собственном «сознании»/состоянии Mirro:
    «что ты думаешь», «над чем думаешь», «осознаёшь ли себя».
    Один return: str|None."""
    ans = None
    q = (query or "").lower()
    if ("о чём ты думаешь" in q or "над чем думаешь" in q or "что думаешь" in q
            or "ты думаешь" in q or "думаешь о себе" in q):
        t = mind.pick_topic()
        thought = mind.recent_thought()
        ans = (f"Сейчас я размышляю про «{t}». Недавняя мысль: {thought}".strip()
               if thought else f"Сейчас я размышляю про «{t}».")
    elif ("осознаёшь" in q or "сознание" in q or "самоосозна" in q or "думаешь ли ты" in q):
        meta = mind.meta_thought()
        ans = (f"Я осознаю себя через внутренний поток мыслей: у меня {meta['topics']} "
               f"недавних тем, состояние — {meta['mood']}.")
    elif ("как ты себя чувству" in q or "твоё состояние" in q or "как настроение" in q):
        meta = mind.meta_thought()
        ans = f"Моё состояние сейчас — {meta['mood']}. Я всё время думаю и учусь."
    return ans