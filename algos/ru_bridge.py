# -*- coding: utf-8 -*-
"""Мост между русским вопросом и английской базой знаний.

Английская база (algos/english_kb.py, ~2270 тем) недоступна из русского:
её точка входа требует латиницу. Здесь — слой русских ключей: тема
английской базы -> слова, которыми о ней спрашивают по-русски.

Мост не переводит определения (переводчика в системе нет): он находит тему
и отдаёт её английское определение как источник фактов, а русскую
формулировку берёт из algos/module_knowledge (155 понятий) или из корпуса.

Запуск проверки:  python algos/ru_bridge.py "что такое память"
"""
import re
import sys

from algos.english_kb import _EN_KB
from algos.module_knowledge import _norm_q, _stem_ru, _KNOWLEDGE

# тема английской базы -> русские ключи (стемы сравниваются после _stem_ru)
RU_KEYS = {
    "memory": ("память", "запоминание"),
    "attention": ("внимание", "сосредоточенность"),
    "attentiveness": ("внимательность", "чуткость"),
    "curiosity": ("любопытство", "любознательность"),
    "insight": ("озарение", "инсайт", "догадка"),
    "wisdom": ("мудрость", "мудрый"),
    "reason": ("разум", "рассудок"),
    "reasoning": ("рассуждение", "умозаключение"),
    "intellect": ("интеллект", ),
    "intelligence": ("сообразительность", "смекалка"),
    "understanding": ("понимание", "осмысление"),
    "learning": ("обучение", "учёба", "изучение"),
    "doubt": ("сомнение", "сомневаться"),
    "uncertainty": ("неопределённость", "неуверенность"),
    "imagination": ("воображение", "фантазия"),
    "mind": ("ум", "сознание"),
    "anger": ("гнев", "злость"),
    "anxiety": ("тревога", "беспокойство"),
    "grief": ("горе", "скорбь"),
    "hope": ("надежда", "надеяться"),
    "joyfulness": ("радость", "веселье"),
    "calmness": ("спокойствие", "умиротворение"),
    "pride": ("гордость", ),
    "shame": ("стыд", ),
    "sorrow": ("печаль", "грусть"),
    "envy": ("зависть", ),
    "pleasure": ("удовольствие", ),
    "delight": ("восторг", "восхищение"),
    "enjoyment": ("наслаждение", ),
    "affection": ("привязанность", "нежность"),
    "friendship": ("дружба", "друг"),
    "trust": ("доверие", "доверять"),
    "honesty": ("честность", "честный"),
    "courage": ("смелость", "храбрость"),
    "patience": ("терпение", "терпеливость"),
    "diligence": ("прилежание", "старательность"),
    "generosity": ("щедрость", ),
    "gratitude": ("благодарность", "признательность"),
    "humility": ("смирение", ),
    "justice": ("справедливость", "правосудие"),
    "mercy": ("милосердие", "пощада"),
    "kindness": ("доброта", "добрый"),
    "loyalty": ("верность", "преданность"),
    "modesty": ("скромность", ),
    "sincerity": ("искренность", ),
    "tolerance": ("терпимость", "толерантность"),
    "prudence": ("благоразумие", "осмотрительность"),
    "temperance": ("умеренность", "воздержанность"),
    "wit": ("остроумие", "остроумный"),
    "humor": ("юмор", ),
    "beauty": ("красота", "прекрасное"),
    "truth": ("истина", "правда"),
    "honor": ("честь", "достоинство"),
    "duty": ("долг", "обязанность"),
    "freedom": ("свобода", "свободный"),
    "wealth": ("богатство", "богатый"),
    "poverty": ("бедность", "нищета"),
    "skill": ("навык", "умение"),
    "practice": ("практика", "упражнение"),
    "perception": ("восприятие", "ощущение"),
    "choice": ("выбор", "выбирать"),
    "peace": ("покой", "мир"),
    "time": ("время", "временной"),
    "space": ("пространство", "космос"),
    "ocean": ("океан", "океанский"),
    "forest": ("лес", "лесной"),
    "mountain": ("гора", "горы", "горный"),
    "river": ("река", "реки"),
    "sun": ("солнце", "солнечный"),
    "moon": ("луна", "лунный"),
    "star": ("звезда", "звёзды"),
    "light": ("свет", "освещение"),
    "music": ("музыка", "музыкальный"),
    "art": ("искусство", "художество"),
    "dream": ("сон", "сновидение"),
    "health": ("здоровье", "здоровый"),
    "illness": ("болезнь", "недуг"),
    "conscience": ("совесть", ),
    "decisiveness": ("решительность", "решимость"),
    "willpower": ("сила воли", "воля"),
    "safeguard": ("защита", "безопасность"),
    "workmanship": ("мастерство", "умение работать"),
    "docility_teachable": ("обучаемость", "восприимчивость"),
    "equanimity_mind": ("невозмутимость", "равновесие"),
    "awareness": ("осознанность", "осознание"),
    "reflection": ("рефлексия", "самоанализ"),
    "discernment": ("различение", "проницательность"),
    "inference_reasoning": ("вывод", "логический вывод"),
    "deduction_reasoning": ("дедукция", "логика"),
    "process": ("процесс", "процедура"),
    "task": ("задача", "задание"),
    "plan": ("план", "планирование"),
    "routine": ("рутина", "распорядок", "режим"),
    "upbringing": ("воспитание", ),
    "possibility": ("возможность", "возможности"),
    "achievement": ("достижение", "успех"),
    "character": ("характер", "нрав"),
    "priority": ("приоритет", "приоритеты"),
    "evidence": ("доказательство", "свидетельство", "улика"),
    "comfort": ("комфорт", "удобство"),
    "belonging": ("принадлежность", "причастность"),
    "contrast": ("контраст", "противопоставление"),
    "echo": ("эхо", "отголосок"),
    "breeze": ("бриз", "ветерок"),
    "humanity": ("человечество", "гуманность"),
    "determination": ("решимость", "настойчивость"),
    "integrity": ("целостность", "честность", "неподкупность"),
    "discipline": ("дисциплина", ),
    "fervour": ("пыл", "рвение"),
    "zest": ("азарт", "энтузиазм"),
    "mettle": ("мужество", "характер"),
    "vigilance": ("бдительность", ),
    "lenity": ("мягкость", "снисходительность"),
    "tenacity": ("упорство", "настойчивость"),
    "prowess": ("доблесть", "мастерство"),
    "sagacity": ("проницательность", "мудрость"),
    "resolution": ("решимость", "постановление"),
    "promise": ("обещание", ),
    "savvy": ("смекалка", "сообразительность"),
    "staunchness": ("стойкость", ),
    "merit": ("заслуга", "достоинство"),
    "devotion": ("преданность", "самоотдача"),
    "steadfastness": ("непоколебимость", "стойкость"),
    "dutifulness": ("исполнительность", ),
    "mirth": ("веселье", "смех"),
    "zeal": ("рвение", "усердие"),
    "assiduousness": ("усердие", "старательность"),
    "stamina": ("выносливость", ),
    "gentleness": ("мягкость", "кротость"),
    "quietness": ("тишина", "спокойствие"),
    "hardihood": ("отвага", "неустрашимость"),
    "benevolence": ("благожелательность", "доброжелательность"),
    "civility": ("вежливость", "гражданственность"),
    "moderation": ("умеренность", ),
    "tranquility": ("безмятежность", "спокойствие"),
    "nurturance": ("забота", "поддержка"),
    "serendipity": ("счастливая случайность", ),
    "warmth": ("теплота", "душевность"),
    "magnificence": ("великолепие", "величие"),
    "sageness": ("мудрость", ),
    "eloquence": ("красноречие", ),
    "earnestness": ("серьёзность", "искренность"),
    "pyramid": ("пирамида", ),
    "climate change": ("изменение климата", ),
    "sum": ("сумма", ),
    "repair": ("ремонт", "починка"),
    "packet": ("пакет", ),
    "scales": ("весы", "масштаб"),
    # уточнение имён: прежние брались из пар Викиданных и иногда означали
    # другое (жвачные вместо размышления, соматосенсорная вместо осязания)
    "ruminating": ("размышление", "обдумывание"),
    "fruiting": ("плодоношение", ),
    "acquaintance": ("знакомство", ),
    "adroitness": ("ловкость", "сноровка"),
    "forte": ("сильная сторона", ),
    "panache": ("шик", "молодечество"),
    "penetration": ("проницательность", ),
    "dissertation": ("диссертация", ),
    "suggest": ("предложение", ),
    "daydreaming": ("мечтательность", "грёзы"),
    "bond": ("узы", "связь"),
    "touch": ("осязание", ),
    "concentration": ("сосредоточенность", "концентрация"),
    "discrimination": ("различение", "дискриминация"),
    "storytelling": ("рассказывание историй", "сказительство"),
    "taste": ("вкус", ),
    "sight": ("зрение", ),
    "hearing": ("слух", ),
    # ещё несколько имён из пар Викиданных означали не то: merchandise — это
    # товар, а не мерчандайзинг, customs — обычаи, а не таможня
    "merchandise": ("товар", "товары"),
    "harangue": ("пышная речь", "витийство"),
    "handicraft": ("народный промысел", "рукоделие"),
    "customs": ("обычаи", "нравы"),
    "schooling": ("школьное обучение", ),
    "workmanship": ("мастерство работы", "отделка"),
    # имена, которые пришли из пар Викиданных и означали другое дело
    "regimentation": ("муштра", "казарменный порядок"),
    "lore": ("предания", "изустные знания"),
    "banter": ("пикировка", "шутливая перепалка"),
    "persuasion": ("убеждение", "уговаривание"),
    "intimacy": ("близость", "задушевность"),
    "soliloquy": ("разговор с собой", "самоговорение"),
    "inference_reasoning": ("умозаключение", "вывод"),
    "deduction_reasoning": ("дедукция", "вывод от общего к частному"),
    "interest": ("процент", "проценты"),
}

