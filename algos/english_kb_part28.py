# -*- coding: utf-8 -*-
"""English KB part 28: trees and herbs (oak, willow, bramble, heath, fern).

Каркас будущего разбиения базы. Источник правды — algos/english_kb.py:
здесь только срез реестра по своим темам, чтобы не держать вторую копию
определений (они уже разошлись с основной базой и не читались никем).
"""
from algos.english_kb import _TOPIC_TEST as _ALL_TRIGGERS
from algos.english_kb import _EN_KB

NAMES = (
    "oak",
    "willow",
    "bramble",
    "heath",
    "fern",
)

TOPICS = {name: _EN_KB[name] for name in NAMES}

_KEYS = dict(_ALL_TRIGGERS)

TOPIC_TEST = [(name, _KEYS[name]) for name in NAMES]

del _ALL_TRIGGERS, _KEYS
