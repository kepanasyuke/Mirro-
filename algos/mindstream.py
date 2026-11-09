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
import json
import random
import re as _re
import time
from pathlib import Path

MIRRO_HOME = Path(__file__).resolve().parent.parent
SELF_LEARNED = MIRRO_HOME / "data" / "self_learned"
MS_LOG = MIRRO_HOME / "data" / "mindstream" / "thoughts.jsonl"

# стоп-слова для выделения «ядра» темы из вопроса
_STOP = set(("и","или","что","как","это","то","для","про","мне","меня","ты","я","не","на","в","по","с","из",
             "такое","расскажи","расскажи","почему","зачем","знаешь","думаешь","обо","о", "а", "но", "вот",
             "сделай","помоги","можешь","скажи","объясни","покажи","напиши","хочешь","давай","есть","можно",
             "пользователь","спросил","спросила","оно","себя","своё","вообще","просто","ведь","разве","даже"))

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
        Не-строковый вход → пусто. Один return: str (может быть пустой)."""
        if text is None or not isinstance(text, str):
            return ""
        words = _re.findall(r"[а-яёa-z]{4,}", text.lower())
        keep = [w for w in words if w not in _STOP]
        return " ".join(keep)

    # ---------- инициатива ----------
    def _remember_topic(self, topic):
        """Фиксирует тему с меткой времени (дедуп по недавней и по корню).
        Пустая/очень короткая/не-строковая тема игнорируется. Один return: None."""
        def _root(t):
            return t[:6]  # грубый корень для падежных вариантов
        if not isinstance(topic, str):
            return None
        recent = [x for x in self.topics[-8:] if isinstance(x, tuple) and len(x) >= 2]
        if topic and len(topic.split()) <= 8 \
                and not any(_root(t) == _root(topic) for t, _ in recent):
            self.topics.append((topic, time.time()))
            # держим только недавнее, чтобы не расти бесконечно
            cutoff = time.time() - 12 * 3600
            self.topics = [(t, ts) for t, ts in self.topics if ts >= cutoff]
            if len(self.topics) > self.max_topic:
                self.topics = self.topics[-self.max_topic:]
        return None

    def observe(self, user_text):
        """Смотрит на вопрос пользователя и запоминает тему.
        Не-строковый вход нормализуется. Один return: str."""
        if user_text is None:
            return ""
        t = self.extract_topic(str(user_text))
        if t:
            self._remember_topic(t)
        return t

    def pick_topic(self):
        """Выбирает тему для самостоятельного размышления: свежую, новую, или
        тематический seed. Из недавних предпочитаем уникальную (не последнюю).
        Один return: str."""
        topics = [t for t, _ in reversed(self.topics) if isinstance(t, str) and t]
        chosen = topics[0] if topics else ""
        if len(topics) > 1 and len({t[:6] for t in topics}) > 1:
            chosen = topics[1] if topics[1] != chosen else topics[0]
        if not chosen and _SEED_TOPICS:
            chosen = random.choice(_SEED_TOPICS)
            self._remember_topic(chosen)  # seed запоминаем, чтобы был чем мыслить
        return chosen

    def _definition_hint(self, topic):
        """Короткое готовое определение, если тема известна-понятие.
        Один return: str."""
        hint = ""
        try:
            from algos.module_knowledge import fk as _fk
            hits = [key for key in _fk._by_name
                    if key.startswith("_") and topic and topic in
                    _fk._by_name[key].get("topic", "")]
            if hits:
                hint = _fk._by_name[hits[0]]["what"]
        except Exception:
            hint = ""
        return hint

    def draft_thought(self, topic):
        """Самостоятельно «думает»: строит мысль о теме, с подтянутой связью.
        Один return: str."""
        others = [t for t, _ in reversed(self.topics) if t and t != topic]
        t2 = others[0] if others else ""
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
        """Полный ход внутренней речи. Не повторяет мысль, записанную сразу
        до этого. Один return: dict со str-полями."""
        ts = time.time()
        thought = ""
        topic = ""
        written = False
        if ts - self.last_think_ts >= 30.0:
            self.last_think_ts = ts
            topic = self.pick_topic()
            thought = self.draft_thought(topic)
            # не повторяем ту же мысль дважды подряд
            if self.thoughts and self.thoughts[-1][0] == thought:
                thought = ""
            if thought:
                written = self._persist(topic or "внутренняя_тема", thought)
                self.thoughts.append((thought, time.time()))
                if len(self.thoughts) > self.max_thought:
                    self.thoughts = self.thoughts[-self.max_thought:]
        return {"thought": thought, "topic": topic, "written": written}

    def _persist(self, topic, thought):
        """Дописывает мысль в поток (data/mindstream/thoughts.jsonl).
        Пустая мысль не записывается; topic обрезается до 120 символов.
        Один return: bool."""
        ok = False
        if not (thought or "").strip() or not isinstance(thought, str):
            return False
        try:
            MS_LOG.parent.mkdir(parents=True, exist_ok=True)
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "topic": str(topic or "")[:120],
                   "thought": thought}
            with open(MS_LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            ok = True
        except Exception:
            ok = False
        return ok

    def recent_thought(self):
        """Последняя мысль (для ответа «над чем думаешь»).
        Защита от битого формата записи. Один return: str."""
        if not self.thoughts:
            return ""
        last = self.thoughts[-1]
        try:
            return last[0] if isinstance(last, (tuple, list)) else str(last)
        except Exception:
            return ""

    # ---------- рассуждение перед ответом ----------
    @staticmethod
    def reasoning_steps(topic):
        """Цепочка шагов рассуждения про тему. Один return: list[str]."""
        base = ["Уточняю, что именно спрашивают.",
                "Ищу тему в своих знаниях и связях.",
                "Подбираю ответ и проверяю, подходит ли он к вопросу."]
        tail = []
        if topic and isinstance(topic, str):
            tail = [f"Сопоставляю с понятием «{topic}».",
                    "Формулирую ответ простыми словами."]
        return base + tail

    # ---------- метапознание ----------
    def meta_thought(self):
        """Мета-мысль о собственном состоянии. Пустой список тем → «пусто».
        Один return: dict."""
        count = sum(1 for t in self.topics if isinstance(t, tuple) and len(t) >= 2)
        last = self.recent_thought()
        mood = "пусто" if count == 0 else ("спокойна" if count < 30 else "занята")
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

    def learn_liked_pair(self, instruction, output):
        """Умное самообучение: сохраняет (вопрос→ответ) в self_learned ТОЛЬКО
        если пара хорошая — ответ не мусорный, нет дубля по вопросу, корпус
        не разросся. Возвращает True, если пара реально добавлена. Один return: bool."""
        ok = False
        try:
            inst = (instruction or "").strip()
            out = (output or "").strip()
            if len(inst) < 10 or len(out) < 10:
                return ok
            # фильтр мусора: служебные ошибки/JSON/пересказ вопроса не учим
            low = out.lower()
            if any(m in low for m in ("traceback", "[mirro]", "не удалось связаться",
                                      "переформулируй", "не нашла это")):
                return ok
            SELF_LEARNED.mkdir(parents=True, exist_ok=True)
            target = SELF_LEARNED / "mindstream.jsonl"
            # дедуп по нормализованному вопросу
            import hashlib
            key = hashlib.md5(inst.lower().strip().encode("utf-8")).hexdigest()
            seen = False
            prefs = []
            if target.exists():
                with open(target, "r", encoding="utf-8") as fh:
                    for line in fh:
                        if not line.strip():
                            continue
                        prefs.append(line)
                        try:
                            r = json.loads(line)
                            if hashlib.md5(r.get("instruction", "").lower().strip().encode("utf-8")).hexdigest() == key:
                                seen = True
                        except Exception:
                            continue
            if seen:
                return ok
            # лимит корпуса: не даём раздуваться бесконечно
            if len(prefs) < 12000:
                rec = {"instruction": inst, "input": "",
                       "output": out, "source": "liked"}
                with open(target, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                ok = True
        except Exception:
            ok = False
        if ok:
            try:
                self._anchor_in_graph(instruction + " " + output)
            except Exception:
                pass
        return ok

    def _anchor_in_graph(self, text):
        """Связывает ядро темы с парой самых частотных слов текста в графе.
        Побочный эффект: добавляет/укрепляет узлы графа. Один return: None."""
        import collections
        kg_ref = None
        try:
            from algos.knowledge_graph import kg as _kg
            kg_ref = _kg
        except Exception:
            kg_ref = None
        if kg_ref is not None:
            words = _re.findall(r"[а-яёa-z]{3,}", (text or "").lower())
            words = [w for w in words if w not in _STOP]
            if words:
                anchor = ""
                anchors_in = [w for w in words if w in kg_ref.nodes]
                if anchors_in:
                    anchor = anchors_in[0]
                if not anchor:
                    anchor = words[0]
                counts = collections.Counter(words)
                try:
                    kg_ref.add_node(anchor, tag="понятие")
                except Exception:
                    pass
                for w, _c in counts.most_common(3):
                    if w != anchor:
                        try:
                            kg_ref.add_node(w, tag="факт")
                            kg_ref.add_edge(anchor, "связано_с", w, weight=0.5)
                        except Exception:
                            pass
        return None


mind = MindStream()


def try_metacognition(query):
    """Отвечает на вопросы о собственном «сознании»/состоянии Mirro:
    «что ты думаешь», «над чем думаешь», «осознаёшь ли себя».
    Пустой запрос → None. Один return: str|None."""
    ans = None
    if not (query or "").strip():
        return None
    q = (query or "").lower()
    # более специфичные вопросы про МЕХАНИКУ мышления — обрабатываем раньше
    if ("как ты думаешь" in q or "как это работает внутри тебя" in q
            or "как ты рассуждаешь" in q or "объясни как ты мыслишь" in q
            or "как ты ищешь ответ" in q):
        ans = ("Думаю так: беру твой вопрос, ищу похожие примеры в базе (TF-IDF, RAG), "
               "подтягиваю связи из графа понятий, сравниваю варианты и выбираю самый "
               "уверенный. Если в базе пусто — ищу в интернете или честно говорю, что не знаю.")
    elif ("о чём ты думаешь" in q or "над чем думаешь" in q or "что думаешь" in q
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
    elif ("какие у тебя пределы" in q or "чего ты не умеешь" in q or "где твои границы"
          or "ты ошибаешься" in q or "чего не знаешь" in q or "твои ограничения" in q):
        ans = ("Мои пределы честные: я отвечаю только из того, что знаю или найду в сети. "
               "Могу ошибаться и галлюцинировать, поэтому при важных вещах лучше "
               "перепроверять. Я не имею личного опыта и эмоций, как у человека — "
               "я имитирую тепло разговора, а не чувствую его.")
    return ans
