# -*- coding: utf-8 -*-
"""Mirro Algorithms — 35 · Профиль пользователя (User Profile)

Инновация: «своя личность» — Mirro запоминает собеседника между сессиями:
имя, любимые темы, предпочтение по длине ответов (коротко/подробно) и тональность.
Профиль персистентный (data/user_profile.json, атомарная запись) и используется,
чтобы отвечать теплее и персональнее: «Ты, {имя}, любишь {тема} — расскажу подробнее».

Чистый Python, атомарные функции (один return), по LINTER.md.
"""
import os
import re as _re
import json

_PROF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
_PROF_FILE = os.path.join(_PROF_DIR, "user_profile.json")

# слова-маркеры предпочтения по длине ответа
_VERBOSE_MARKERS = ("подробнее", "подробно", "разверни", "расширь", "поподробнее",
                    "деталь", "короче говоря", "простым", "простыми словами")
_BRIEF_MARKERS = ("коротко", "кратко", "покороче", "кратенько", "в двух словах")

# маркеры «меня зовут X» (имя может быть составным через дефис: Анна-Мария)
_NAME_RE = _re.compile(r"(?:меня\s+зовут|мо[её]\s+имя|я\s+—|я\s+это)\s+([а-яёa-z-]{2,})", _re.I)

_TOPIC_EXTRACT_STOP = {"что", "такое", "как", "это", "про", "расскажи", "объясни",
                       "мне", "меня", "хочу", "знать", "люблю", "нравится", "помоги",
                       "напиши", "сделай", "покажи", "about", "the", "и", "в", "на"}


def _default_profile():
    """Пустой профиль пользователя. Один return: dict."""
    return {"name": None, "topics": [], "verbosity": 0.0, "remarks": []}


def _path():
    """Файл профиля (создаёт каталог при необходимости). Один return: str."""
    d = os.path.dirname(_PROF_FILE)
    if not os.path.isdir(d):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
    return _PROF_FILE


