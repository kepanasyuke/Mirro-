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
    "robot": ("A robot is a machine that follows programmed instructions to perform "
              "tasks, often in physical space. Robots combine sensors, motors and "
              "control logic. They help in industry, medicine and daily life."),
"bacteria": ("Bacteria are tiny single-celled organisms. Many are harmless or "
                 "helpful (digestion, fermentation), while some cause disease. They "
                 "reproduce by dividing."),
    "light": ("Light is electromagnetic radiation that travels in waves. It can be "
              "described as photons. Light carries energy and lets us see; its speed "
              "in vacuum is fixed."),
    "genetics": ("Genetics is the study of heredity and how traits pass from parents "
                 "to offspring through genes. DNA carries the instructions; mutations "
                 "and inheritance shape variation."),
    "stem cell": ("Stem cells are unspecialized cells that can develop into different "
                  "cell types. They help repair tissues and are studied for potential "
                  "regenerative therapies."),
    "illness": ("Illnesses are conditions that disrupt normal body function. They can "
                "be infectious (caused by pathogens) or non-infectious (like allergies). "
                "Prevention, hygiene and medicine help manage them."),
    "programming": ("Programming means writing instructions that a computer runs. "
                    "Code in languages like Python is translated so the machine can "
                    "execute it step by step to solve tasks."),
    "operating system": ("An operating system (OS) manages hardware and programs. "
                         "It handles files, memory and processes. Examples are Linux "
                         "and Windows."),
    "photosynthesis": ("Photosynthesis is how green plants make food from sunlight. "
                       "They take in water and carbon dioxide and, using light energy, "
                       "produce glucose and oxygen."),
    "climate change": ("Climate change is the long-term shift in global temperatures "
                       "and weather patterns. Human activity, mainly burning fossil "
                       "fuels, adds greenhouse gases that warm the planet."),
    "wave": ("A wave is a disturbance that carries energy through a medium or space. "
             "Sound and light travel as waves; their frequency and wavelength "
             "determine pitch and color."),
    "biology": ("Biology is the science of living things. It studies cells, "
                "organisms, genetics and ecosystems, from tiny bacteria to "
                "whole environments and how life changes over time."),
    "weather": ("Weather is the short-term state of the atmosphere: temperature, "
                "rain, wind and clouds on a given day. It changes quickly, unlike "
                "climate, which describes long-term trends."),
    "space": ("Space is the region beyond Earth's atmosphere. It holds stars, "
              "planets, galaxies and emptiness. Stars are born, live and die, "
              "and gravity shapes their motion."),
    "history": ("History is the study of the human past through records and "
                "artifacts. It examines events, civilizations and change over "
                "time to understand how societies developed."),
}

# англ. стоп-слова, чтобы не срабатывать на русских вопросах с латиницей (код и т.п.)
_EN_COMMON = ("what", "which", "how", "why", "who", "when", "where", "is", "are",
              "the", "a", "an", "of", "in", "on", "to", "for", "i", "you", "explain",
              "tell", "about", "that", "do", "does", "can", "please", "me", "my",
              "than", "there", "your", "it", "also", "not", "could", "would",
              "should", "know", "want", "what's", "how's", "define", "mean",
              "actually", "basically", "rather", "however", "maybe", "perhaps",
              "still", "though", "well")


_EN_MARKER_SET = frozenset(_EN_COMMON)

