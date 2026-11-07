# -*- coding: utf-8 -*-
"""Mirro Algorithms — 36 · Эмпатичный отклик (Empathic Response)

Инновация: Mirro чувствует тон собеседника (радость, усталость, раздражение,
грусть, нейтрально) и отвечает с подходящей эмпатией — теплее в диалоге,
а не безликим ботом.

Распознаёт тональность по словарям, помнит её скользяще (как настроение
разговора) и добавляет короткую эмпатичную заставку к ответу.

Чистый Python, атомарные функции (один return), по LINTER.md.
"""
import os
import re as _re

# расширенные словари тональности (словоформы за счёт -о/-а/суффиксов не нужны —
# ищем вхождение основы в текст)
_RAD = {
    "positive": {"отличн", "прекрасн", "крут", "замечательн", "спасиб", "супер",
                 "нрав", "любл", "успех", "радостн", "помогл", "здорово", "лучш",
                 "класс", "победа", "восхитительн"},
    "negative": {"плох", "ужасн", "проблем", "ошиб", "провал", "грустн", "ненавиж",
                 "катастроф", "худш", "сломал", "фейл", "огорч", "разочар",
                 "злюсь", "раздраж", "не работает", "не получается"},
    "fatigue": {"устал", "устала", "вымотан", "выдохся", "спать хочу", "нет сил",
                "измотан", "выгорел", "перегруз"},
}

# скользящее настроение диалога (в памяти процесса)
_emotion = 0.0        # -1 (негатив) .. +1 (позитив)
_fatigue = 0.0        # 0..1 усталость
_MEM_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "emotion_state.json")

_NEUTRAL = None        # нейтральная заставка не нужна

# заставки по настроению
_LEAD_RAD = {
    "positive": ["Отрадно это слышать, ", "Приятно помочь, ", "Отличный ход, что спрашиваешь, "],
    "negative_full": ["Понимаю, неприятно. ", "Слышу, что тебе нелегко. ", "Жаль, что так вышло. "],
    "negative_mild": ["Понимаю, звучит непросто. ", "Слышу тебя. ", "Понимаю, что это напрягает. "],
    "fatigue": ["Похоже, ты устал(а) — отвечу коротко и по делу. ", "Чувствую, что сил мало — дам самое важное. "],
}


def _detect_rad(message):
    """Определяет тональность и усталость реплики по словарям.
    Один return: dict {'pos', 'neg', 'fatigue'}."""
    m = (message or "").lower()
    pos = sum(1 for w in _RAD["positive"] if w in m)
    neg = sum(1 for w in _RAD["negative"] if w in m)
    fatigue = sum(1 for w in _RAD["fatigue"] if w in m)
    return {"pos": pos, "neg": neg, "fatigue": fatigue}


def observe(message):
    """Обновляет скользящее настроение по новой реплике. Один return: dict."""
    global _emotion, _fatigue
    d = _detect_rad(message)
    delta = 0.15 * (d["pos"] - d["neg"])
    if d["pos"] == 0 and d["neg"] == 0:
        # нейтральная реплика мягко тянет к нулю
        delta = -0.02 * _emotion
    _emotion = max(-1.0, min(1.0, _emotion + delta))
    if d["fatigue"]:
        _fatigue = min(1.0, _fatigue + 0.25)
    else:
        _fatigue = max(0.0, _fatigue - 0.08)
    return {"emotion": _emotion, "fatigue": _fatigue}


def current_tone():
    """Текущее настроение разговора. Один return: dict."""
    return {"emotion": _emotion, "fatigue": _fatigue}


def empathy_lead(message):
    """Подбирает эмпатичную заставку к ответу под тон собеседника.
    Если разговор нейтральный — возвращает None (заставка не нужна).
    Один return: str или None."""
    d = _detect_rad(message)
    lead = None
    if d["fatigue"]:
        lead = _pick(_LEAD_RAD["fatigue"])
    elif d["pos"] > d["neg"] and d["pos"] > 0:
        lead = _pick(_LEAD_RAD["positive"])
    elif d["neg"] > 0:
        lead = _pick(_LEAD_RAD["negative_mild"] if d["neg"] == 1 else _LEAD_RAD["negative_full"])
    return lead


def _pick(options):
    """Случайный элемент списка. Один return: str."""
    import random
    return random.choice(options)


def apply_empathy(message, answer):
    """Оборачивает ответ эмпатичной заставкой под тон сообщения.
    Один return: str."""
    out = answer
    lead = empathy_lead(message)
    if lead and answer:
        ans = answer if isinstance(answer, str) else str(answer or "")
        # не дублируем, если пользователь просто спросил настроение/самочувствие
        low = (message or "").lower()
        if not any(w in low for w in ("как ты себя", "как настроение", "как дела")):
            first = ans[0].lower() if ans else ""
            out = lead + first + ans[1:] if ans else lead
    return out


if __name__ == "__main__":
    print(apply_empathy("у меня всё сломалось и не работает, какая катастрофа",
                        "Проверь подключение и перезапусти сервис."))
    print(apply_empathy("спасибо, отлично помогло!",
                        "Рада, что получилось."))
    print(apply_empathy("я очень устал сегодня",
                        "Отдохни и возвращайся."))