def _load_all():
    """Читает все профили из диска: {user_id: profile}. Один return: dict."""
    all_profiles = {}
    try:
        if os.path.exists(_path()):
            with open(_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                all_profiles = {str(k): v for k, v in data.items() if isinstance(v, dict)}
    except Exception:
        all_profiles = {}
    return all_profiles


def load_profile(user_id="default"):
    """Читает профиль конкретного пользователя (по умолчанию — единый).
    Если нет/битый — пустой. Один return: dict."""
    all_p = _load_all()
    prof = _default_profile()
    entry = all_p.get(str(user_id))
    if entry:
        prof["name"] = entry.get("name")
        prof["topics"] = list(entry.get("topics", []))[:20]
        try:
            prof["verbosity"] = max(-1.0, min(1.0, float(entry.get("verbosity") or 0.0)))
        except Exception:
            prof["verbosity"] = 0.0
        prof["remarks"] = list(entry.get("remarks", []))[:30]
    return prof


def save_profile(prof, user_id="default"):
    """Атомарно сохраняет профиль пользователя (мультипрофиль: по ключу user_id).
    Пустой/None-профиль не сохраняется. Один return: bool."""
    ok = False
    if not isinstance(prof, dict):
        return False
    try:
        all_p = _load_all()
        all_p[str(user_id)] = {
            "name": prof.get("name"),
            "topics": prof.get("topics", [])[:20],
            "verbosity": prof.get("verbosity", 0.0),
            "remarks": prof.get("remarks", [])[:30],
        }
        tmp = str(_path()) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(all_p, f, ensure_ascii=False)
        os.replace(tmp, str(_path()))
        ok = True
    except Exception:
        ok = False
    return ok


def _extract_name(query):
    """Достаёт имя из фразы «меня зовут X / моё имя X / я — X».
    Слишком длинные «имена» (>30 симв.) отбрасываются. Один return: str|None."""
    name = None
    m = _NAME_RE.search((query or "").strip())
    if m:
        cand = m.group(1).strip(" ,.!?")
        # имя — отдельное слово (не «Мария Петрова», берём первое)
        cand = cand.split()[0][:30]
        if len(cand) >= 2 and not _re.match(r"^\W+$", cand):
            name = cand.capitalize()
    return name


def _extract_topic(query):
    """Пытается вытащить тему интереса из фразы «(мне, расскажи) про X» /
    «люблю X» / «интересуюсь X». Один return: str или None."""
    q = (query or "").strip().lower()
    topic = None
    for marker in ("интересуюсь", "люблю", "нравится", "увлекаюсь", "хочу знать про"):
        if marker in q:
            idx = q.find(marker) + len(marker)
            tail = q[idx:].strip(" ,.!?;:—")
            # убираем хвост-вопрос («...?», «...и подробнее»)
            for stop in (" и", " про", " пожалуйста", "?"):
                cut = tail.find(stop)
                if cut > 0:
                    tail = tail[:cut]
                    break
            words = [w for w in tail.split() if w and w not in _TOPIC_EXTRACT_STOP][:4]
            if words:
                topic = " ".join(words).capitalize()
                break
    # «расскажи про X» или просто «про X» — тема после «про»
    m = _re.search(r"\bпро\s+([а-яёa-z]{4,})", q)
    if m:
            cand = m.group(1).strip()
            first = cand.split()[0]
            if first not in _TOPIC_EXTRACT_STOP and len(first) >= 4:
                topic = first.capitalize()
    # не копим служебное в качестве темы
    if topic and topic.lower() in ("расскажи", "про", "подробнее", "меня", "мне"):
        topic = None
    return topic


def learn_from_message(prof, message):
    """Обновляет профиль по реплике пользователя: имя, темы, длину ответа.
    Возвращает (новый профиль, заметок). Один return: tuple."""
    prof = dict(prof)
    msg = (message or "").strip()
    if not msg:
        return prof, 0
    changed = 0
    name = _extract_name(msg)
    if name and prof.get("name") != name:
        prof["name"] = name
        note = f"познакомились: {name}"
        if note not in prof.get("remarks", []):
            prof["remarks"].append(note)
            prof["remarks"] = prof["remarks"][-30:]
        changed += 1
    topic = _extract_topic(msg)
    if topic:
        topics = list(prof.get("topics", []))
        if topic not in topics:
            topics.append(topic)
            prof["topics"] = topics[-20:]
            prof["remarks"].append(f"интерес: {topic}")
            changed += 1
    low = msg.lower()
    v = prof.get("verbosity", 0.0)
    if any(m in low for m in _VERBOSE_MARKERS):
        prof["verbosity"] = max(-1.0, min(1.0, v + 0.2))
        changed += 1
    if any(m in low for m in _BRIEF_MARKERS):
        prof["verbosity"] = max(-1.0, min(1.0, v - 0.2))
        changed += 1
    return prof, changed


def _remember_text(prof, query):
    """Ответ для «как меня зовут / что ты обо мне знаешь». Один return: str."""
    name = prof.get("name")
    topics = [t for t in prof.get("topics", []) if t]
    if name or topics:
        parts = []
        if name:
            parts.append(f"зовут тебя {name}")
        if topics:
            parts.append("любишь " + ", ".join(topics[:3]))
        return "Я помню: " + (" и ".join(parts)) + "."
    return "Я пока мало знаю о тебе. Расскажи: как тебя зовут и что интересно?"


def _say_remember(prof, q):
    """Разговорная фраза «помнишь меня». Один return: str."""
    if prof.get("name"):
        return f"Конечно помню, {prof['name']}! " + _remember_text(prof, q)
    return _remember_text(prof, q)


def try_user_profile(query, user_id="default"):
    """Точка входа для try_директ: отвечает на вопросы о знании пользователя,
    а также молча запоминает имя/темы/длину и отвечает None (не перебивает).
    Многопользовательский режим: user_id выбирает профиль.
    q — вопрос. Один return: str или None."""
    q = (query or "").strip().lower()
    ans = None
    prof = load_profile(user_id)
    if any(w in q for w in ("как меня зовут", "как зовут", "помнишь меня",
                            "что ты обо мне", "ты меня знаешь", "моё имя")):
        ans = _say_remember(prof, q)
    elif any(w in q for w in ("меня зовут", "моё имя", "люблю ", "интересуюсь",
                              "увлекаюсь", "нравится ", "расскажи про", "подробнее",
                              "покороче", "коротко", "в двух словах", "кратко")):
        new_prof, _ch = learn_from_message(prof, query)
        if _ch:
            save_profile(new_prof, user_id)
    return ans


# обращение по имени: если знаем, подставляем в начало голосового ответа
def greet_name(content, query):
    """Вставляет имя пользователя в начало ответа, если оно известно и ответ
    не начинается с него. Длинные имена обрезаются до 40 символов.
    Один return: str."""
    out = content if isinstance(content, str) else str(content or "")
    try:
        prof = load_profile()
        name = str(prof.get("name") or "")[:40]
        if name and out and out.lower()[:len(name) + 1] != name.lower() + " ":
            head = out[:200]
            if not any(w in head.lower() for w in ("переформулируй", "не нашла", "ошибк")):
                out = name + ", " + out[0].lower() + out[1:]
    except Exception:
        out = content if isinstance(content, str) else str(content or "")
    return out


def adapt_style(content, query):
    """Адаптирует длину ответа под предпочтение пользователя из профиля
    (verbosity: -1 = кратко, +1 = подробно). Длинный ответ для «кратко»
    сжимается до первых двух предложений + подсказки. Один return: str."""
    out = content if isinstance(content, str) else str(content or "")
    try:
        prof = load_profile()
        v = prof.get("verbosity", 0.0)
        if v is None:
            return out
        # порог: при заметном предпочтении «кратко» (verbosity < -0.3)
        if v < -0.3 and len(out) > 600:
            import re as _re_a
            sents = _re_a.split(r"(?<=[.!?])\s+", out.strip())
            if len(sents) > 3:
                short = " ".join(sents[:2]).strip()
                out = short + " Хочешь подробнее — скажи, разверну."
        elif v > 0.3 and len(out) < 300:
            # «подробно»: добавляем приглашение развернуть (я дам больше по запросу)
            out = out.rstrip() + " Могу раскрыть ещё детальнее — спроси."
    except Exception:
        out = content if isinstance(content, str) else str(content or "")
    return out