# тема -> ключевые англ. слова (основа)
_TOPIC_TEST = [
    ("neural", ("neural", "network", "perceptron", "machine learn", "deep learn", "neuron", "gradient", "backprop")),
    ("algorithm", ("algorithm", "sort", "complexity", "procedure", "bubble", "search", "data structure")),
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
    ("robot", ("robot", "machine", "automation", "automaton", "mechatronic")),
    ("bacteria", ("bacteria", "microbe", "microorganism", "germ", "single-celled")),
    ("light", ("light", "photon", "electromagnetic radiation", "optics", "wavelength")),
    ("psychology", ("psychology", "mind", "behavior", "behaviour", "brain", "cognition")),
    ("genetics", ("genetics", "gene", "heredity", "dna", "inheritance", "chromosome")),
    ("stem cell", ("stem cell", "stem cells", "regenerative", "unspecialized")),
    ("illness", ("illness", "disease", "infection", "disorder", "allergy")),
    ("programming", ("programming", "code", "program", "python", "compiler", "source")),
    ("operating system", ("operating system", "os", "kernel", "linux", "windows", "files")),
    ("photosynthesis", ("photosynthesis", "chlorophyll", "glucose", "oxygen", "plants")),
    ("climate change", ("climate change", "global warming", "greenhouse", "carbon dioxide", "emissions")),
    ("wave", ("wave", "sound", "frequency", "amplitude", "wavelength")),
    ("biology", ("biology", "organism", "species", "ecosystem", "living")),
    ("weather", ("weather", "rain", "wind", "temperature", "forecast", "climate")),
    ("space", ("space", "star", "galaxy", "planet", "universe", "orbit")),
    ("history", ("history", "ancient", "civilization", "empire", "medieval", "era"))
]


def _is_english_query(q):
    """Похож ли вопрос на английский. Минимальная длина латиницы — 6 символов
    (чтобы одиночные «what?/hi» не срабатывали). Не-строка → False.
    Один return: bool."""
    if not isinstance(q, str):
        return False
    q = (q or "").strip()
    if not q:
        return False
    latin = sum(1 for c in q if 'a' <= c.lower() <= 'z')
    cyr = sum(1 for c in q if '\u0400' <= c <= '\u04FF')
    words = q.split()
    # англ-вопрос: заметная доля латиницы (>=6), нет кириллицы, есть англ. маркер.
    # Одиночное «what?/hi» игнорируются (нет латинских слов повсюду ≥4)
    has_full_word = any(len(w) >= 4 for w in words if w.isalpha())
    enough_latin = latin >= 6 and has_full_word
    # англ. маркер должен быть отдельным словом, а не частью большего
    # (снимаем хвостовую пунктуацию, чтобы «why?» матчилось как «why»)
    toks = {w.strip(".,!?;:'\"()") for w in q.lower().split()}
    has_marker = bool(toks & _EN_MARKER_SET)
    return (enough_latin and cyr == 0 and has_marker)


def try_english(query):
    """Точка входа: отвечает по-английски, если вопрос английский.
    Пустой/не-строковый/слишком короткий запрос → None. Один return: str/None.
    None = вопрос не англ. (нужно другое)."""
    if not isinstance(query, str) or len(query.strip()) < 6:
        return None
    if not _is_english_query(query):
        return None
    if not isinstance(_EN_KB, dict):
        return None
    q_low = (query or "").lower()
    answer = None
    # поиск темы по ключевым словам; при нескольких совпадениях выбираем тему с
# самым длинным совпавшим ключом (чтобы «stem cell» не съедала «cell»)
    topics_test = _TOPIC_TEST if isinstance(_TOPIC_TEST, (list, tuple)) else []
    best_len = -1
    for topic, keys in topics_test:
        for k in (keys or []):
            if isinstance(k, str) and k and k in q_low and len(k) > best_len:
                best_len = len(k)
                answer = _EN_KB.get(topic)
    # fallback: прямое вхождение ключа-темы как отдельного слова
    if not answer:
        q_toks = set()
        for t in q_low.replace("-", " ").split():
            w = t.strip(".,!?;:'\"()")
            if w:
                q_toks.add(w)
        for topic in _EN_KB:
            if isinstance(topic, str) and topic and topic in q_toks:
                answer = _EN_KB.get(topic)
                break
    if not answer and _EN_KB:
        answer = ("I understood your question. I'm mainly trained on Russian. "
                  "Tell me the topic and I'll answer in simple English if I can.")
    return (answer if isinstance(answer, str) and answer else None)


if __name__ == "__main__":
    print(try_english("what is a neural network?"))
    print(try_english("what is the fibonacci algorithm and its complexity?"))
    print(try_english("расскажи про нейрон"))  # русский — должно быть None