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

CORPUS_DIR = Path(r"D:\Mirro\data\corpus_big")
INDEX_DIR = Path(r"D:\Mirro\models\rag_index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

SEG_SIZE = 200_000   # примеров в сегменте


def tokenize(text):
    return [w for w in _re.findall(r"[а-яёa-z0-9]+", text.lower()) if len(w) > 2]


class MirroRAG:
    def __init__(self):
        self.global_index = {}        # слово -> set(номер сегмента)
        self.segments = sorted(CORPUS_DIR.glob("corpus-*.jsonl"))
        self.seg_built = set()        # номера сегментов, для которых есть pickle
        self.seg_files = {}           # номер -> имя файла
        self._load_global()

    # ------------- построение глобального индекса -------------
    def _load_global(self):
        gfile = INDEX_DIR / "global_index.pkl"
        if gfile.exists():
            try:
                with open(gfile, "rb") as f:
                    data = pickle.load(f)
                self.global_index = data["global"]
                self.seg_built = set(data["seg_built"])
                print(f"  [RAG] глобальный индекс загружен: {len(self.global_index)} слов, "
                      f"{len(self.seg_built)} сегментов")
                return
            except Exception:
                pass
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
                    if not line.strip():
                        continue
                    try:
                        inst = json.loads(line).get("instruction", "")
                    except Exception:
                        continue
                    for w in set(tokenize(inst)):
                        gidx[w].add(i)
        self.global_index = dict(gidx)
        with open(INDEX_DIR / "global_index.pkl", "wb") as f:
            pickle.dump({"global": self.global_index, "seg_built": []}, f, protocol=4)
        print(f"  [RAG] глобальный индекс: {len(gidx)} слов, {len(self.segments)} сегментов "
              f"за {time.time()-t0:.0f}с")

    # ------------- построение локальных индексов сегментов -------------
    def build_segment_index(self, i):
        """Строит локальный индекс сегмента: слово -> {локальный id: tf}."""
        seg = self.seg_files.get(i) or self.segments[i]
        pfile = INDEX_DIR / f"seg_{i:06d}.pkl"
        local_words = defaultdict(dict)  # слово -> {doc_id: tf}
        with open(seg, encoding="utf-8", errors="replace") as f:
            for doc_id, line in enumerate(f):
                if not line.strip():
                    continue
                try:
                    ex = json.loads(line)
                    inst = ex.get("instruction", "")
                    out = ex.get("output", "")
                except Exception:
                    continue
                words = Counter(tokenize(inst + " " + out[:100]))
                for w, tf in words.items():
                    local_words[w][doc_id] = tf
        with open(pfile, "wb") as f:
            pickle.dump({"words": dict(local_words), "n_docs": doc_id + 1}, f, protocol=4)
        # освобождаем память
        local_words.clear()
        return pfile

    def _load_segment(self, i):
        pfile = INDEX_DIR / f"seg_{i:06d}.pkl"
        if not pfile.exists():
            self.build_segment_index(i)
        with open(pfile, "rb") as f:
            return pickle.load(f)

    # ------------- поиск -------------
    def search(self, query, top_segments=4, top_k=3):
        """
        Двухуровневый поиск.
        Уровень 1: глобальный индекс -> кандидаты-сегменты.
        Уровень 2: локальный TF-IDF в выбранных сегментах.
        Возвращает [(score, instruction, output)].
        """
        t0 = time.time()
        q_words = Counter(tokenize(query))
        if not q_words:
            return []

        # --- Уровень 1: ранжирование сегментов ---
        seg_scores = defaultdict(float)
        for w, qt in q_words.items():
            segs = self.global_index.get(w, set())
            for s in segs:
                seg_scores[s] += qt
        if not seg_scores:
            return []

        best_segs = [s for s, _ in sorted(seg_scores.items(), key=lambda x: -x[1])[:top_segments]]

        # --- Уровень 2: локальный поиск внутри сегментов ---
        results = []
        total_docs_in_segs = 0
        for s in best_segs:
            data = self._load_segment(s)
            local = data["words"]
            ndocs = data["n_docs"] or 1
            total_docs_in_segs += ndocs
            # локальные кандидаты по пересечению слов
            candidate_docs = set()
            for w in q_words:
                if w in local:
                    candidate_docs.update(local[w].keys())
            # idf для локального корпуса
            def local_idf(w):
                df = len(local.get(w, {}))
                return math.log(ndocs / (1 + df))

            for doc_id in candidate_docs:
                score = 0.0
                for w, qt in q_words.items():
                    tf = local.get(w, {}).get(doc_id, 0)
                    if tf:
                        score += qt * local_idf(w) * (tf * 1.5) / (tf + 1.5)
                if score > 0:
                    # достаём текст документа
                    text = self._read_doc(s, doc_id)
                    if text:
                        results.append((score, text[0], text[1]))

        results.sort(key=lambda x: -x[0])
        return results[:top_k]

    def _read_doc(self, seg_idx, doc_id):
        """Читает один документ из сегмента по номеру строки."""
        seg = self.seg_files.get(seg_idx) or self.segments[seg_idx]
        with open(seg, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i == doc_id:
                    try:
                        ex = json.loads(line)
                        return (ex.get("instruction", ""), ex.get("output", ""))
                    except Exception:
                        return None
                if i > doc_id:
                    break
        return None

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