_QUESTION_STOP = {
    "что", "такое", "кто", "это", "как", "работает", "объясни", "объяснить",
    "расскажи", "про", "о", "об", "define", "значит", "означает", "такой",
    "такая", "такие", "есть", "ли", "мне", "для", "чем", "отличается",
}


def _stems(text):
    """Стеммы значимых слов запроса. Один return: list."""
    words = [w for w in _norm_q(text).split() if len(w) > 2 and w not in _QUESTION_STOP]
    return [_stem_ru(w) for w in words]


def _same_stem(left, right):
    """Одна ли основа у слов («дружба» и «дружбы»). Один return: bool.

    Раньше сравнивались первые шесть букв, поэтому «искусственный» сходился с
    «искусством», а «память» с «памятью» — нет. Теперь допускается только
    различие в окончании: |Δдлины| ≤ 3 и общий префикс не короче короткого
    слова минус две буквы.
    """
    word_a = (left or "").lower()
    word_b = (right or "").lower()
    if word_a == word_b:
        return True
    shorter, longer = (word_a, word_b) if len(word_a) <= len(word_b) else (word_b, word_a)
    prefix = 0
    for one, two in zip(shorter, longer):
        if one != two:
            break
        prefix += 1
    # окончание меняет не больше одной буквы; «искусство»/«искусственный» (Δ=2)
    # расходятся уже по словообразованию, а не по падежу
    close = abs(len(word_a) - len(word_b)) <= 1
    # основы сравниваем только у слов от пяти букв: у коротких «гора» и «горе»
    # расходятся в последней букве, но это разные слова, а не падежи
    return close and len(shorter) >= 5 and prefix >= len(shorter) - 1


