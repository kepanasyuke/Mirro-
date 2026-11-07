# -*- coding: utf-8 -*-
"""Mirro Algorithms — 22 · Эмоциональная память диалога (Affective Dialogue Memory)

Инновация: превращает поток отдельных сообщений в СВЯЗНУЮ беседу.
Запоминает:
  - тему разговора (последние темы),
  - «что о чём говорили» (контекстные пары),
  - эмоциональную тональность прошлых реплик,
чтобы отвечать с опорой на предысторию: «как ты обычно…», «повтори, что я просил»,
«в прошлый раз ты говорил про X».

Лёгкий, без внешних библиотек; состояние хранится в памяти процесса.
"""
import re as _re
import os
from collections import deque

# ----- персистентная память диалога (между сессиями) -----
_MEM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
_MEM_FILE = os.path.join(_MEM_DIR, "dialogue_memory.json")


def _default_mem_path():
    """Путь к файлу персистентной памяти (создаёт каталог при необходимости).
    Один return: str."""
    d = os.path.dirname(_MEM_FILE)
    if not os.path.isdir(d):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
    return _MEM_FILE


# стоп-слова для извлечения «темы» из реплики
_STOP = set(("и","или","а","но","то","как","что","это","мне","меня","меня","ты","я",
             "могу","быть","есть","был","была","в","на","по","с","из","для","не","про"))


def _keywords(text):
    words = _re.findall(r"[а-яёa-z]+", (text or "").lower())
    return [w for w in words if len(w) > 3 and w not in _STOP]


class DialogueMemory:
    def __init__(self, max_topics=8, max_context=30):
        self.topics = deque(maxlen=max_topics)     # темы последних реплик
        self.context = deque(maxlen=max_context)   # (user_keywords, bot_reply_keywords)
        self.emotion = 0.0                          # скользящая тональность -1..1
        self.pos_words = {"спасибо","отлично","круто","здорово","супер","люблю","нравится","помогло"}
        self.neg_words = {"плохо","грустно","злюсь","не работает","ошибка","не получается","жаль","ужас","ненавижу"}
        self._persist_path = None
        self.load()

    # ----- персистентность между сессиями -----
    def set_persist_path(self, path):
        """Задаёт файл сохранения (по умолчанию data/dialogue_memory.json).
        Один return: str."""
        self._persist_path = path
        return path

    def _path(self):
        """Файл персистентной памяти. Один return: str."""
        return self._persist_path or _default_mem_path()

    def load(self):
        """Восстанавливает память из файла (если есть и корректен JSON).
        Один return: bool."""
        ok = False
        try:
            import json
            path = self._path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.topics = deque(data.get("topics", [])[-(self.topics.maxlen or 8):],
                                    maxlen=self.topics.maxlen)
                self.context = deque(data.get("context", [])[-(self.context.maxlen or 30):],
                                     maxlen=self.context.maxlen)
                self.emotion = float(data.get("emotion", 0.0))
                ok = True
        except Exception:
            ok = False
        return ok

    def save(self):
        """Сохраняет память на диск (JSON, атомарно через tmp+replace).
        Один return: bool."""
        ok = False
        try:
            import json
            path = self._path()
            d = os.path.dirname(path)
            if d and not os.path.isdir(d):
                try:
                    os.makedirs(d, exist_ok=True)
                except Exception:
                    pass
            data = {"topics": [list(t) for t in self.topics],
                    "context": [list(c) for c in self.context],
                    "emotion": self.emotion}
            tmp = str(path) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, str(path))
            ok = True
        except Exception:
            ok = False
        return ok

    def remember(self, user_text, bot_reply=""):
        """Фиксирует реплику: тему + тональность + контекст."""
        kw = _keywords(user_text)
        if kw:
            self.topics.append(tuple(kw[:4]))
        # тональность простым счётчиком совпадений
        seg = (user_text + " " + bot_reply).lower()
        pos = sum(w in seg for w in self.pos_words)
        neg = sum(w in seg for w in self.neg_words)
        delta = 0.1 if pos > neg else (-0.1 if neg > pos else 0.0)
        self.emotion = max(-1.0, min(1.0, self.emotion + delta))
        self.context.append((kw, _keywords(bot_reply)))
        self.save()
        return kw

    # ----- интерфейс для try_* -----
    def last_topic(self):
        """Свежая тема последней реплики. Один return: str или None."""
        result = None
        for t in reversed(self.topics):
            if t:
                result = " ".join(t)
                break
        return result

    def topic_context(self, user_text):
        """Есть ли похожая тема в истории? Один return: str или None."""
        kw = set(_keywords(user_text))
        result = None
        for t in reversed(self.topics):
            if set(t) & kw:
                result = " ".join(t)
                break
        return result

    def mood(self, word_ru="да"):
        """Разговорная фраза о текущем настроении диалога. Один return: str."""
        phrase = "Нейтральный тон, слушаю внимательно."
        if self.emotion > 0.3:
            phrase = "Разговор тёплый, иду навстречу."
        elif self.emotion < -0.3:
            phrase = "Разговор напряжённый — отвечу аккуратнее."
        return phrase

    def summarize(self):
        return f"тем: {len(self.topics)}, реплик в памяти: {len(self.context)}, тон: {self.emotion:+.2f}"


# синглтон памяти для всего сервера
dm = DialogueMemory()


_SAY_TOPIC_TRIGGERS = ["помнишь что я говорил", "помнишь про", "что мы обсуждали",
                        "о чём мы говорили", "что я просил", "что я просила",
                        "в прошлый раз", "недавно говорил", "недавно говорила"]
_MOOD_TRIGGERS = ["как у нас разговор", "наше настроение", "как протекает", "какой тон"]
_MEM_TRIGGERS = ["сколько ты помнишь", "что ты помнишь", "твоя память"]


def _answer_topic(q):
    """Ответ про вспоминание темы. Один return: str."""
    topic = dm.topic_context(q) or dm.last_topic()
    msg = "Мы ещё не обсуждали это — давай начнём."
    if topic:
        msg = "Помню: мы говорили про «" + topic + "»."
    return msg


def _has_trigger(q, triggers):
    """Есть ли в запросе любой из триггеров. Один return: bool."""
    return any(w in q for w in triggers)


def try_dialogue_memory(query):
    """Возвращает ответ строкой, если вопрос про память/историю, иначе None."""
    q = (query or "").strip().lower()
    ans = None
    if _has_trigger(q, _SAY_TOPIC_TRIGGERS):
        ans = _answer_topic(q)
    elif _has_trigger(q, _MOOD_TRIGGERS):
        ans = dm.mood()
    elif _has_trigger(q, _MEM_TRIGGERS):
        ans = "В краткосрочной памяти держу последние темы и тон диалога. " + dm.summarize() + "."
    return ans


if __name__ == "__main__":
    dm.remember("Расскажи про нейронные сети")
    dm.remember("Как работает градиентный спуск?", "Градиентный спуск итеративно находит минимум функции потерь.")
    dm.remember("Спасибо, помогло!", "Пожалуйста!")
    print(dm.summarize())
    print("вопрос про память:", try_dialogue_memory("помнишь что я говорил?"))
    print("тема свежая:", dm.last_topic())
    print("контекст 'спуск':", dm.topic_context("что такое градиентный спуск?"))