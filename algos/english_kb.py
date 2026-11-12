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
    "ocean": ("The ocean is the vast body of salt water covering most of Earth. "
              "It has currents, tides and layers, and hosts huge marine ecosystems "
              "from coral reefs to deep trenches."),
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
    "voting": ("Voting is how a group makes a decision by letting each member "
               "choose an option. It can be by ballot, show of hands or online; "
               "the most chosen outcome usually wins."),
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
    "time": ("Time is the continuous progression of events from past to future. "
             "We measure it in seconds, minutes and hours; clocks and calendars "
             "help us organize and compare durations."),
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
    "literature": ("Literature is written artistic work such as novels, poetry "
                   "and plays. It uses language to express ideas, emotions and "
                   "stories, reflecting culture and imagination."),
    "trade": ("Trade is the exchange of goods and services between people or "
              "countries. It relies on money, transport and markets, and lets "
              "regions specialize in what they produce best."),
    "art": ("Art is the expression of ideas and emotions through visual or "
            "performing forms like painting, sculpture and music. It reflects "
            "culture, creativity and the human experience."),
    "music": ("Music is organized sound made with voice or instruments. Melody, "
              "harmony and rhythm come together in songs and pieces that express "
              "emotion across cultures."),
    "election": ("An election is the process by which people choose a leader or "
                 "representative. Voters cast ballots, results are counted, and "
                 "the candidate with the most support wins the role."),
    "math": ("Math is the study of numbers, shapes and patterns. Arithmetic, "
             "algebra and geometry are its branches. It solves problems with "
             "logical steps and exact rules."),
    "chess": ("Chess is a board game for two players. Each controls sixteen "
              "pieces with different moves; the goal is to checkmate the "
              "opponent's king through strategy and tactics."),
    "geology": ("Geology is the science of the Earth: its rocks, minerals and "
                "layers, and the forces like volcanoes and erosion that shape "
                "its surface over long periods of time."),
    "philosophy": ("Philosophy is the study of fundamental questions about "
                   "existence, knowledge, values and reason. It uses careful "
                   "argument and reflection instead of experiment alone."),
    "sum": ("A sum is the result of adding numbers together. For 3 + 5 the sum "
            "is 8; order does not change it. Sums appear in counting, totals "
            "and averages all across math."),
    "health": ("Health is the state of being physically and mentally well. "
               "Good sleep, nutrition and exercise support it, while illness "
               "and stress can weaken it."),
    "economy": ("Economy is how people produce, trade and use goods and money. "
                "Markets, prices, supply and demand, and national budgets shape "
                "wealth and choices in society."),
    "astronomy": ("Astronomy is the study of everything beyond Earth: stars, "
                  "planets, galaxies and the universe. It uses telescopes and "
                  "physics to understand how celestial objects move and evolve."),
    "botany": ("Botany is the science of plants. It studies leaves, roots and "
               "flowers, how plants grow and make food through photosynthesis, "
               "and their role in ecosystems and food chains."),
    "city": ("A city is a large, densely populated settlement with homes, "
             "businesses and services. People live close together and share "
             "transport, schools, shops and public infrastructure."),
