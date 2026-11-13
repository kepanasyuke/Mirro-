# -*- coding: utf-8 -*-
"""
Mirro RAG — двухуровневый поиск по большому корпусу на диске.
=================================================================
Уровень 1: компактный глобальный индекс (слово → номера сегментов)
Уровень 2: локальный TF-IDF внутри выбранных сегментов (по pickle-индексам)
Не загружает весь корпус в память — только нужные сегменты.
"""

import json, math, time, pickle, re as _re
from pathlib import Path
from collections import Counter, defaultdict

ROOT_DIR = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT_DIR / "data" / "corpus_big"
INDEX_DIR = ROOT_DIR / "models" / "rag_index"

SEG_SIZE = 200_000   # примеров в сегменте
GLOBAL_INDEX_NAME = "global_index.pkl"   # имя файла глобального индекса
INDEX_VERSION = 1    # формат pickle; несовпадение = пересборка


def _ensure_index_dir():
    """Создаёт папку индексов при первом использовании. Один return: Path."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    return INDEX_DIR


def _open_pickle(path):
    """Читает pickle в бинарном режиме. Один return: dict|None при битом файле."""
    data = None
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
    except (OSError, EOFError, pickle.UnpicklingError, ValueError, AttributeError):
        data = None
    return data


def _is_index_payload(data, payload_key):
    """Годится ли pickle как индекс: поле payload_key на месте, формат совпадает.

    Индексы, собранные до версионирования (без поля version), читаются как
    есть — пересборка боевого индекса на 4.8 млн примеров недопустима.
    Один return: bool.
    """
    is_valid = isinstance(data, dict) and payload_key in data
    if is_valid:
        is_valid = data.get("version", INDEX_VERSION) == INDEX_VERSION
    return is_valid


def tokenize(text):
    toks = []
    if text:
        toks = [w for w in _re.findall(r"[а-яёa-z0-9]+", text.lower()) if len(w) > 2]
    return toks


class MirroRAG:
    @property
    def segments(self):
        """Сегменты корпуса; перечитываются, если каталог сменился.
        Один return: list[Path]."""
        found = sorted(CORPUS_DIR.glob("corpus-*.jsonl"))
        if found != self._segments_cache:
            self._segments_cache = found
            self._seg_built = set()
        return self._segments_cache

    @segments.setter
    def segments(self, value):
        self._segments_cache = list(value)
        self._seg_built = set()

    def __init__(self):
        self.global_index = {}        # слово -> set(номер сегмента)
        self.seg_built = set()        # номера сегментов, для которых есть pickle
        self.seg_files = {}           # номер -> имя файла
        self._segments_cache = []
        self.segments = sorted(CORPUS_DIR.glob("corpus-*.jsonl"))
        self._load_global()

    # ------------- построение глобального индекса -------------
    def _load_global(self):
        gfile = INDEX_DIR / GLOBAL_INDEX_NAME
        data = _open_pickle(gfile) if gfile.exists() else None
        if _is_index_payload(data, "global"):
            self.global_index = data.get("global") or {}
            self.seg_built = set(data.get("seg_built") or ())
            print(f"  [RAG] глобальный индекс загружен: {len(self.global_index)} слов, "
                  f"{len(self.seg_built)} сегментов")
        else:
            print("  [RAG] глобальный индекс не найден — сначала вызови build_tier1()")

    def build_tier1(self):
        """Строит глобальный индекс: слово -> сегменты. Быстро."""
        t0 = time.time()
        gidx = defaultdict(set)
        for i, seg in enumerate(self.segments):
            self.seg_files[i] = seg
            # читаем только инструкции первых 100k строк сэмплом (голосование)
            with open(seg, encoding="utf-8", errors="replace") as f:
                for j, line in enumerate(f):
                    if j > 100_000:
                        break
                    if line.strip():
                        try:
                            inst = json.loads(line).get("instruction", "")
                        except (ValueError, AttributeError):
                            inst = ""
                        for w in set(tokenize(inst)):
                            gidx[w].add(i)
        self.global_index = dict(gidx)
        with open(_ensure_index_dir() / GLOBAL_INDEX_NAME, "wb") as f:
            pickle.dump({"version": INDEX_VERSION, "global": self.global_index,
                         "seg_built": sorted(self.seg_built)}, f, protocol=4)
        print(f"  [RAG] глобальный индекс: {len(gidx)} слов, {len(self.segments)} сегментов "
              f"за {time.time()-t0:.0f}с")

    def load_segment_file(self, i, path):
        """Регистрирует сегмент по номеру (для альтернативных каталогов).
        Один return: список сегментов."""
        self.seg_files[i] = Path(path)
        while len(self.segments) <= i:
            self.segments.append(Path(path))
        self.segments[i] = Path(path)
        return self.segments

    # ------------- построение локальных индексов сегментов -------------
    def build_segment_index(self, i):
        """Строит локальный индекс сегмента: слово -> {локальный id: tf}."""
        seg = self.seg_files.get(i) or self.segments[i]
        pfile = INDEX_DIR / f"seg_{i:06d}.pkl"
        local_words = defaultdict(dict)  # слово -> {doc_id: tf}
        n_docs = 0
        with open(seg, encoding="utf-8", errors="replace") as f:
            for doc_id, line in enumerate(f):
                n_docs = doc_id + 1
                if line.strip():
                    try:
                        ex = json.loads(line)
                    except ValueError:
                        ex = {}
                    if isinstance(ex, dict):
                        inst = ex.get("instruction", "")
                        out = ex.get("output", "")
                        words = Counter(tokenize(inst + " " + out[:100]))
                        for w, tf in words.items():
                            local_words[w][doc_id] = tf
        with open(_ensure_index_dir() / f"seg_{i:06d}.pkl", "wb") as f:
            pickle.dump({"version": INDEX_VERSION, "words": dict(local_words),
                         "n_docs": n_docs}, f, protocol=4)
        # освобождаем память
        local_words.clear()
        return pfile

    def _load_segment(self, i):
        pfile = INDEX_DIR / f"seg_{i:06d}.pkl"
        data = _open_pickle(pfile) if pfile.exists() else None
        if not _is_index_payload(data, "words") or not isinstance(data.get("words"), dict):
            self.build_segment_index(i)
            data = _open_pickle(pfile) or {"version": INDEX_VERSION, "words": {}, "n_docs": 0}
        return data

    # ------------- поиск -------------
    @staticmethod
    def _local_idf(local, ndocs, w):
        """IDF слова внутри локального корпуса сегмента. Один return: float.

        Неотрицательный: если df >= ndocs (счётчик документов отстал от
        индекса), вес не должен становиться отрицательным — иначе частые
        термины штрафуются, а сглаживание 0.5 душит вес целиком.
        """
        df = len(local.get(w, {}))
        return max(0.0, math.log((ndocs + 1) / (df + 0.5)))

    def search(self, query, top_segments=4, top_k=3):
        """
        Двухуровневый поиск.
        Уровень 1: глобальный индекс -> кандидаты-сегменты.
        Уровень 2: локальный TF-IDF в выбранных сегментах.
        Возвращает [(score, instruction, output)].
        """
        t0 = time.time()
        q_words = Counter(tokenize(query))
        results = []
        if q_words:
            # --- Уровень 1: ранжирование сегментов ---
            seg_scores = defaultdict(float)
            for w, qt in q_words.items():
                for s in self.global_index.get(w, ()):
                    seg_scores[s] += qt
            best_segs = [s for s, _ in sorted(seg_scores.items(), key=lambda x: -x[1])[:top_segments]]
            # --- Уровень 2: локальный поиск внутри сегментов ---
            for s in best_segs:
                results.extend(self._search_segment(s, q_words))

        results.sort(key=lambda x: -x[0])
        return results[:top_k]

    def _search_segment(self, seg_idx, q_words):
        """Локальный TF-IDF внутри одного сегмента. Один return: list."""
        found = []
        data = self._load_segment(seg_idx)
        local = data.get("words") or {}
        ndocs = data.get("n_docs") or 1
        candidate_docs = set()
        for w in q_words:
            candidate_docs.update(local.get(w, {}).keys())

        for doc_id in candidate_docs:
            score = 0.0
            for w, qt in q_words.items():
                tf = local.get(w, {}).get(doc_id, 0)
                if tf:
                    score += qt * self._local_idf(local, ndocs, w) * (tf * 1.5) / (tf + 1.5)
            text = self._read_doc(seg_idx, doc_id) if score > 0 else None
            if text:
                found.append((score, text[0], text[1]))
        return found

    def _segment_path(self, seg_idx):
        """Путь сегмента по номеру (с приоритетом seg_files). Один return: Path."""
        return self.seg_files.get(seg_idx) or self.segments[seg_idx]

    def _read_doc(self, seg_idx, doc_id):
        """Читает один документ из сегмента по номеру строки. Один return: tuple|None."""
        seg = self._segment_path(seg_idx)
        hit = None
        with open(seg, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i == doc_id:
                    try:
                        ex = json.loads(line)
                    except ValueError:
                        ex = None
                    if isinstance(ex, dict):
                        hit = (ex.get("instruction", ""), ex.get("output", ""))
                    break
                if i > doc_id:
                    break
        return hit

    def run_quantum_guided_rag(self, user_query, meta_pair=None, top_k=3):
        """Направленный RAG-поиск с детерминированным мета-контекстом.

        Комбинаторное ядро выбирает пару концептов (meta_pair). Из неё строится
        СТАБИЛЬНЫЙ (не рандомизированный hash()) добавочный контекст, который
        расширяет запрос перед двухуровневым search. Это направляет поиск в
        тематические сегменты диска и гасит «кашу».

        Возвращает [(score, instruction, output)] — как обычный search.
        Один return: list.
        """
        pair = meta_pair or ("general", "general")
        # стабильный хэш пары (Python hash() рандомизирован между сессиями —
        # для навигации по сегментам нужен детерминированный код)
        seed = 0
        for tok in (pair[0] + "::" + pair[1]):
            seed = (seed * 31 + ord(tok)) % 2147483647
        hint = " ".join(pair)  # тематические слова-подсказки из комбинаторной пары
        expanded = (user_query or "").strip() + " " + hint
        results = self.search(expanded, top_segments=self._guided_segments(seed), top_k=top_k)
        return results

    @staticmethod
    def _guided_segments(seed):
        """Число сегментов для направленного поиска (1..4 по стабильному коду).
        Один return: int."""
        return 1 + (seed % 4)

    def rebuild_all(self):
        """Полная сборка обоих уровней."""
        print("  [RAG] сборка двухуровневого индекса...")
        self.build_tier1()
        built = 0
        for i in range(len(self.segments)):
            self._load_segment(i)
            built += 1
        print(f"  [RAG] готово: {len(self.segments)} сегментов, {built} локальных индексов")


rag = MirroRAG()


if __name__ == "__main__":
    print("Mirro RAG — демо")
    # если индексы ещё не построены
    if not rag.global_index:
        rag.rebuild_all()
    else:
        print(f"  сегментов: {len(rag.segments)}")
    # тест поиска
    for q in ["Сколько будет 245 + 178", "Что такое НДС", "Реши уравнение x + 5 = 12"]:
        t0 = time.time()
        res = rag.search(q, top_segments=3, top_k=2)
        dt = time.time() - t0
        print(f"\nQ: {q}  ({dt:.2f}с)")
        for sc, inst, out in res:
            print(f"  [{sc:.1f}] {inst[:50]}")
            print(f"      → {out[:60]}")