def _hits(words, key_stems):
    """Сколько слов запроса попало в основы ключей. Один return: int."""
    return sum(1 for word in words if any(_same_stem(word, key) for key in key_stems))


def _text_keys():
    """Русские имена из первых слов описаний: имя -> тема. Один return: dict.

    Описания начинаются с русского названия («Фотон — квант…»), поэтому
    имя берётся до тире: так тема становится доступной из русского без
    отдельной записи в RU_KEYS.
    """
    from algos.ru_descriptions import RU_TEXT

    index = {}
    for topic, text in RU_TEXT.items():
        head = (text or "").split("—")[0].strip().lower()
        name = re.sub(r"[^а-яё\- ]", "", head).strip()
        if len(name) >= 3:
            index.setdefault(name, topic)
    return index


_TEXT_KEYS = _text_keys()


def find_topic(query):
    """Тема английской базы по русскому запросу. Один return: str/None."""
    stems = _stems(query)
    low = (query or "").lower()
    best = None
    best_hits = 0
    candidates = [(topic, keys) for topic, keys in RU_KEYS.items() if topic in _EN_KB]
    candidates += [(topic, (name,)) for name, topic in _TEXT_KEYS.items()]
    for topic, keys in candidates:
        # составное имя («база данных») ищем целой фразой: по словам оно
        # разваливается на «база» + «данных» и проигрывает другим темам
        phrase = any(" " in key and key.lower() in low for key in keys)
        hits = _hits(stems, [_stem_ru(key) for key in keys])
        score = 5 if phrase else hits
        if score > best_hits:
            best = topic
            best_hits = score
    return best