"zoology": ("Zoology is the science of animals. It studies their bodies, "
                 "behavior and habitats, how they adapt and live in groups, "
                 "from tiny insects to large mammals."),
    "country": ("A country is a land with its own government, borders and laws. "
                "People share a common history and culture within it. Countries "
                "trade, cooperate and sometimes compete with each other."),
    "moon": ("The Moon is Earth's natural satellite. It orbits Earth and its "
             "gravity causes tides. Sunlight reflects from it, giving us "
             "phases from new moon to full moon."),
    "magnet": ("A magnet attracts iron and other magnets. It has two poles, "
               "north and south; opposite poles pull together and like poles "
               "push apart. Magnetism powers motors and compasses."),
    "volcano": ("A volcano is an opening in Earth's crust that lets magma, ash "
                "and gases escape. When it erupts, lava flows out and builds new "
                "land; some volcanoes are active, others dormant or extinct."),
    "island": ("An island is a piece of land surrounded by water. It can be big "
               "or small, formed by volcanoes, reefs or rising land. Islands "
               "have unique plants and animals."),
    "skyscraper": ("A skyscraper is a very tall building with many floors. "
                   "Steel frames and elevators let towers rise high in cities, "
                   "packing offices and homes into a small footprint."),
    "desert": ("A desert is a dry region that gets very little rain. It can be "
               "hot or cold, with sand, rock or ice. Plants and animals there "
               "adapt to save water and survive extreme heat or cold."),
    "journey": ("A journey is travel from one place to another. People travel "
                "for work, family or discovery, by foot, road, sea or air. "
                "Journeys can be short trips or long adventures."),
    "river": ("A river is a natural stream of water flowing toward a sea, lake "
              "or another river. It shapes valleys, carries nutrients and "
              "supplies water that people and wildlife depend on."),
    "wheat": ("Wheat is a cereal crop grown for its grain, which is milled into "
              "flour for bread, pasta and many foods. It is one of the most "
              "important crops in the world."),
    "forest": ("A forest is a large area covered with trees and other plants. "
               "It gives oxygen, shelters wildlife and cools the climate. Many "
               "animals and people depend on forests for food and shelter."),
    "lake": ("A lake is a large body of water surrounded by land. It can be "
             "fresh or salty, fed by rivers and rain. Lakes store water, "
             "support wildlife and are used for fishing and recreation."),
    "hill": ("A hill is a raised area of land, lower and gentler than a mountain. "
             "Hills are formed by erosion, glaciers or volcanoes. They give good "
             "views and are common in rolling countryside."),
    "coal": ("Coal is a black, burnable rock formed from ancient plants under "
             "heat and pressure. For centuries it has fuelled power plants and "
             "industry, though it releases carbon dioxide when burned."),
    "meteor": ("A meteor is a streak of light in the sky caused by a small space "
               "rock burning up in Earth's atmosphere. If a piece survives and "
               "lands, it is called a meteorite."),
    "comet": ("A comet is a small icy body from the outer solar system. Near the "
              "Sun, heat turns its ice into gas and dust, forming a bright head "
              "and a long glowing tail."),
    "glacier": ("A glacier is a slow-moving mass of ice formed where snow piles "
                "up and compresses over many years. It flows downhill, carving "
                "valleys and reshaping the landscape as it melts."),
    "plan": ("A plan is an organized set of steps toward a goal. It lists what "
             "to do, when, and how. Good plans are flexible and are updated as "
             "situations change or new information appears."),
    "routine": ("A routine is a regular, repeated way of doing something. Daily "
                "habits like waking, eating and studying form a routine that "
                "saves time and brings stability to life."),
    "upbringing": ("Upbringing is how a child is raised and guided by family. "
                   "It includes values, habits and education learned at home, "
                   "shaping character and how a person deals with the world."),
    "memory": ("Memory is the ability to store and recall information. Working "
               "memory holds what we use now; long-term memory keeps facts and "
               "skills over time. Repetition and rest help strengthen it."),
    "society": ("A society is a group of people living together and sharing "
                "rules, culture and institutions. People cooperate through "
                "laws, work and trade to meet common needs and goals."),
    "souvenir": ("A souvenir is an object kept to remember a place, event or "
                 "person. People buy them while traveling as a reminder of "
                 "experiences or to give as small gifts."),
    "possibility": ("A possibility is something that may happen or be true. "
                    "It is an option or chance among several outcomes. We weigh "
                    "probabilities to decide how likely a possibility is."),
    "dialogue": ("A dialogue is a conversation between two or more people. "
                 "Speakers take turns sharing ideas and questions. Good "
                 "dialogue builds understanding and resolves disagreements."),
    "achievement": ("An achievement is something accomplished through effort or "
                    "skill, like finishing a goal or passing a test. It brings "
                    "a sense of progress and is often recognized by others."),
    "character": ("A character is the set of qualities that define how a person "
                  "thinks, feels and acts. Honesty, patience and courage are "
                  "parts of it; character is shaped by choices and experience."),
    "priority": ("A priority is what matters most and should be done first. "
                 "When resources or time are limited, priority helps decide "
                 "the order of tasks and where to focus attention."),
    "reaction": ("A reaction is a response to an event, word or change. In "
                 "chemistry it is a process where substances change into others. "
                 "In life, a reaction shows how someone feels or acts."),
    "horizon": ("The horizon is the line where the sky seems to meet the ground "
                "or sea. It is an apparent edge created by the curvature of the "
                "Earth, and it shifts as the viewer moves or height changes."),
    "scales": ("Scales are tools or systems for measuring or weighing. A balance "
               "compares masses; rating scales order opinions or sizes. In music "
               "and in charts, scales set the steps between values."),
    "treasure": ("Treasure is a collection of valuable things, such as gold, gems "
                 "or precious objects. It can be buried, found or inherited, and "
                 "it holds worth to both its owners and historians."),
    "motion": ("Motion is the change in position of an object over time. Speed "
               "and direction describe it; acceleration changes motion. Forces "
               "like gravity and push cause objects to start, stop or turn."),
    "task": ("A task is a piece of work to be done, with a clear goal or outcome. "
             "Tasks can be small or large, personal or shared. Breaking work "
             "into tasks makes big jobs easier to manage."),
    "machinery": ("Machinery is a set of machines that do work using power. "
                  "It can include engines, tools and equipment in factories or "
                  "farms. Machines multiply human strength and speed up tasks."),
    "orbit": ("An orbit is the curved path an object takes around another in space. "
              "Planets orbit stars and moons orbit planets, held by gravity. "
              "Orbits can be round or oval and take different amounts of time."),
    "repair": ("A repair is the act of fixing something that is broken or worn. "
               "It may be done by replacing parts, joining pieces or tuning "
               "settings. Repairing saves resources and extends what we use."),
    "process": ("A process is a series of steps that turn inputs into a result. "
                "Workflows, chemical reactions and learning are all processes. "
                "Understanding each step helps improve speed and quality."),
    "packet": ("A packet is a unit of data sent over a network. Messages are "
               "split into packets that travel through routers and are reordered "
               "at the destination. This makes transfer reliable and efficient."),
    "evidence": ("Evidence is information that supports a claim or conclusion. "
                 "It can be facts, data, observations or documents. Strong "
                 "evidence helps people judge what is true and decide wisely."),
