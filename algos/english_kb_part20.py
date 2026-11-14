# -*- coding: utf-8 -*-
"""English KB part 20: tune, chorus and discord (batch).

Каркас будущего разбиения базы. Источник правды — algos/english_kb.py:
здесь только срез реестра по своим темам, чтобы не держать вторую копию
определений (они уже разошлись с основной базой и не читались никем).
"""
from algos.english_kb import _TOPIC_TEST as _ALL_TRIGGERS
from algos.english_kb import _EN_KB

NAMES = (
    "tune",
    "strain",
    "chorus",
    "discord",
    "chant",
)

TOPICS = {name: _EN_KB[name] for name in NAMES}

TOPIC_TEST = [(name, keys) for name, keys in _ALL_TRIGGERS if name in NAMES]

del _ALL_TRIGGERS
