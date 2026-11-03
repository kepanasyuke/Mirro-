# -*- coding: utf-8 -*-
"""Mirro Algorithms — 27 · Нейромедиаторы (Neuromodulators)

Инновация: эмоциональное состояние диалога модулирует СТИЛЬ ответа,
как в биологических нейросетях. Каждый «медиатор» — отдельная шкала:

  дофамин    DOP  — мотивация, радость, «иду навстречу»
  серотонин  SER  — спокойствие, стабильность, уверенность
  норадреналин NOR — бодрость, тревога, срочность
  ацетилхолин ACH  — внимание, фокус, обучение

Диалог сдвигает уровни (позитив поднимает дофамин+серотонин, срочность —
норадреналин, новая тема — ацетилхолин). Итоговый «химический профиль»
влияет на формулировку: энтузиазм, уверенность, сдержанность или тревогу.

Лёгкий, без внешних библиотек; работает поверх dialogue_memory.
"""
import random

# базовые уровни медиаторов (0..1)
BASE = {"dop": 0.5, "ser": 0.5, "nor": 0.3, "ach": 0.4}
CLAMP = (0.0, 1.0)


def _clamp(v):
    """Ограничивает уровень диапазоном [0,1]. Один return: float."""
    return max(CLAMP[0], min(CLAMP[1], v))


class Neuromodulators:
    def __init__(self, base=None):
        self.level = dict(base or BASE)

    def shift(self, dop=0.0, ser=0.0, nor=0.0, ach=0.0):
        """Сдвигает уровни медиаторов (затухая к базе). Один return: dict."""
        for k, v in self.level.items():
            self.level[k] = _clamp(v + {"dop": dop, "ser": ser, "nor": nor, "ach": ach}[k])
        return dict(self.level)

    def decay(self, amount=0.02):
        """Медиаторы медленно возвращаются к базе (гомеостаз). Один return: dict."""
        for k, v in self.level.items():
            self.level[k] = _clamp(v + (BASE[k] - v) * amount)
        return dict(self.level)

    def dominant(self):
        """Доминирующий медиатор. Один return: str (ключ)."""
        return max(self.level, key=self.level.get)

    def profile(self):
        """Короткое описание состояния. Один return: str."""
        dom = self.dominant()
        labels = {
            "dop": "дофамин: радость и мотивация",
            "ser": "серотонин: спокойствие и уверенность",
            "nor": "норадреналин: бодрость, внимание к срочному",
            "ach": "ацетилхолин: фокус и готовность учиться",
        }
        return " | ".join(f"{k.upper()}={v:.2f}" for k, v in self.level.items()) + f" → {labels[dom]}"


# стили ответов под доминирующий медиатор
_STYLES = {
    "dop": [
        "Отличный вопрос! Давай разберём!",
        "Как здорово, что ты спросил!",
        "Обожаю такие темы! Смотри:",
    ],
    "ser": [
        "Спокойно разберём это.",
        "Всё по порядку: вот суть.",
        "Уверена в ответе:",
    ],
    "nor": [
        "Быстро и по делу:",
        "Срочно к сути:",
        "Важно сейчас, отвечаю:",
    ],
    "ach": [
        "Сфокусируюсь на деталях:",
        "Новая тема — вникаю:",
        "Разберу внимательно:",
    ],
}


def style_prefix(nm: Neuromodulators):
    """Префикс ответа по доминирующему медиатору. Один return: str."""
    dom = nm.dominant()
    return random.choice(_STYLES[dom])


def answer_with_style(nm, core_answer):
    """Оборачивает ответ в эмоциональный стиль. Один return: str."""
    if not core_answer:
        return core_answer
    return style_prefix(nm) + " " + core_answer[0:1].lower() + core_answer[1:]


# глобальный набор медиаторов для процесса
nm = Neuromodulators()


def try_neuromod(query):
    """Точка входа для try_*: отвечает про состояние или какой медиатор доминирует.
    Один return: str или None."""
    q = (query or "").strip().lower()
    ans = None
    if any(w in q for w in ["нейромедиатор", "исколько у тебя эмоц", "какое настроение бесед",
                            "какой медиатор", "нейрохимия", "химический профиль"]):
        ans = "Нейромедиаторы: " + nm.profile()
    return ans


if __name__ == "__main__":
    print("база:", nm.profile())
    nm.shift(dop=0.3, ser=0.2)  # обрадовали
    print("после радости:", nm.profile())
    nm.decay()
    print("после затухания:", nm.profile())
    print("стиль при доминанте:", style_prefix(nm))
    print("ответ:", answer_with_style(nm, "нейрон передаёт сигнал"))