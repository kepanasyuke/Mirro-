# -*- coding: utf-8 -*-
"""Мост между русским вопросом и английской базой знаний Mirro.

Английская база (`algos/english_kb.py`, 2241 тема) знает понятия, но отвечает
только на английские вопросы: вход закрыт проверкой `_is_english_query`.

Мост работает в два слоя:
1. **Настоящие пары RU→EN** из `data/bilingual_map.json` (собираются
   `scripts/build_bilingual_map.py` по интервики Википедии) — так «мудрость»
   находит `wisdom`, а не «висдом».
2. **Транслитерация** как резерв для заимствований: «алгоритм» → `algorithm`.

Ответ всегда по-русски. Если понятие знает русский граф — отвечает он; если нет,
берём английское определение, сжимаем до пары фраз и явно помечаем источник.
Переводчик не подключён, поэтому английский текст не выдаётся за русский.
"""
import json
import re as _re
from pathlib import Path

from algos.english_kb import _EN_KB

# Диграфы обрабатываются до отдельных букв, иначе «sh» станет «сх»
_PAIRS = (("sh", "ш"), ("ch", "ч"), ("th", "т"), ("ph", "ф"),
          ("ya", "я"), ("yu", "ю"), ("kh", "х"), ("zh", "ж"))

_LETTERS = {"a": "а", "b": "б", "c": "к", "d": "д", "e": "е", "f": "ф",
            "g": "г", "h": "х", "i": "и", "j": "дж", "k": "к", "l": "л",
            "m": "м", "n": "н", "o": "о", "p": "п", "q": "к", "r": "р",
            "s": "с", "t": "т", "u": "у", "v": "в", "w": "в", "x": "кс",
            "y": "и", "z": "з"}

_LATIN = _re.compile(r"[a-zA-Z]")
_PARENS = _re.compile(r"\s*\(.*?\)\s*$")

_DEFINITION_MARKERS = ("что такое", "что значит", "что означает", "объясни",
                       "расскажи про", "поясни", "определение", "что за")

_ALIASES = None
_RU_TO_EN = None
_EN_TO_RU = None
_STEMS = None

MAP_PATH = Path(__file__).resolve().parents[1] / "data" / "bilingual_map.json"


def transliterate(word):
    """Русская запись латинского слова по простым правилам. Один return: str."""
    text = (word or "").lower()
    for src, dst in _PAIRS:
        text = text.replace(src, dst)
    return "".join(_LETTERS.get(ch, ch) for ch in text)


def build_aliases():
    """Карта «русская запись → английская тема» для заимствованных понятий.
    Один return: dict."""
    aliases = {}
    for topic in _EN_KB:
        if not isinstance(topic, str):
            continue
        ru = transliterate(topic)
        if ru and ru != topic and ru not in aliases:
            aliases[ru] = topic
    return aliases


def aliases():
    """Ленивая карта алиасов (строится один раз). Один return: dict."""
    global _ALIASES
    if _ALIASES is None:
        _ALIASES = build_aliases()
    return _ALIASES


def _load_pairs():
    """Пары из data/bilingual_map.json: (RU→EN, EN→RU). Один return: tuple."""
    ru_to_en = {}
    en_to_ru = {}
    try:
        data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ru_to_en, en_to_ru
    for en, ru in (data.get("map") or {}).items():
        if not isinstance(ru, str) or "значения" in ru.lower():
            continue
        name = _PARENS.sub("", ru).strip().lower()
        if not name or len(name) < 3:
            continue
        ru_to_en.setdefault(name, []).append(en)
        en_to_ru.setdefault(en, name)
    return ru_to_en, en_to_ru


def pairs():
    """Ленивые пары RU→EN и EN→RU. Один return: tuple (dict, dict)."""
    global _RU_TO_EN, _EN_TO_RU
    if _RU_TO_EN is None:
        _RU_TO_EN, _EN_TO_RU = _load_pairs()
    return _RU_TO_EN, _EN_TO_RU


def _stem_map():
    """Индекс по первым пяти буквам русских названий. Один return: dict."""
    global _STEMS
    if _STEMS is None:
        stems = {}
        for name, topics in pairs()[0].items():
            if len(name) >= 5:
                stems.setdefault(name[:5], []).extend(topics)
        _STEMS = stems
    return _STEMS


def _by_prefix():
    """Индекс русских названий по первым пяти буквам. Один return: dict."""
    global _STEMS
    if _STEMS is None:
        index = {}
        for name in pairs()[0]:
            if len(name) >= 5:
                index.setdefault(name[:5], []).append(name)
        _STEMS = index
    return _STEMS


def _same_word_form(word, name):
    """Одна и та же лемма в разных формах: отличаются только окончанием.
    «мудрость»/«мудрости» — да; «искусство»/«искусственный» — нет.
    Один return: bool."""
    shorter, longer = (word, name) if len(word) <= len(name) else (name, word)
    if word == name:
        return True
    prefix = 0
    for left, right in zip(shorter, longer):
        if left != right:
            break
        prefix += 1
    # окончание меняет не больше одной буквы; «искусство»/«искусственный» (Δ=2)
    # расходятся по словообразованию, а не по падежу
    return abs(len(word) - len(name)) <= 1 and prefix >= len(shorter) - 1


def russian_name(topic):
    """Русское название английской темы по карте. Один return: str."""
    name = pairs()[1].get(topic)
    return name or transliterate(topic)


