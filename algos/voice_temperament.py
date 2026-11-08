# -*- coding: utf-8 -*-
"""Mirro Algorithms — 32 · Адаптивный характер и темперамент ответов

Слой, который связывает нейрохимию графа (дофамин, серотонин, норадреналин) с
ЛИНГВИСТИЧЕСКИМИ фильтрами: он определяет, как именно оформляется сгенерированный
ответ — длину предложений, строгость формулировок, эмоциональную окраску.

Это «голос» поверх голоса: scripts/voice.py задаёт тон/характер реплики, а этот
модуль подбирает психотип по химии и фильтрует токены под него.

Чистый Python, атомарные функции (один return), по LINTER.md.
"""
import re as _re


def determine_voice_temperament(neuromodulators):
    """Определяет психотип системы на основе уровней нейромедиаторов.
    Пустые/некорректные уровни → «сбалансированный».
    Добавлены промежуточные психотипы при сильном дисбалансе.
    Один return: str."""
    if not neuromodulators:
        return "сбалансированный"
    try:
        dopamine = float(neuromodulators.get("dopamine", 0.0) or 0.0)
        serotonin = float(neuromodulators.get("serotonin", 1.0) or 1.0)
    except Exception:
        return "сбалансированный"
    temperament = "сбалансированный"
    if dopamine > 0.4 and serotonin < 0.6:
        temperament = "хаотичный_холерик"
    elif serotonin > 1.2:
        temperament = "флегматичный_философ"
    elif dopamine < 0.2 and serotonin < 0.7:
        temperament = "уставший_меланхолик"
    return temperament


def try_apply_temperament_filters(text_tokens, temperament, min_len=4, max_len=8):
    """Корректирует длину и структуру токенов ответа под выбранный темперамент.
    Пустые/неизвестный темперамент → исходный список без изменений.
    Один return: list."""
    processed = []
    if not text_tokens:
        return processed
    tokens = list(text_tokens)
    processed = tokens
    if temperament == "хаотичный_холерик":
        # Укорачиваем: оставляем только короткие, ёмкие токены (без вводных длинных)
        processed = [t for t in tokens if len(_re.sub(r"\W", "", str(t))) < max_len]
    elif temperament == "флегматичный_философ":
        # Оставляем только весомые, длинные концептуальные токены
        processed = [t for t in tokens if len(_re.sub(r"\W", "", str(t))) > min_len]
    else:
        # прочие/неизвестные темпераменты не нарушают структуру
        processed = tokens
    return processed


def apply_temperament_to_text(text, temperament, min_len=4, max_len=8):
    """Применяет темперамент-фильтр к целому тексту: разбивает на слова,
    фильтрует по длине и возвращает текст. Пустой/None → «».
    Один return: str."""
    if not text:
        return ""
    words = _re.findall(r"[а-яёa-z0-9]+", str(text).lower())
    kept = try_apply_temperament_filters(words, temperament, min_len, max_len)
    return " ".join(kept)


if __name__ == "__main__":
    chem = {"dopamine": 0.8, "serotonin": 0.3}
    tmp = determine_voice_temperament(chem)
    print("темперамент:", tmp)
    print("фильтр:", try_apply_temperament_filters(["математика", "код", "ии"], "флегматичный_философ"))
    print("текст-фильтр:", apply_temperament_to_text("математика и код это приятно", "флегматичный_философ"))