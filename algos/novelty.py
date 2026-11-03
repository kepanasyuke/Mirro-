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


class Novelty:
    def __init__(self, window=200):
        # коллектор известных тем/ключевых групп из прошедших вопросов
        self.seen = set()
        self.recent = deque(maxlen=window)

    @staticmethod
    def _kw(text):
        words = _re.findall(r"[а-яёa-z]{3,}", (text or "").lower())
        return set(w for w in words if w not in _STOP)

    def feed(self, user_text, known=True):
        """Учит: вопрос известен (known=True) или нет (False)."""
        kw = self._kw(user_text)
        if known:
            self.seen.update(kw)
        self.recent.append((kw, known))
        return kw

    def is_novel(self, user_text, known_kw=None):
        """True, если вопрос выглядит новым (нет общих ключевых слов ни с чем."""
        kw = self._kw(user_text)
        if not kw:
            return False
        # пересечение с накопленным
        if kw & self.seen:
            return False
        # известна ли тема через переданный набор (например, из графа/базы)
        if known_kw is not None and kw & set(known_kw):
            return False
        return True

    def unknown_topic(self, user_text):
        """Возвращает «якорное» слово новизны или None."""
        kw = self._kw(user_text)
        if not kw:
            return None
        return kw.pop()


_STOP = set(("и","или","что","как","это","то","для","про","мне","меня","ты","я","не","на","в","по","с","из"))


# синглтон
novelty = Novelty()


def try_novelty(query, known_kw=None):
    """Отвечает, только если вопрос действительно новый и нет готового ответа."""
    try:
        if novelty.is_novel(query, known_kw):
            topic = novelty.unknown_topic(query)
            return (f"Это новое для меня — такого я ещё не изучала/{(topic or 'этой темы')}."
                    f" Я запомню и постараюсь освоить. Сейчас могу ответить на то, что уже в моих знаниях.")
    except Exception:
        pass
    return None


if __name__ == "__main__":
    novelty.feed("Что такое градиентный спуск", known=True)
    print("известно:", novelty.is_novel("объясни градиентный спуск"))
    print("ново:", novelty.is_novel("как собрать квантовый компьютер из бумаги"))
    print(try_novelty("почему небо зелёное в облачный день"))