"complaint": ("A complaint is when someone says they are unhappy with a "
                   "product, service or situation. It raises a problem so it can "
                   "be examined and fixed. Fair complaints lead to improvements."),
    "comfort": ("Comfort is a pleasant feeling of ease and well-being. It comes "
                "from cozy places, kind words or safety. Comfort helps people "
                "relax, recover and feel at home in a situation."),
    "correction": ("A correction is a change that fixes a mistake or error. It "
                   "can apply to writing, data, behavior or a course of action. "
                   "Making corrections improves accuracy and helps prevent future "
                   "errors."),
    "perception": ("Perception is how we take in and interpret the world through "
                   "the senses. Sight, hearing and touch give signals that the "
                   "brain turns into meaning; you can be active literal or "
                   "shaped by experience."),
    "universe": ("The universe is everything that exists: all matter, energy, "
                 "space and time. It holds galaxies, stars and planets and has "
                 "been expanding since the Big Bang about 14 billion years ago."),
    "skill": ("A skill is an ability to do something well, learned through "
              "practice and experience. It can be practical, social or mental. "
              "Skills grow with training and open doors to new tasks and jobs."),
    "migration": ("Migration is the movement of people or animals from one place "
                  "to another. People migrate for work, safety or family; birds "
                  "and fish migrate with seasons to find food and climate."),
    "belonging": ("Belonging is the feeling of being accepted and connected to a "
                  "group, place or community. It comes from shared identity and "
                  "trust, and it gives people a sense of security and purpose."),
    "balance": ("Balance is the state of being steady and even. A scale balances "
                "weights, and our bodies balance while we walk. In life, balance "
                "means giving time and energy to different needs fairly."),
    "contrast": ("Contrast is the difference between two things, ideas or colors. "
                 "It makes them easier to tell apart and highlights their features. "
                 "Contrast is used in design, in writing and in comparing choices."),
    "torque": ("Torque is a rotational force that makes an object spin. It equals "
               "force multiplied by the distance from the pivot. Torque turns "
               "wheels, tightens bolts and powers many machines."),
    "questionnaire": ("A questionnaire is a set of written questions used to "
                      "collect information from people. It can be on paper or "
                      "online, with closed or open answers. Analysis of replies "
                      "helps research and decision-making."),
    "manual": ("A manual is a book or guide that explains how to use or fix "
               "something. It gives step-by-step instructions, warnings and "
               "tips. Manuals help both beginners and experts work correctly."),
    "echo": ("An echo is a reflected sound that returns after hitting a surface. "
             "Hearing it depends on distance and time; echoes help ships measure "
             "depth and bats navigate in the dark. They reveal the shape around us."),
    "fermentation": ("Fermentation is a natural process where microorganisms break "
                     "down sugars into alcohol, gases or acids. It preserves food, "
                     "adds flavor and is used to make bread, yogurt and beer."),
    "recipe": ("A recipe is a set of instructions for preparing a dish or drink. "
               "It lists ingredients, amounts and steps in order. Following a "
               "recipe carefully helps get a consistent, tasty result."),
    "breeze": ("A breeze is a gentle wind, softer than a gale. It moves leaves, "
               "spreads smells and cools the air on warm days. Breezes can be "
               "steady and light or come in short gusts."),
    "storm": ("A storm is a violent weather event with strong winds, rain, snow "
              "or thunder. It can bring lightning and flooding. Storms form when "
              "warm and cold air meet; they vary from mild to severe."),
    "cactus": ("A cactus is a plant adapted to dry deserts. Its thick stem stores "
               "water, and spines reduce water loss and guard it from animals. "
               "Cacti flower and some live for many decades."),
    "dawn": ("Dawn is the time of day when the sky grows light before sunrise. "
             "It comes with soft colors and quiet calm. Dawn marks the beginning "
             "of a new day and the start of daily routines."),
    "contradiction": ("A contradiction happens when two statements cannot both be "
                      "true at the same time. Spotting contradictions helps find "
                      "errors in logic and forces us to rethink ideas."),
    "vacuum": ("A vacuum is a space with very little or no matter inside. Sound "
               "cannot travel through a perfect vacuum, and objects fall freely "
               "in it. Vacuums are used in bulbs, packaging and scientific tools."),
    "silence": ("Silence is the absence of sound or noise. It can bring calm and "
                "focus, or it can feel awkward in conversation. In music, rests "
                "and quiet pauses shape rhythm and mood just like the notes do."),
}

