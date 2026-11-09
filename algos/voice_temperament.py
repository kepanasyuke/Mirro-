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
    """Определяет психотип системы на основе уровней нейромедиаторов
    (дофамин/серотонин, клампятся в [0,2]).
    Пустой/не-дикт/некорректные уровни → «сбалансированный».
    Психотипы: воодушевлённый_лидер, хаотичный_холерик, флегматичный_философ,
    уставший_меланхолик, спокойный_реалист. Один return: str."""
    if not isinstance(neuromodulators, dict) or not neuromodulators:
        return "сбалансированный"
    try:
        dopamine = max(0.0, min(2.0, float(neuromodulators.get("dopamine", 0.0) or 0.0)))
        serotonin = max(0.0, min(2.0, float(neuromodulators.get("serotonin", 1.0) or 1.0)))
    except Exception:
        return "сбалансированный"
    temperament = "сбалансированный"
    if dopamine > 0.7 and serotonin > 0.8:
        temperament = "воодушевлённый_лидер"
    elif dopamine > 0.4 and serotonin < 0.6:
        temperament = "хаотичный_холерик"
    elif serotonin > 1.2:
        temperament = "флегматичный_философ"
    elif dopamine < 0.2:
        temperament = "уставший_меланхолик" if serotonin < 0.7 else "спокойный_реалист"
    return temperament


def try_apply_temperament_filters(text_tokens, temperament, min_len=4, max_len=8):
    """Корректирует длину и структуру токенов ответа под выбранный темперамент.
    Пустые/неизвестный темперамент → исходный список без изменений.
    Токены приводятся к str; min_len∈[0,50], max_len∈[1,50]. Один return: list."""
    processed = []
    if not isinstance(text_tokens, (list, tuple, set)) or not text_tokens:
        return processed
    min_len = max(0, min(50, int(min_len or 0)))
    max_len = max(1, min(50, int(max_len or 8)))
    tokens = [str(t) for t in text_tokens]
    processed = tokens
    if temperament == "хаотичный_холерик":
        # Укорачиваем: оставляем только короткие, ёмкие токены (без вводных длинных)
        processed = [t for t in tokens if len(_re.sub(r"\W", "", t)) < max_len]
    elif temperament == "флегматичный_философ":
        # Оставляем только весомые, длинные концептуальные токены
        processed = [t for t in tokens if len(_re.sub(r"\W", "", t)) > min_len]
    elif temperament == "уставший_меланхолик":
        # Усталый: оставляем только короткие и средние токены
        processed = [t for t in tokens if len(_re.sub(r"\W", "", t)) <= max_len + 2]
    else:
        # прочие/неизвестные темпераменты не нарушают структуру
        processed = tokens
    return processed[:200]


def apply_temperament_to_text(text, temperament, min_len=4, max_len=8):
    """Применяет темперамент-фильтр к целому тексту: разбивает на слова,
    фильтрует по длине и возвращает текст. Пустой/None → «»; non-str → текст.
    Один return: str."""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
    words = _re.findall(r"[а-яёa-z0-9]+", text.lower())
    kept = try_apply_temperament_filters(words, temperament, min_len, max_len)
    return " ".join(kept)[:4000]


if __name__ == "__main__":
    chem = {"dopamine": 0.8, "serotonin": 0.3}
    tmp = determine_voice_temperament(chem)
    print("темперамент:", tmp)
    print("фильтр:", try_apply_temperament_filters(["математика", "код", "ии"], "флегматичный_философ"))
    print("текст-фильтр:", apply_temperament_to_text("математика и код это приятно", "флегматичный_философ"))