# -*- coding: utf-8 -*-
"""
Mirro Semantics — понимание значений слов
==========================================
1. Word embeddings через совместную встречаемость (co-occurrence) на выборке.
2. Словарь синонимов (русский + английский, тематический).
3. API: смысл слова, синонимы, похожесть двух слов, ближайшие слова,
   смысловое сходство фраз, ответ "что значит X".
Строится быстро на ~30-60k примеров.
"""

import math, re, json, time, random
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(r"D:\Mirro\data")
PROC = DATA_DIR / "processed"
EMB_FILE = DATA_DIR / "semantics.json"


def tokenize(text):
    return [w for w in re.findall(r"[а-яёa-z0-9]+", text.lower()) if len(w) > 1]


# ===== Словарь синонимов =====
SYNONYMS = {
    # русский
    "налог": ["налоги", "сбор", "пошлина", "взнос", "акциз", "платёж"],
    "автомобиль": ["машина", "авто", "автомашина", "транспорт"],
    "код": ["программа", "скрипт", "исходники", "программирование"],
    "python": ["питон", "python3", "язык python"],
    "быстро": ["мгновенно", "скоро", "оперативно", "стремительно"],
    "хорошо": ["отлично", "прекрасно", "замечательно", "классно"],
    "плохо": ["ужасно", "скверно", "негативно"],
    "работать": ["функционировать", "действовать", "трудиться"],
    "знание": ["понимание", "осведомлённость", "компетенция"],
    "учиться": ["обучаться", "изучать", "осваивать", "постигать"],
    "создать": ["сделать", "построить", "разработать", "собрать"],
    "мир": ["вселенная", "свет"],  # в смысле "вокруг"
    "время": ["период", "момент", "срок", "час"],
    "число": ["цифра", "величина", "значение"],
    "помощь": ["поддержка", "содействие", "выручка"],
    "компьютер": ["пк", "машина", "вычислительная машина"],
    "вопрос": ["запрос", "интерес", "проблема"],
    "ответ": ["решение", "результат", "отклик"],
    "книга": ["издание", "том", "текст"],
    "изображение": ["картинка", "рисунок", "фото", "графика"],
    # английский
    "tax": ["taxes", "levy", "duty", "impost", "charge"],
    "car": ["automobile", "vehicle", "auto", "machine"],
    "fast": ["quick", "rapid", "swift", "speedy"],
    "good": ["great", "excellent", "fine", "wonderful"],
    "bad": ["terrible", "awful", "poor"],
    "work": ["function", "operate", "labour", "job"],
    "create": ["make", "build", "develop", "produce", "design"],
}