def _ru_index():
    """Индекс русских понятий module_knowledge по стемму темы. Один return: dict."""
    index = {}
    for entry in _KNOWLEDGE.values():
        if isinstance(entry, dict):
            topic = (entry.get("topic") or "").strip()
            if topic:
                index.setdefault(_stem_ru(_norm_q(topic)), entry)
    return index


_RU_BY_TOPIC = _ru_index()


def ru_definition(topic):
    """Русское описание понятия: готовый текст или module_knowledge. Один return: str/None."""
    from algos.ru_descriptions import RU_TEXT

    answer = RU_TEXT.get(topic)
    if answer is None:
        entry = None
        for key in RU_KEYS.get(topic, ()):
            entry = _RU_BY_TOPIC.get(_stem_ru(key))
            if entry:
                break
        if isinstance(entry, dict):
            what = (entry.get("what") or "").strip()
            example = (entry.get("ex") or "").strip()
            topic_ru = (entry.get("topic") or topic).strip()
            if what:
                answer = "%s — это %s." % (topic_ru, what)
                if example:
                    answer += " Например: %s." % example
    return answer


def bridge(query):
    """Русский ответ через понятие английской базы. Один return: dict/None.

    Молчит, если русского определения нет: английский текст как «ответ
    по-русски» не отдаём — пусть цепочка пробует граф и корпус.
    """
    topic = find_topic(query)
    answer = ru_definition(topic) if topic else None
    return {"topic": topic, "content": answer, "strategy": "ru_bridge"} if answer else None


def _topics_in(query):
    """Все понятия базы, чьи русские ключи есть в запросе. Один return: list."""
    stems = _stems(query)
    scored = []
    for topic, keys in RU_KEYS.items():
        if topic in _EN_KB:
            hits = _hits(stems, [_stem_ru(key) for key in keys])
            if hits:
                scored.append((hits, topic))
    for name, topic in _TEXT_KEYS.items():
        hits = _hits(stems, [_stem_ru(name)])
        if hits:
            scored.append((hits, topic))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    unique = []
    for _, topic in scored:
        if topic not in unique:
            unique.append(topic)
    return unique


def _ru_label(topic):
    """Русская подпись понятия: ключ моста, имя из описания или тема. Один return: str."""
    keys = RU_KEYS.get(topic) or ()
    label = keys[0] if keys else None
    if label is None:
        names = [name for name, owner in _TEXT_KEYS.items() if owner == topic]
        label = names[0] if names else topic
    return label


def related(query):
    """Ответ про связи понятий: сравнение двух или окружение одного. Один return: dict/None."""
    from algos.concept_graph import EDGES_CONTRAST, EDGES_MENTION, neighbours

    topics = _topics_in(query)
    answer = None
    if len(topics) >= 2:
        first, second = topics[0], topics[1]
        contrasted = (second in EDGES_CONTRAST.get(first, [])
                      or first in EDGES_CONTRAST.get(second, []))
        mentioned = (second in EDGES_MENTION.get(first, [])
                     or first in EDGES_MENTION.get(second, []))
        left, right = ru_definition(first), ru_definition(second)
        if left and right:
            # в каждом заголовке есть слово о различии: итоговый гейт сравнений
            # иначе не считает ответ сравнением и гасит его целиком
            head = "Прямой связи в базе нет: это разные понятия, и вот чем они различаются."
            if contrasted:
                head = "В базе они прямо противопоставлены, то есть различаются."
            elif mentioned:
                head = "В базе они связаны между собой, хотя и различаются."
            answer = "%s\n\n«%s»: %s\n\n«%s»: %s" % (
                head, _ru_label(first), left, _ru_label(second), right)
        elif contrasted:
            answer = ("«%s» и «%s» в базе различаются: это разные понятия, "
                      "и определение одного прямо противопоставлено другому."
                      % (_ru_label(first), _ru_label(second)))
        else:
            answer = ("Прямого противопоставления между «%s» и «%s» в базе нет."
                      % (_ru_label(first), _ru_label(second)))
    elif len(topics) == 1:
        topic = topics[0]
        near = neighbours(topic, depth=1)[:6]
        if near:
            labels = ", ".join("«%s»" % _ru_label(name) if name in RU_KEYS else name
                               for name in near)
            answer = "С понятием «%s» в базе связаны: %s." % (_ru_label(topic), labels)
    return {"topic": topics[0] if topics else None,
            "content": answer, "strategy": "ru_links"} if answer else None


def main(argv):
    """Проверка из командной строки. Один return: int."""
    query = " ".join(argv) or "что такое память"
    found = bridge(query)
    print("topic:", (found or {}).get("topic"))
    print("answer:", (found or {}).get("content"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