def _topics_for(word):
    """Английские темы для русского слова (точное совпадение, затем словоформа).
    Один return: list."""
    ru_to_en = pairs()[0]
    found = list(ru_to_en.get(word) or ())
    if not found and len(word) >= 5:
        names = [name for name in _by_prefix().get(word[:5], ())
                 if _same_word_form(word, name)]
        found = [topic for name in names[:1] for topic in (ru_to_en.get(name) or ())]
    return found


def _in_compound(query, word):
    """Слово — только часть дефисного сложного слова: «функция» в «хеш-функция»."""
    for part in _re.split(r"[\s,.;:!?()«»\"']+", (query or "").lower()):
        if "-" in part and part != word and word in part.split("-"):
            return True
    return False


def find_concept(query):
    """Английская тема, на которую указывает русское слово в запросе.
    Сначала настоящие пары, затем транслитерация. Один return: str или None."""
    words = [word for word in _re.findall(r"[а-яё]{3,}", (query or "").lower())
             if not _in_compound(query, word)]
    found = [(len(word), _topics_for(word)[0])
             for word in words if _topics_for(word)]
    legacy = [(len(word), aliases().get(word))
              for word in words if not _topics_for(word) and aliases().get(word)]
    found.extend(legacy)
    found.sort(reverse=True)
    return found[0][1] if found else None


def _explain_first(kg, names):
    """Первое непустое объяснение из списка имён. Один return: str или None."""
    texts = [kg.explain(name) for name in names if name]
    found = [text for text in texts if text]
    return found[0] if found else None


def summarize(text, limit=320):
    """Сжимает английское определение до 1–2 фраз. Один return: str или None."""
    clean = " ".join((text or "").split())
    if not clean:
        return None
    cut = clean[:limit]
    dot = cut.rfind(".")
    result = cut[:dot + 1] if dot > 120 else cut.rstrip(" ,;:") + "…"
    return result


_GRAPH_READY = False


def _ensure_graph():
    """Подгружает граф знаний из models/knowledge_graph.pkl один раз.
    Граф нужен как фильтр: связанным считается понятие, которое мозг уже знает."""
    global _GRAPH_READY
    if not _GRAPH_READY:
        _GRAPH_READY = True
        from algos.knowledge_graph import kg
        if not kg.nodes:
            try:
                kg.load(str(Path(__file__).resolve().parents[1] / "models" / "knowledge_graph.pkl"))
            except Exception:
                pass


def related_concepts(topic, limit=3):
    """Русские понятия, на которые ссылается английское определение.
    Работает как один шаг вывода между языками: текст → слова → темы → русские имена.
    Один return: list русских названий."""
    text = (_EN_KB.get(topic) or "").lower()
    words = _re.findall(r"[a-z]{4,}", text)
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    ru_to_en, en_to_ru = pairs()
    _ensure_graph()
    from algos.knowledge_graph import kg
    have_graph = bool(kg.nodes)
    known = [name for name in counts
             if name != topic and name in _EN_KB and name in en_to_ru
             and len(en_to_ru[name]) >= 4
             and (not have_graph or en_to_ru[name] in kg.nodes)]
    candidates = [(counts[name], name) for name in known]
    candidates.sort(reverse=True)
    names = [en_to_ru[name] for _, name in candidates[:limit]]
    unique = [name for name in dict.fromkeys(names) if name]
    return unique


def _brief(text, limit=220):
    """Первое предложение английского описания. Один return: str.
    Русский вопрос не должен получать простыню по-английски."""
    clean = _re.sub(r"\s+", " ", (text or "")).strip()
    result = ""
    if clean:
        sentences = _re.split(r"(?<=[.!?])\s+", clean)
        first = sentences[0] if sentences else clean
        result = first if len(first) <= limit else first[:limit].rstrip() + "…"
    return result


def _from_english(topic, name):
    """Ответ по-русски с коротким английским источником. Один return: str или None."""
    summary = _brief(summarize(_EN_KB.get(topic) or ""))
    ans = None
    if summary:
        ans = ("«%s» — по-английски %s. Русского описания пока нет, кратко из английской базы: %s"
               % (name.capitalize(), topic, summary))
        related = related_concepts(topic)
        if related:
            ans += " Связанные понятия: %s." % ", ".join(related)
    return ans


def _russian_text(topic):
    """Готовое русское описание темы, если оно уже написано. Один return: str|None."""
    text = None
    try:
        from algos.ru_descriptions import RU_TEXT
        text = RU_TEXT.get(topic)
    except (ImportError, AttributeError):
        text = None
    return text if isinstance(text, str) and text.strip() else None


def try_bilingual(query):
    """Русский вопрос о понятии → ответ по-русски (граф, иначе английская база).
    Один return: str или None (не наш случай — отвечают другие обработчики)."""
    ans = None
    text = (query or "").strip()
    low = text.lower()
    is_russian = bool(text) and not _LATIN.search(text)
    wants_definition = any(marker in low for marker in _DEFINITION_MARKERS)
    if is_russian and wants_definition:
        topic = find_concept(text)
        if topic:
            # сначала готовое русское описание: оно уже на языке пользователя,
            # и переводить английское определение не нужно
            ans = _russian_text(topic)
            if not ans:
                from algos.knowledge_graph import kg
                name = russian_name(topic)
                ans = _explain_first(kg, (name, transliterate(topic), topic))
            if not ans:
                ans = _from_english(topic, russian_name(topic))
    return ans
