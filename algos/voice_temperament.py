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
    Один return: str."""
    dopamine = neuromodulators.get("dopamine", 0.0)
    serotonin = neuromodulators.get("serotonin", 1.0)
    temperament = "сбалансированный"
    if dopamine > 0.4 and serotonin < 0.6:
        temperament = "хаотичный_холерик"
    elif serotonin > 1.2:
        temperament = "флегматичный_философ"
    return temperament


def try_apply_temperament_filters(text_tokens, temperament, min_len=4, max_len=8):
    """Корректирует длину и структуру токенов ответа под выбранный темперамент.
    Один return: list."""
    tokens = list(text_tokens)
    processed = tokens
    if temperament == "хаотичный_холерик":
        # Укорачиваем: оставляем только короткие, ёмкие токены (без вводных длинных)
        processed = [t for t in tokens if len(_re.sub(r"\W", "", t)) < max_len]
    elif temperament == "флегматичный_философ":
        # Оставляем только весомые, длинные концептуальные токены
        processed = [t for t in tokens if len(_re.sub(r"\W", "", t)) > min_len]
    return processed


if __name__ == "__main__":
    chem = {"dopamine": 0.8, "serotonin": 0.3}
    tmp = determine_voice_temperament(chem)
    print("темперамент:", tmp)
    print("фильтр:", try_apply_temperament_filters(["математика", "код", "ии"], "флегматичный_философ"))