class MirroSemantics:
    def __init__(self, sample=60000):
        self.word_vectors = {}
        self.vocab = []
        self.synonyms = SYNONYMS
        self._built = False
        if EMB_FILE.exists():
            try:
                data = json.loads(EMB_FILE.read_text("utf-8"))
                self.word_vectors = {k: v for k, v in data.get("vectors", {}).items()}
                self.vocab = list(self.word_vectors.keys())
                self._built = True
                return
            except Exception:
                pass
        self._build(sample)

    def _build(self, sample):
        t0 = time.time()
        # Собираем выборку документов
        docs = []
        for f in sorted(PROC.glob("*.jsonl")):
            with open(f, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if len(docs) >= sample:
                        break
                    if not line.strip():
                        continue
                    try:
                        ex = json.loads(line)
                        inst = ex.get("instruction", "")
                        out = ex.get("output", "")
                        docs.append((inst + " " + out[:200]).lower())
                    except Exception:
                        pass
            if len(docs) >= sample:
                break

        # Частоты и ко-оккурентность (окно 3)
        window = 3
        cooc = defaultdict(Counter)
        for doc in docs:
            toks = tokenize(doc)
            for i, w in enumerate(toks):
                lo = max(0, i - window)
                hi = min(len(toks), i + window + 1)
                for j in range(lo, hi):
                    if i != j:
                        cooc[w][toks[j]] += 1

        # Топ-слова в словарь
        freq = Counter()
        for w, neigh in cooc.items():
            freq[w] = sum(neigh.values())
        self.vocab = [w for w, _ in freq.most_common(3000)]

        # Векторы: соседи топ-1000 → нормализованный вектор
        dim_words = [w for w, _ in freq.most_common(600)]
        dim_idx = {w: i for i, w in enumerate(dim_words)}
        V = len(dim_words)
        for w in self.vocab:
            vec = [0.0] * V
            maxv = 0
            for nw, cnt in cooc.get(w, {}).items():
                if nw in dim_idx:
                    vec[dim_idx[nw]] = float(cnt)
                    if cnt > maxv:
                        maxv = cnt
            if maxv:
                vec = [x / maxv for x in vec]
                self.word_vectors[w] = vec

        # сохраняем
        EMB_FILE.write_text(json.dumps({"vectors": self.word_vectors}, ensure_ascii=False), "utf-8")
        self._built = True
        print(f"  [семантика] {len(self.word_vectors)} слов, {len(dim_words)}-мерн. за {time.time()-t0:.0f}s")

    # ----- API -----
    def meaning(self, word):
        """Значение слова: описание через связанные слова."""
        w = word.lower().strip()
        if w not in self.word_vectors and w not in self.synonyms:
            # ищем близкие
            near = self.nearest(w, top=1)
            if near:
                return f"«{word}» — слово, близкое по смыслу к «{near[0]}»."
            return None
        syn = self.synonyms.get(w, [])
        near = self.nearest(w, top=4) if w in self.word_vectors else []
        parts = []
        if near:
            parts.append("похожие по смыслу: " + ", ".join(near))
        if syn:
            parts.append("синонимы: " + ", ".join(syn))
        if parts:
            return f"«{word}» — " + "; ".join(parts) + "."
        return f"«{word}» — слово из базы знаний Mirro."

    def synonyms_of(self, word):
        """Синонимы из словаря + семантически близкие."""
        w = word.lower().strip()
        out = list(self.synonyms.get(w, []))
        # дополняем близкими из векторов
        near = self.nearest(w, top=5)
        for n in near:
            if n != w and n not in out:
                out.append(n)
        return out[:10]

    def nearest(self, word, top=5):
        """Ближайшие по косинусной близости слова."""
        w = word.lower().strip()
        vec = self.word_vectors.get(w)
        if not vec:
            # попробуем по словарю синонимов
            syn = self.synonyms.get(w, [])
            return syn[:top]
        scored = []
        for ow, ov in self.word_vectors.items():
            if ow == w:
                continue
            dot = sum(a * b for a, b in zip(vec, ov))
            na = math.sqrt(sum(x * x for x in vec))
            nb = math.sqrt(sum(x * x for x in ov))
            if na and nb:
                scored.append((dot / (na * nb), ow))
        scored.sort(key=lambda x: -x[0])
        return [s for _, s in scored[:top]]

    def similarity(self, w1, w2):
        """Косинусное сходство двух слов (0..1)."""
        v1 = self.word_vectors.get(w1.lower())
        v2 = self.word_vectors.get(w2.lower())
        if not v1 or not v2:
            # фолбэк: общие синонимы
            s1 = set(self.synonyms.get(w1.lower(), [])) | {w1.lower()}
            s2 = set(self.synonyms.get(w2.lower(), [])) | {w2.lower()}
            inter = len(s1 & s2)
            if inter:
                return inter / max(len(s1), len(s2))
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(x * x for x in v1))
        n2 = math.sqrt(sum(x * x for x in v2))
        if n1 and n2:
            return dot / (n1 * n2)
        return 0.0

    def phrase_similarity(self, p1, p2):
        """Сходство фраз через средние векторы слов."""
        t1 = [t for t in tokenize(p1) if t in self.word_vectors]
        t2 = [t for t in tokenize(p2) if t in self.word_vectors]
        if not t1 or not t2:
            return 0.0
        v1 = [sum(vec[i] for vec in (self.word_vectors[t] for t in t1)) / len(t1)
              for i in range(len(next(iter(self.word_vectors.values()))))]
        v2 = [sum(vec[i] for vec in (self.word_vectors[t] for t in t2)) / len(t2)
              for i in range(len(v1))]
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(x * x for x in v1))
        n2 = math.sqrt(sum(x * x for x in v2))
        return dot / (n1 * n2) if n1 and n2 else 0.0

    def understanding(self, word):
        """Полное объяснение понимания слова."""
        m = self.meaning(word)
        syn = self.synonyms_of(word)[:6]
        sim_with = None
        # для примера возьмём несколько пар
        return {
            "word": word,
            "meaning": m,
            "synonyms": syn,
            "related": self.nearest(word, top=6),
        }

    def status(self):
        return {"words": len(self.word_vectors), "built": self._built}


# синглтон
semantics = MirroSemantics()


if __name__ == "__main__":
    for w in ["налог", "машина", "код", "хорошо", "работать"]:
        u = semantics.understanding(w)
        print(f"\nСлово: {w}")
        print(f"  значение: {u['meaning']}")
        print(f"  синонимы: {u['synonyms']}")
        print(f"  близкие: {u['related']}")
    print("\nПохожесть 'машина' ↔ 'автомобиль':", round(semantics.similarity("машина", "автомобиль"), 3))
    print("Похожесть 'машина' ↔ 'налог':", round(semantics.similarity("машина", "налог"), 3))