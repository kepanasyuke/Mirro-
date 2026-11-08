# -*- coding: utf-8 -*-
"""Mirro English KB — базовый английский режим.

Распознаёт англоязычный вопрос (подавляющее большинство букв — латиница,
есть англ. стоп-слово) и отвечает из мини-справочника базовых понятий
(нейросеть, алгоритм, память, граф, ДНК и т.п.) на английском.
Если понятия нет в справочнике — отвечает нейтральной фразой-переходом.

Чистый Python, атомарные функции (одни return), по LINTER.md.
"""
import re as _re

# мини-справочник: английский вопрос -> связный английский ответ
_EN_KB = {
    "neural": ("Neural networks learn by adjusting weights through training. "
               "A simple one, a perceptron, sums weighted inputs and passes them "
               "through an activation function. Training uses the error to tune weights."),
    "algorithm": ("An algorithm is a step-by-step procedure that solves a task. "
                  "For example, sorting can be done with bubble sort or merge sort. "
                  "Algorithms differ in speed and memory use."),
    "memory": ("Memory is the ability to store and reproduce information. In a "
               "computer it is RAM and disk; in the brain it is patterns of "
               "strengthened connections between neurons."),
    "graph": ("A graph is a set of nodes connected by edges. It models networks, "
              "paths, relations. Key ideas: connectivity, centrality, shortest path."),
    "dna": ("DNA is the molecule that stores hereditary information. Genes are "
            "sections of DNA that code for traits. DNA passes from parents to children."),
    "gravity": ("Gravity is the attraction between objects with mass. Earth pulls "
                "things down; heavier objects attract more strongly. It keeps planets "
                "in orbit and shapes the universe."),
    "cell": ("A cell is the basic unit of life. It has a membrane, nucleus and "
             "cytoplasm. Cells divide to grow and repair an organism."),
    "photon": ("A photon is a quantum of light, a particle of electromagnetic "
               "radiation. It carries energy proportional to its frequency."),
    "pyramid": ("A pyramid is a structure with a square base and triangular sides. "
                "The Egyptian pyramids are ancient tombs made of stone."),
    "internet": ("The internet is a global network connecting computers. Data moves "
                 "in packets routed by protocols like TCP/IP between connected devices."),
    "energy": ("Energy is the ability to do work. It can be kinetic (motion), "
               "potential (stored), thermal, electrical. Energy is conserved — it "
               "changes form but is never lost."),
    "database": ("A database stores data in an organized way and lets you retrieve "
                 "it quickly. Tables hold records; SQL queries read and update them. "
                 "Indexes speed up searches."),
}

# англ. стоп-слова, чтобы не срабатывать на русских вопросах с латиницей (код и т.п.)
_EN_COMMON = ("what", "which", "how", "why", "who", "when", "where", "is", "are",
              "the", "a", "an", "of", "in", "on", "to", "for", "i", "you", "explain",
              "tell", "about", "that", "do", "does", "can", "please", "me", "my",
              "than", "there", "your", "it", "also", "not")

# тема -> ключевые англ. слова (основа)
_TOPIC_TEST = [
    ("neural", ("neural", "network", "perceptron", "machine learn", "deep learn")),
    ("algorithm", ("algorithm", "sort", "complexity", "procedure", "bubble")),
    ("memory", ("memory", "remember", "recall", "store info")),
    ("graph", ("graph", "node", "edge", "vertex", "connected")),
    ("dna", ("dna", "gene", "genetic", "heredit")),
    ("gravity", ("gravity", "gravitation", "fall", "attraction", "orbit")),
    ("cell", ("cell", "cell division", "organ", "nucleus", "tissue")),
    ("photon", ("photon", "light quantum", "electromagnetic")),
    ("pyramid", ("pyramid", "clamp", "tomb", "sphinx")),
    ("internet", ("internet", "web", "http", "network", "protocol")),
    ("energy", ("energy", "work", "kinetic", "potential", "electric", "power")),
    ("database", ("database", "table", "sql", "query", "record", "index")),
]


def _is_english_query(q):
    """Похож ли вопрос на английский. Один return: bool."""
    q = (q or "").strip()
    if not q:
        return False
    latin = sum(1 for c in q if 'a' <= c.lower() <= 'z')
    cyr = sum(1 for c in q if '\u0400' <= c <= '\u04FF')
    words = q.split()
    has_word = bool(words and len(words) > 1)
    # англ-вопрос: заметная доля латиницы, нет кириллицы, есть англ. маркер
    # для вопросов из 2+ слов порог 6 латинских символов остаётся,
    # для одиночного «what?» допускаем меньше
    enough_latin = latin > 6 or (has_word and latin >= 4)
    return (enough_latin and cyr == 0 and any(w in q.lower() for w in _EN_COMMON))


def try_english(query):
    """Точка входа: отвечает по-английски, если вопрос английский.
    Один return: str или None. None = вопрос не английский (нужно другое)."""
    if not _is_english_query(query):
        return None
    q_low = (query or "").lower()
    answer = None
    # поиск темы по ключевым словам
    for topic, keys in _TOPIC_TEST:
        if any(k in q_low for k in keys):
            answer = _EN_KB.get(topic)
            break
    if not answer:
        answer = ("I understood your question. I'm mainly trained on Russian. "
                  "Tell me the topic and I'll answer in simple English if I can.")
    return answer if answer else None


if __name__ == "__main__":
    print(try_english("what is a neural network?"))
    print(try_english("what is the fibonacci algorithm and its complexity?"))
    print(try_english("расскажи про нейрон"))  # русский — должно быть None