# англ. стоп-слова, чтобы не срабатывать на русских вопросах с латиницей (код и т.п.)
_EN_COMMON = ("what", "which", "how", "why", "who", "when", "where", "is", "are",
              "the", "a", "an", "of", "in", "on", "to", "for", "i", "you", "explain",
              "tell", "about", "that", "do", "does", "can", "please", "me", "my",
              "than", "there", "your", "it", "also", "not", "could", "would",
              "should", "know", "want", "what's", "how's", "define", "mean",
              "actually", "basically", "rather", "however", "maybe", "perhaps",
              "still", "though", "well", "since", "because", "before", "after",
              "always", "usually", "often", "sometimes", "many", "much")


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
    ("history", ("history", "ancient", "civilization", "empire", "medieval", "era")),
    ("literature", ("literature", "novel", "poem", "poetry", "author", "genre")),
    ("art", ("art", "painting", "sculpture", "music", "artist", "canvas", "color")),
    ("music", ("music", "melody", "harmony", "rhythm", "song", "instrument", "guitar")),
    ("math", ("math", "algebra", "arithmetic", "geometry", "fraction", "equation")),
    ("chess", ("chess", "checkmate", "rook", "queen", "knight", "pawn", "board")),
    ("geology", ("geology", "rock", "mineral", "mantle", "crust", "volcano", "erosion")),
    ("philosophy", ("philosophy", "ethics", "logic", "existence", "knowledge", "reason")),
    ("health", ("health", "nutrition", "exercise", "sleep", "wellness", "immune")),
    ("economy", ("economy", "market", "money", "inflation", "trade", "budget", "price")),
    ("astronomy", ("astronomy", "planet", "star", "galaxy", "nebula", "telescope", "comet")),
    ("botany", ("botany", "plant", "leaf", "root", "flower", "photosynthesis", "tree")),
    ("zoology", ("zoology", "animal", "mammal", "insect", "bird", "habitat", "reptile")),
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