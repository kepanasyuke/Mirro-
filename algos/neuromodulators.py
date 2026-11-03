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

# разные скорости возврата к базе (биология: норадреналин быстрее, серотонин медленнее)
DECAY_RATE = {"dop": 0.08, "ser": 0.02, "nor": 0.15, "ach": 0.06}
# порог «спайка» (всплеска) и во сколько раз подскочит уровень
SPIKE_THRESHOLD = 0.18
SPIKE_AMPLITUDE = 0.35


def _clamp(v):
    """Ограничивает уровень диапазоном [0,1]. Один return: float."""
    return max(CLAMP[0], min(CLAMP[1], v))


class Neuromodulators:
    def __init__(self, base=None):
        self.level = dict(base or BASE)
        self._charge = {k: 0.0 for k in BASE}          # накопленный заряд (до спайка)
        self._pending = {}                             # отложенное высвобождение: k -> (amount, ticks)
        self._ticks = 0
        self.spike_log = []                            # последние спайки: (медиатор, tick)

    def shift(self, dop=0.0, ser=0.0, nor=0.0, ach=0.0):
        """Сдвигает уровни медиаторов. Один return: dict."""
        inc = {"dop": dop, "ser": ser, "nor": nor, "ach": ach}
        for k, v in self.level.items():
            self.level[k] = _clamp(v + inc[k])
        self._charge = {k: _clamp(self._charge[k] + abs(inc[k])) for k in BASE}
        return dict(self.level)

    def spike_check(self):
        """Пороговая активация: накопленный заряд выдаёт «спайк» (всплеск
        возбудимости), потом сбрасывается. Медиаторы, перешагнувшие порог,
        получают скачок уровня и откладывают возврат (отложенное высвобождение).
        Один return: list спайкнувших медиаторов."""
        fired = []
        for k in BASE:
            if self._charge[k] >= SPIKE_THRESHOLD:
                self.level[k] = _clamp(self.level[k] + SPIKE_AMPLITUDE)
                self._charge[k] = 0.0
                # отложенное высвобождение: на 3 тика уровень не затухает
                self._pending[k] = (self.level[k], 3)
                fired.append(k)
                self.spike_log.append((k, self._ticks))
        return fired

    def delayed(self, delay=2, dop=0.0, ser=0.0, nor=0.0, ach=0.0):
        """Отложенное высвобождение (дофамин-предвкушение): сдвиг произойдёт
        через `delay` тиков, а не сразу. Один return: None."""
        for k, amt in {"dop": dop, "ser": ser, "nor": nor, "ach": ach}.items():
            if amt:
                # складываем в ожидаемое с задержкой
                self._pending[k] = (self.level.get(k, BASE[k]) + amt, delay)
        return None

    def decay(self, amount=None):
        """Медиаторы медленно возвращаются к базе (гомеостаз), у каждого своя
        скорость. Отложенные (`_pending`) не затухают до окончания задержки.
        Один return: dict."""
        self._ticks += 1
        fired = self.spike_check()
        release = {}
        for k in list(self._pending):
            val, ticks = self._pending[k]
            if self._ticks >= ticks:
                self.level[k] = _clamp(val)
                release[k] = self.level[k]
                del self._pending[k]
        for k, v in self.level.items():
            if k in self._pending:
                continue  # отложенный — держим уровень
            rate = DECAY_RATE[k] if amount is None else amount
            self.level[k] = _clamp(v + (BASE[k] - v) * rate)
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