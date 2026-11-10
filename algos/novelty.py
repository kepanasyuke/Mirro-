# -*- coding: utf-8 -*-
"""Mirro Algorithms — 23 · Детектор новизны (Novelty Detector)

Инновация: мета-осознание границ собственных знаний.
Позволяет Мирро отличить:
  - «я знаю об этом» (есть близкий пример в базе/графе)
  - «это новое, я не готова» (вопрос не похож ни на что известное)

Вместо того, чтобы выдумывать нерелевантный ответ на неизвестный вопрос,
Мирро честно сообщает о новизне и запоминает тему, чтобы позже её освоить.
Для работы внутри процеастроителя идентичность между запросами уже задана.
"""
import re as _re
from collections import deque

_STOP = set(("и","или","что","как","это","то","для","про","мне","меня","ты","я",
             "не","на","в","по","с","из","расскажи","объясни","почему","зачем",
             "который","которая","можно","нужно","есть","быть","очень","вообще","ещё",
             "уже","только","чтобы","потому","поэтому","даже","какие","какая","такое",
             "сейчас","потом","тогда","здесь","тут","себя","свой","самый","было",
             "а","от","до","под","над","при","без","для","после","через","между",
             "когда","куда","откуда","сколько","какой","какие","какая"))


class Novelty:
    def __init__(self, window=200):
        # коллектор известных тем/ключевых групп из прошедших вопросов
        self.seen = set()
        self.recent = deque(maxlen=window)

    @staticmethod
    def _kw(text):
        if not isinstance(text, str) or not text.strip():
            return set()
        words = _re.findall(r"[а-яёa-z]{4,}", text.lower())
        return set(w for w in words if w not in _STOP)

    def feed(self, user_text, known=True):
        """Учит: вопрос известен (known=True) или нет (False).
        Пустой вход → пустое множество. Один return: set."""
        kw = self._kw(user_text)
        if known:
            self.seen.update(kw)
        self.recent.append((kw, bool(known)))
        return kw

    def _known_via(self, kw, known_kw):
        """Совпадает ли запрос с известными темами. Один return: bool."""
        known_in_seen = bool(kw & self.seen)
        known_in_passed = False
        if known_kw is not None:
            try:
                known_in_passed = bool(kw & set(known_kw))
            except Exception:
                known_in_passed = False
        return known_in_seen or known_in_passed

    def is_novel(self, user_text, known_kw=None):
        """True, если вопрос выглядит новым. Тема, уже отмеченная недавно как
        новая и запрошенная повторно, — считается менее новой (ответ не
        зацикливается). Не-строка/пустой вход → False. Один return: bool."""
        if not isinstance(user_text, str) or not user_text.strip():
            return False
        kw = self._kw(user_text)
        novel = True
        if not kw:
            novel = False
        elif self._known_via(kw, known_kw):
            novel = False
        elif self._just_seen_novel(kw):
            novel = True  # сохраняем новизну, пользователь ещё спрашивает
        return novel

    def _just_seen_novel(self, kw):
        """Была ли эта тема недавно помечена как НОВАЯ. Пустой kw → False.
        Один return: bool."""
        if not kw:
            return False
        for rkw, known in reversed(self.recent):
            if rkw and set(rkw) & kw:
                return not known
        return False

    def unknown_topic(self, user_text):
        """Возвращает «якорное» слово новизны (детерминированно — первое
        по алфавиту, чтобы ответ не «прыгал» между запусками). Один return: str|None."""
        kw = self._kw(user_text)
        topic = None
        if kw:
            # предпочитаем более длинные/содержательные слова (не за 40 симв.)
            cands = [w for w in kw if isinstance(w, str) and len(w) <= 40]
            topic = sorted(cands or [w for w in kw if isinstance(w, str)],
                           key=lambda w: (-len(w), w))[0] if cands or any(
                isinstance(w, str) for w in kw) else None
        return topic


# синглтон
novelty = Novelty()


def _novelty_msg(topic):
    """Строка ответа про новизну. Пустой topic → «этой темы», тема обрезается
    до 60 символов. Один return: str."""
    label = (topic if isinstance(topic, str) else (str(topic) if topic else "этой темы"))[:60]
    return (f"Это новое для меня — «{label}» я ещё не изучала."
            f" Я запомню и постараюсь освоить. Сейчас могу ответить на то, что уже в моих знаниях.")


def try_novelty(query, known_kw=None):
    """Отвечает, только если вопрос действительно новый. Пустой/не-строковый
    запрос → None. Один return: str|None."""
    ans = None
    if not isinstance(query, str) or not query.strip():
        return None
    try:
        if novelty.is_novel(query, known_kw):
            ans = _novelty_msg(novelty.unknown_topic(query))
    except Exception:
        ans = None
    return ans


if __name__ == "__main__":
    novelty.feed("Что такое градиентный спуск", known=True)
    print("известно:", novelty.is_novel("объясни градиентный спуск"))
    print("ново:", novelty.is_novel("как собрать квантовый компьютер из бумаги"))
    print(try_novelty("почему небо зелёное в облачный день"))