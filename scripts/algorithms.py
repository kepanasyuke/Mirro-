#!/usr/bin/env python3
"""
Mirro Algorithms — все алгоритмы нейросетей и NLP на чистом Python
==================================================================
Без numpy, без requests, без внешних API.

1. TF-IDF + BM25 поиск
2. Word Embeddings (co-occurrence matrix, GloVe-style)
3. TextRank — суммаризация текста
4. Naive Bayes — классификация задач
5. KeyBERT-style — выделение ключевых слов
6. Cosine similarity — семантическая близость
7. Self-correction — самокоррекция ответов
8. QA scoring — оценка качества ответа
"""

import json, math, re as _re, collections, random, time, os
from pathlib import Path
from collections import Counter, defaultdict

MAX_INMEMORY_EXAMPLES = 1_500_000
DATA_DIR = Path(r"D:\Mirro\data")
MODELS_DIR = Path(r"D:\Mirro\models")
MODELS_DIR.mkdir(exist_ok=True)


class MirroAlgorithms:
    """
    Все алгоритмы в одном классе. 
    Обучается на данных из processed/ при инициализации.
    Использует кэш стемминга и персистентный индекс (pickle).
    """

    INDEX_CACHE = MODELS_DIR / "index_cache.pkl"

    def __init__(self):
        self.examples = []          # (instruction, output, cluster)
        self.vocab = []             # ordered word list
        self.word2idx = {}          # word -> index
        self.qa_boost = {}          # query key -> boost value
        self.qa_boost_ts = {}       # query key -> последний ts обновления (для затухания)
        self.boost_decay_hours = 168.0  # время полураспада буста (7 дней)
        self.feedback_history = []  # (query, response, liked) — для батч-обучения
        self.cache = {}             # query -> cached answer
        self.cache_max = 200
        self._ingested_corpus_files = set()

        # Перцептрон → MLP (2 слоя: скрытый + выходной)
        self.perceptron_weights = {}    # output layer: feature -> weight (обратная совместимость)
        self.perceptron_bias = 0.0
        self.perceptron_hidden = {}     # hidden layer: "h{j}_w{i}" -> weight (j-нейрон, i-вход)
        self.perceptron_hidden_bias = {}  # hidden layer biases: "h{j}" -> bias
        self.hidden_units = 6           # число нейронов скрытого слоя
        self.perceptron_trained = False
        self.perceptron_lr = 0.01

        # Стемминг (Porter-style для русского и английского)
        self.stem_rules_ru = {
            # Только основные окончания (неагрессивно)
            "ам": "а", "ям": "я", "ами": "а", "ями": "я",
            "ого": "", "его": "", "ому": "", "ему": "",
            "ых": "", "их": "", "ый": "", "ий": "",
            "ая": "а", "яя": "я", "ое": "о", "ее": "е",
            "ые": "ы", "ие": "и", "а": "", "я": "",
            "о": "", "е": "", "ы": "", "и": "", "у": "", "ю": "",
            "ет": "ть", "ит": "ть", "ут": "ть", "ют": "ть",
            "ал": "ть", "ил": "ть", "лась": "ться", "лись": "ться",
        }
        self.stem_exceptions_ru = {"человек": "человек", "люди": "человек", "детей": "ребенок", "дети": "ребенок"}

        # Стоп-слова
        self.stop_words = {
            "и", "в", "на", "с", "по", "за", "от", "до", "из", "у", "для", "о",
            "не", "ни", "все", "это", "как", "так", "что", "кто", "где", "когда",
            "к", "об", "под", "над", "перед", "между", "чтобы", "потому",
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "it", "at", "in", "on", "of", "to", "for", "by", "with",
            "this", "that", "these", "those", "and", "or", "but", "if",
        }

        # TF-IDF
        self.doc_freq = Counter()
        self.term_freq = Counter()
        self.total_docs = 0
        self.term_docs = defaultdict(set)  # term -> set of example IDs

        # Embeddings (word co-occurrence)
        self.cooc_matrix = defaultdict(Counter)
        self.embedding_size = 0
        self.word_vectors = {}
        # CBOW (собственные word embeddings через скользящее окно)
        self.cbow_dim = 32
        self.cbow_vectors = {}   # word -> [float] (нормированный вектор)
        self._cbow_built = False

        # TextRank graph
        self.graph_ready = False

        # Naive Bayes
        self.nb_priors = Counter()
        self.nb_priors_calib = {}  # калиброванные (смягчённые) априорные вероятности
        self.nb_word_probs = defaultdict(Counter)
        self.nb_total_words = Counter()

        self._loaded = False
        # Какие файлы corpus_ready уже ингестированы — защита от дублей
        self._ingested_corpus_files = set()
        # Кэш стемминга: слово -> результат
        self._stem_cache = {}
        self._try_load_index()
        if not self._loaded:
            self._build()
            self._save_index()
        else:
            # Даже при загрузке из кэша подтягиваем новые файлы из corpus_ready
            self._extend_from_corpus()
            self._save_index()

    # ========================
    #  BOOST — предпочтения, экспоненциально затухающие со временем
    # ========================
    @staticmethod
    def _boost_key(inst):
        """Стабильный ключ буста. Обычный hash() рандомизирован между
        перезапусками Python (PYTHONHASHSEED), что теряло предпочтения."""
        return _re.sub(r"\W+", " ", (inst or "").lower()).strip()[:120]

    @staticmethod
    def _now_iso():
        from datetime import datetime as _dt
        return _dt.utcnow().isoformat()

    def _decay_boost(self, key, now=None):
        """Возвращает текущий (затухший) буст и обновляет его временем.

        Экспоненциальное затухание: за каждые boost_decay_hours буст делится
        на 2. Старые предпочтения перестают доминировать.
        """
        if key not in self.qa_boost:
            return 0.0
        now = now or time.time()
        last = self.qa_boost_ts.get(key, now)
        elapsed = max(0.0, now - last) / 3600.0  # в часах
        halflife = self.boost_decay_hours
        factor = 0.5 ** (elapsed / halflife) if halflife > 0 else 1.0
        current = self.qa_boost[key] * factor
        # срезаем совсем малые значения
        if current < 0.05:
            self.qa_boost.pop(key, None)
            self.qa_boost_ts.pop(key, None)
            return 0.0
        self.qa_boost[key] = current
        self.qa_boost_ts[key] = now
        return current

    def _add_boost(self, key, delta):
        """Добавляет буст к ключу (с пересчётом затухания до прибавки)."""
        now = time.time()
        cur = self._decay_boost(key, now)
        self.qa_boost[key] = max(0.0, cur + delta)
        self.qa_boost_ts[key] = now

    def _save_boost_state(self):
        """Лёгкая персистентность буста (без перезаписи 1.5 ГБ индекса).

        Пишет отдельный маленький JSON рядом с индексом — так лайк/дизлайк
        не вызывает дорогой _save_index() на каждом feedback.
        """
        try:
            import json as _json
            state = {
                "qa_boost": self.qa_boost,
                "qa_boost_ts": self.qa_boost_ts,
                "boost_decay_hours": self.boost_decay_hours,
            }
            path = self.INDEX_CACHE.with_suffix(".boost.json")
            tmp = path.with_suffix(".tmp")
            tmp.write_text(_json.dumps(state, ensure_ascii=False), "utf-8")
            os.replace(tmp, path)
        except Exception as e:
            print(f"  Не удалось сохранить буст: {e}")

    def _load_boost_state(self):
        """Восстанавливает буст из лёгкого JSON (если есть)."""
        try:
            import json as _json
            path = self.INDEX_CACHE.with_suffix(".boost.json")
            if path.exists():
                state = _json.loads(path.read_text("utf-8"))
                self.qa_boost = dict(state.get("qa_boost", {}))
                self.qa_boost_ts = dict(state.get("qa_boost_ts", {}))
                self.boost_decay_hours = float(state.get("boost_decay_hours", self.boost_decay_hours))
        except Exception:
            pass

    # ========================
    #  PERSISTENT INDEX (pickle)
    # ========================
    def _try_load_index(self):
        """Загружает индекс из кэша, если он есть (быстрый старт)."""
        try:
            import pickle
            if self.INDEX_CACHE.exists():
                t0 = time.time()
                with open(self.INDEX_CACHE, "rb") as f:
                    state = pickle.load(f)
                self.examples = state["examples"]
                self.vocab = state["vocab"]
                self.word2idx = state["word2idx"]
                self.doc_freq = state["doc_freq"]
                self.term_freq = state["term_freq"]
                self.total_docs = state["total_docs"]
                self.term_docs = state["term_docs"]
                # doc_tf не храним в кэше (сильно раздувает), а пересчитываем
                # в памяти из examples — это секунды, а не полная пересборка.
                self.doc_tf = state.get("doc_tf")
                self._stem_cache = state.get("stem_cache", {})
                self.nb_priors = state.get("nb_priors", Counter())
                self.nb_priors_calib = state.get("nb_priors_calib", {})
                self.nb_word_probs = state.get("nb_word_probs", defaultdict(Counter))
                self.nb_total_words = state.get("nb_total_words", Counter())
                self._ingested_corpus_files = state.get("ingested_corpus_files", set())
                self.qa_boost = state.get("qa_boost", {})
                self.qa_boost_ts = state.get("qa_boost_ts", {})
                self._load_boost_state()
                self._load_perceptron()
                self._loaded = True
                if not self._ingested_corpus_files:
                    corpus_dir = DATA_DIR / "corpus_ready"
                    if corpus_dir.exists():
                        for f in corpus_dir.glob("*.jsonl"):
                            self._ingested_corpus_files.add(f.name)
                if self.doc_tf is None:
                    dt0 = time.time()
                    self.doc_tf = [Counter(self.tokenize(inst)) for inst, _, _ in self.examples]
                    print(f"  doc_tf пересчитан из examples за {time.time()-dt0:.1f}s")
                print(f"  Индекс загружен из кэша за {time.time()-t0:.1f}s ({len(self.examples)} ex, {len(self.doc_freq)} terms)")
        except Exception as e:
            print(f"  Кэш индекса не загрузился: {e}")

    def _save_index(self):
        """Сохраняет индекс в pickle для быстрого старта.

        Пишет атомарно: полится во временный файл, затем переименовывается,
        чтобы сбой на середине записи не оставил битый кэш (что вызывало
        полную пересборку индекса при каждом старте).
        """
        try:
            import pickle
            state = {
                "examples": self.examples,
                "vocab": self.vocab,
                "word2idx": self.word2idx,
                "doc_freq": self.doc_freq,
                "term_freq": self.term_freq,
                "total_docs": self.total_docs,
                "term_docs": self.term_docs,
                "stem_cache": self._stem_cache,
                "nb_priors": self.nb_priors,
                "nb_priors_calib": self.nb_priors_calib,
                "nb_word_probs": self.nb_word_probs,
                "nb_total_words": self.nb_total_words,
                "ingested_corpus_files": self._ingested_corpus_files,
                "qa_boost": self.qa_boost,
                "qa_boost_ts": self.qa_boost_ts,
            }
            tmp = self.INDEX_CACHE.with_suffix(".pkl.tmp")
            with open(tmp, "wb") as f:
                pickle.dump(state, f, protocol=4)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.INDEX_CACHE)
            print(f"  Индекс сохранён в кэш ({self.INDEX_CACHE.stat().st_size/1e6:.0f} MB)")
        except Exception as e:
            print(f"  Не удалось сохранить кэш: {e}")

    # ========================
    #  TOKENIZER
    # ========================
    def tokenize(self, text):
        """Tokenize with cached stemming + stop words filter."""
        words = _re.findall(r"[а-яёa-z0-9]+", text.lower())
        stemmed = []
        for w in words:
            if w in self.stop_words or len(w) < 3:
                continue
            # Кэш стемминга
            if w in self._stem_cache:
                stemmed.append(self._stem_cache[w])
                continue
            original_w = w
            if w in self.stem_exceptions_ru:
                w = self.stem_exceptions_ru[w]
            else:
                for suffix, replacement in self.stem_rules_ru.items():
                    if w.endswith(suffix) and len(w) > len(suffix) + 2:
                        w = w[:-len(suffix)] + replacement
                        break
            self._stem_cache[original_w] = w
            stemmed.append(w)
        return stemmed

    # ========================
    #  BUILD INDEX
    # ========================
    # Приоритет кластеров: ценные сначала (по алфавиту generated шёл бы первым и съедал лимит)
    CLUSTER_PRIORITY = ["ru", "math", "code", "design", "general", "knowledge",
                        "3d", "document", "presentation", "research", "system", "generated"]

    def _cluster_priority(self, name):
        try:
            return self.CLUSTER_PRIORITY.index(name)
        except ValueError:
            return 99

    def _build(self):
        print("  [Mirro Algorithms] building indexes...")
        t0 = time.time()

        files = sorted((DATA_DIR / "processed").glob("*.jsonl"))
        files.sort(key=lambda f: self._cluster_priority(f.stem))

        for f in files:
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    if len(self.examples) >= MAX_INMEMORY_EXAMPLES:
                        break
                    if not line.strip():
                        continue
                    try:
                        ex = json.loads(line)
                        inst = ex.get("instruction", ex.get("user", ""))
                        out = ex.get("output", ex.get("assistant", ""))
                        if inst and out and len(out) > 5:
                            idx = len(self.examples)
                            self.examples.append((inst, out, f.stem))
                            words = self.tokenize(inst + " " + out[:200])
                            self.term_freq.update(words)
                            for w in set(words):
                                self.doc_freq[w] += 1
                                self.term_docs[w].add(idx)
                    except Exception:
                        pass
            if len(self.examples) >= MAX_INMEMORY_EXAMPLES:
                print(f"  Достигнут лимит памяти ({MAX_INMEMORY_EXAMPLES}) — остальное отдаётся RAG-индексу")
                break

        self.total_docs = max(len(self.examples), 1)
        self.vocab = [w for w, _ in self.doc_freq.most_common(50000)]
        self.word2idx = {w: i for i, w in enumerate(self.vocab)}
        self.embedding_size = min(300, len(self.vocab))

        # Pre-compute TF vectors for fast search
        self.doc_tf = []  # list of {word: count} per document
        for inst, out, cl in self.examples:
            self.doc_tf.append(Counter(self.tokenize(inst)))

        print(f"  Index: {len(self.examples)} ex, {len(self.vocab)} vocab, {time.time()-t0:.0f}s")

        # После сборки индекса обучаем классификатор и вектора слов
        self._extend_from_corpus()
        try:
            if not self.nb_priors:
                self.nb_train()
            if not self._cbow_built:
                self.build_cbow_embeddings(max_examples=20000)
        except Exception as e:
            print(f"  (побочное обучение пропущено: {e})")

    def _extend_from_corpus(self):
        """Добавляет примеры из corpus_ready в индекс без полной пересборки."""
        # Корпус (4.8M+) обслуживается дисковым RAG-индексом — в память не грузим,
        # чтобы не выйти за лимит RAM. Сюда попадают только файлы, которых
        # ещё не было в индексе (инкрементальное добавление малых файлов).
        corpus_dir = DATA_DIR / "corpus_ready"
        if not corpus_dir.exists():
            return
        added = 0
        for f in sorted(corpus_dir.glob("*.jsonl")):
            # Пропускаем уже ингестированные файлы
            if f.name in self._ingested_corpus_files:
                continue
            # Пропускаем большие корпусные сегменты (4.8M+) — их обслуживает RAG на диске
            if f.stat().st_size > 10_000_000:  # >10MB — значит это дисковый сегмент корпуса
                self._ingested_corpus_files.add(f.name)
                continue
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    if len(self.examples) >= MAX_INMEMORY_EXAMPLES:
                        break
                    if not line.strip():
                        continue
                    try:
                        ex = json.loads(line)
                        inst = ex.get("instruction", ex.get("user", ""))
                        out = ex.get("output", ex.get("assistant", ""))
                        if inst and out and len(out) > 5:
                            idx = len(self.examples)
                            self.examples.append((inst, out, "corpus"))
                            words = self.tokenize(inst + " " + out[:200])
                            self.term_freq.update(words)
                            for w in set(words):
                                self.doc_freq[w] += 1
                                self.term_docs[w].add(idx)
                            added += 1
                    except Exception:
                        pass
            self._ingested_corpus_files.add(f.name)
            if len(self.examples) >= MAX_INMEMORY_EXAMPLES:
                print(f"  Достигнут лимит памяти ({MAX_INMEMORY_EXAMPLES}) — остальное отдаётся RAG-индексу")
                break
        if added:
            # построить doc_tf для добавленных
            for i in range(len(self.examples) - added, len(self.examples)):
                self.doc_tf.append(Counter(self.tokenize(self.examples[i][0])))
            self.total_docs = max(len(self.examples), 1)
            # Перестроить vocab и word2idx — включить новые слова
            self.vocab = [w for w, _ in self.doc_freq.most_common(50000)]
            self.word2idx = {w: i for i, w in enumerate(self.vocab)}
            self.embedding_size = min(300, len(self.vocab))
            print(f"  +{added} из корпуса, итого {len(self.examples)} примеров, {len(self.vocab)} слов")

    # ========================
    #  1. TF-IDF SEARCH
    # ========================
    def tfidf(self, term):
        """IDF weight for a term."""
        df = self.doc_freq.get(term, 1)
        return math.log(self.total_docs / (1 + df))

    def search_tfidf(self, query, top_n=5):
        """TF-IDF поиск с BM25-like нормализацией. Быстрый: использует предвычисленные TF."""
        q_words = self.tokenize(query)
        if not q_words:
            return []
        q_counts = Counter(q_words)

        # Сортируем слова по редкости (IDF) — редкие дают больше информации
        scored_words = [(self.tfidf(w), w, qt) for w, qt in q_counts.items()]
        scored_words.sort(key=lambda x: -x[0])

        scores = {}  # ex_id -> accumulated score
        MAX_DOCS = 15000

        for idf, w, qt in scored_words:
            if idf < 0.5:
                continue  # слишком частые слова пропускаем
            doc_ids = self.term_docs.get(w, set())
            for ex_id in doc_ids:
                if ex_id in scores:
                    scores[ex_id] += qt * idf * 0.5
                else:
                    tf = self.doc_tf[ex_id].get(w, 0)
                    bm25 = idf * (tf * 1.5) / (tf + 1.5)
                    scores[ex_id] = bm25 * qt
                if len(scores) > MAX_DOCS:
                    break
            if len(scores) > MAX_DOCS:
                break

        if not scores:
            return []

        best = sorted(scores.items(), key=lambda x: -x[1])[:top_n]
        return [(self.examples[ex_id], sc) for ex_id, sc in best]

    # ========================
    #  2. TEXT RANK — суммаризация
    # ========================
    def textrank_summarize(self, text, ratio=0.3):
        """
        TextRank: извлекает самые важные предложения через граф.
        Чистый Python, без numpy.
        """
        sentences = [s.strip() for s in _re.split(r'[.!?]', text) if len(s.strip()) > 20]
        if len(sentences) <= 3:
            return text

        # Build similarity matrix (cosine overlap)
        n = len(sentences)
        sim_matrix = [[0.0] * n for _ in range(n)]
        sent_words = [set(self.tokenize(s)) for s in sentences]

        for i in range(n):
            for j in range(i + 1, n):
                if not sent_words[i] or not sent_words[j]:
                    continue
                overlap = len(sent_words[i] & sent_words[j])
                sim = overlap / math.sqrt(len(sent_words[i]) * len(sent_words[j]))
                sim_matrix[i][j] = sim
                sim_matrix[j][i] = sim

        # Power iteration (PageRank on graph)
        scores = [1.0 / n] * n
        damping = 0.85
        for _ in range(20):
            new_scores = [0.0] * n
            for i in range(n):
                s = 0.0
                for j in range(n):
                    if j != i and sim_matrix[j][i] > 0:
                        out_sum = sum(sim_matrix[j][k] for k in range(n) if k != j) or 1
                        s += scores[j] * sim_matrix[j][i] / out_sum
                new_scores[i] = (1 - damping) / n + damping * s
            scores = new_scores

        # Pick top sentences
        ranked = sorted([(scores[i], i) for i in range(n)], key=lambda x: -x[0])
        top_n = max(1, int(n * ratio))
        top_indices = sorted([idx for _, idx in ranked[:top_n]])
        return " ".join(sentences[i] for i in top_indices)

    # ========================
    #  3. EMBEDDINGS (word co-occurrence)
    # ========================
    def build_embeddings(self, window=3):
        """Построение word embeddings (co-occurrence matrix)."""
        print("  Building embeddings (co-occurrence)...")
        if self.embedding_size < 10:
            return
        cooc = collections.defaultdict(Counter)
        for _, text, _ in self.examples[:20000]:
            words = self.tokenize(text)[:100]
            for i, w in enumerate(words):
                if w not in self.word2idx:
                    continue
                for j in range(max(0, i - window), min(len(words), i + window + 1)):
                    if i != j and words[j] in self.word2idx:
                        cooc[w][words[j]] += 1

        # Convert to vectors (first embedding_size dimensions = top co-occurring words)
        top_words = [w for w, _ in self.doc_freq.most_common(self.embedding_size)]
        for w in self.word2idx:
            if w in cooc:
                vec = [cooc[w].get(tw, 0) for tw in top_words]
                max_v = max(vec) or 1
                self.word_vectors[w] = [v / max_v for v in vec]

        print(f"  {len(self.word_vectors)} word vectors")

    def build_cbow_embeddings(self, window=2, max_examples=20000):
        """Строит собственные word embeddings через CBOW (без numpy).

        Для каждого окна контекста предсказывает целевое слово по среднему
        контекста; обновляет входные/выходные векторы. Затем нормирует.
        Результат — self.cbow_vectors: word -> float[dim].
        """
        if self._cbow_built or not self.word2idx:
            return
        import random as _rnd
        rnd = _rnd.Random(42)
        vocab = list(self.word2idx.keys())
        idx2w = {v: k for k, v in self.word2idx.items()}
        dim = max(4, min(self.cbow_dim, len(vocab) // 2 or 1))

        # Инициализация векторов: случайные малые значения (уникальны на слово)
        in_vec = {w: [rnd.uniform(-0.01, 0.01) for _ in range(dim)] for w in vocab}
        out_vec = {w: [0.0] * dim for w in vocab}

        def dot(a, b):
            return sum(x * y for x, y in zip(a, b))

        def collect_windows():
            for _, text, _ in self.examples[:max_examples]:
                words = self.tokenize(text)
                if len(words) < 2:
                    continue
                for i, target in enumerate(words):
                    if target not in self.word2idx:
                        continue
                    ctx = [words[j] for j in range(max(0, i - window), min(len(words), i + window + 1)) if j != i]
                    yield target, ctx

        lr = 0.05
        for target, ctx in collect_windows():
            ctx = [w for w in ctx if w in self.word2idx]
            if not ctx:
                continue
            # Усреднённый контекстный вектор
            avg = [sum(in_vec[w][d] for w in ctx) / len(ctx) for d in range(dim)]
            score = dot(avg, out_vec[target])
            # простая сигмоидная ошибка: p - 1 (для положительного примера)
            error = (1.0 / (1.0 + math.exp(-score))) - 1.0
            # Обновление выходного вектора цели
            for d in range(dim):
                out_vec[target][d] -= lr * error * avg[d]
            # Обновление входных векторов контекста
            for w in ctx:
                for d in range(dim):
                    in_vec[w][d] -= (lr * error * out_vec[target][d]) / len(ctx)

        # Нормируем и сохраняем
        self.cbow_vectors = {}
        for w in vocab:
            v = in_vec[w]
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            self.cbow_vectors[w] = [x / norm for x in v]
        self.cbow_dim = dim
        self._cbow_built = True
        print(f"  CBOW: {len(self.cbow_vectors)} векторов, dim={dim}")

    def cbow_similarity(self, word_a, word_b):
        """Косинусная близость по CBOW-векторам (0..1)."""
        if not self._cbow_built or word_a not in self.cbow_vectors or word_b not in self.cbow_vectors:
            return 0.0
        va = self.cbow_vectors[word_a]
        vb = self.cbow_vectors[word_b]
        return sum(x * y for x, y in zip(va, vb))

    def cosine_similarity(self, text1, text2):
        """Cosine similarity between two texts."""
        words1 = set(self.tokenize(text1))
        words2 = set(self.tokenize(text2))
        common = words1 & words2
        if not common:
            return 0.0
        return len(common) / math.sqrt(len(words1) * len(words2))

    # ========================
    #  4. NAIVE BAYES — классификация
    # ========================
    def nb_train(self):
        """Обучение Naive Bayes на интенте кластеров."""
        print("  Training Naive Bayes...")
        for inst, out, cluster in self.examples:
            self.nb_priors[cluster] += 1
            words = self.tokenize(inst)
            for w in set(words):
                self.nb_word_probs[cluster][w] += 1
                self.nb_total_words[cluster] += 1

        # Laplace smoothing
        for cl in self.nb_priors:
            for w in self.vocab:
                self.nb_word_probs[cl][w] += 1

        total = sum(self.nb_priors.values()) or 1
        for cl in self.nb_priors:
            self.nb_priors[cl] /= total

        # Калибровка априорных вероятностей: при сильном дисбалансе кластеров
        # (ru ~650k против design ~6k) частотные prior подавляют редкие кластеры.
        # Смягчаем: нормируем sqrt-шкалу, чтобы редкие классы не забивались.
        self.nb_priors_calib = self._calibrate_priors(dict(self.nb_priors))

        print(f"  {len(self.nb_priors)} classes trained")

    def _calibrate_priors(self, priors, alpha=0.5):
        """Возвращает смягчённые априорные вероятности.

        alpha=1.0 — частотные (без изменений); меньше 1 — сильнее выравнивает
        дисбаланс (калибровка). Сумма нормируется к 1.
        """
        if not priors:
            return {}
        vals = {cl: (p ** alpha) for cl, p in priors.items() if p > 0}
        s = sum(vals.values()) or 1.0
        return {cl: v / s for cl, v in vals.items()}

    def nb_classify(self, text):
        """Naive Bayes классификация текста по кластерам."""
        words = self.tokenize(text)
        best_cl = None
        best_log = -1e9

        # Используем КАЛИБРОВАННЫЕ априорные вероятности (смягчение дисбаланса),
        # если они вычислены; иначе — обычные частотные.
        priors = self.nb_priors_calib if self.nb_priors_calib else self.nb_priors
        for cl, prior in priors.items():
            # Защита от math.log(0): кластер без примеров в выборке (prior=0).
            log_prob = math.log(max(prior, 1e-9))
            total = max(self.nb_total_words[cl], 1)
            for w in words:
                prob = (self.nb_word_probs[cl].get(w, 1)) / (total + len(self.vocab))
                log_prob += math.log(prob)
            if log_prob > best_log:
                best_log = log_prob
                best_cl = cl

        return best_cl

    # ========================
    #  5. KEYBERT — ключевые слова
    # ========================
    def extract_keywords(self, text, top_n=5):
        """Извлечение ключевых слов через TF-IDF взвешивание."""
        words = self.tokenize(text)
        if not words:
            return []
        word_scores = {}
        total = len(words)
        for w in set(words):
            tf = words.count(w) / total
            idf = self.tfidf(w)
            word_scores[w] = tf * idf
        ranked = sorted(word_scores.items(), key=lambda x: -x[1])
        return [w for w, _ in ranked[:top_n]]

    # ========================
    #  6. QA SCORING — качество ответа
    # ========================
    def qa_score(self, question, answer):
        """
        Оценка качества ответа без эталона:
        - Длина ответа (мягкий порог)
        - Покрытие ключевых слов вопроса в ответе
        - Разнообразие (не повторяется)
        """
        if len(answer) < 20:
            return 0.0

        q_words = set(self.tokenize(question))
        a_words = set(self.tokenize(answer))

        if not q_words:
            return 0.3

        # Coverage: сколько ключевых слов вопроса есть в ответе
        coverage = len(q_words & a_words) / len(q_words)

        # Novelty: ответ не слишком похож на вопрос
        a_set = set(a_words)
        novelty = 1 - (len(q_words & a_set) / max(len(q_words | a_set), 1))

        # Length bonus (мягкий: от 20 до 500 символов)
        length_bonus = min(1.0, max(0.0, (len(answer) - 20) / 480))

        score = 0.4 * coverage + 0.3 * novelty + 0.3 * length_bonus
        return score

    # ========================
    #  6b. BLEU SELF-EVAL — сходство ответа с эталоном
    # ========================
    @staticmethod
    def bleu_score(reference, hypothesis, max_n=4):
        """BLEU-подобная метрика без внешних зависимостей (чистый Python).

        Оценивает, насколько ответ (hypothesis) похож на эталон (reference)
        из базы знаний, через точность n-грамм (1..max_n) с brevity-штрафом.
        Возвращает float 0..1.
        """
        def _ngrams(words, n):
            return [" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1))]

        def _precision(ref_tokens, hyp_tokens, n):
            ref_ngrams = _ngrams(ref_tokens, n)
            if not ref_ngrams:
                return 1.0 if n == 1 else 0.0
            hyp_ngrams = _ngrams(hyp_tokens, n)
            if not hyp_ngrams:
                return 0.0
            from collections import Counter as _C
            ref_counts = _C(ref_ngrams)
            hyp_counts = _C(hyp_ngrams)
            clipped = sum(min(c, ref_counts.get(g, 0)) for g, c in hyp_counts.items())
            return clipped / len(hyp_ngrams)

        import re as _re
        ref_tokens = _re.findall(r"[а-яёa-z0-9]+", reference.lower())
        hyp_tokens = _re.findall(r"[а-яёa-z0-9]+", hypothesis.lower())
        if not ref_tokens or not hyp_tokens:
            return 0.0

        # Средняя точность n-грамм (shift от 1 для стабильности 0..1)
        precisions = [_precision(ref_tokens, hyp_tokens, n) for n in range(1, max_n + 1)]
        avg_prec = sum(precisions) / max_n

        # Brevity penalty: штраф за слишком короткий ответ
        bp = 1.0 if len(hyp_tokens) > len(ref_tokens) else max(0.0, min(1.0, len(hyp_tokens) / max(len(ref_tokens), 1)))

        # Взвешиваем: unigram важнее, brevity-штраф умеренный
        return min(1.0, avg_prec * (0.7 + 0.3 * bp))

    def self_eval_bleu(self, question, answer):
        """Self-eval: находит эталон из базы и сравнивает с ответом через BLEU.

        Возвращает (bleu_score, reference), где reference — ближайший эталон
        из базы (или None, если база пуста). Высокий балл = ответ хорошо
        совпадает с эталоном знаний.
        """
        results = self.search_tfidf(question, top_n=1)
        if not results:
            return 0.0, None
        (inst, ref, cl), sc = results[0]
        return self.bleu_score(ref, answer), ref

    # ========================
    #  7. SELF-CORRECTION
    # ========================
    def self_correct(self, question, initial_answer):
        """
        Самокоррекция: проверяет ответ, ищет лучше.
        """
        # Check quality
        score = self.qa_score(question, initial_answer)
        if score > 0.6:
            return initial_answer, score

        # Try to improve: search for better examples
        results = self.search_tfidf(question, top_n=8)
        if results:
            best_text = ""
            best_score = 0
            for (inst, out, cl), sc in results:
                if out and len(out) > 50:
                    s = self.qa_score(question, out)
                    if s > best_score:
                        best_score = s
                        best_text = out

            if best_text and best_score > score:
                return best_text, best_score

        return initial_answer, score

# ========================
#  9. PERCEPTRON — мини-нейросеть
# ========================
    def perceptron_vectorize(self, query, candidate):
        """Преобразует вопрос+кандидат в вектор признаков.

        №08 «Контекстный перцептрон»: добавляем признаки контекста, которые
        вычисляются из самого кандидата и помогают отличать «код» от «текста»
        и учитывать язык, — без смены сигнатуры вызовов.
        """
        q_words = set(self.tokenize(query))
        c_words = set(self.tokenize(candidate))
        common = q_words & c_words

        f1 = len(common) / max(len(q_words), 1)                    # overlap ratio
        f2 = len(common) / max(len(c_words), 1)                    # recall
        f3 = math.log(len(candidate) + 1) / 10                     # length bonus
        f4 = 1.0 if any(w in candidate.lower() for w in q_words) else 0.0  # exact hit
        # Контекстные признаки (улучшение №08):
        #  f5 — «код-подобность»: доля символов, характерных для кода
        code_chars = sum(1 for ch in candidate if ch in "{}[]();=<>#/*")
        f5 = min(1.0, code_chars / max(len(candidate), 1) * 10)
        #  f6 — «русскость»: доля кириллических букв
        cyr = sum(1 for ch in candidate.lower() if 'а' <= ch <= 'я')
        f6 = min(1.0, cyr / max(len(candidate), 1))
        return [f1, f2, min(f3, 1.0), f4, f5, f6]

    def _hidden_forward(self, x):
        """Прямой проход через скрытый слой (tanh). Возвращает вектор h."""
        h = []
        for j in range(self.hidden_units):
            acc = self.perceptron_hidden_bias.get(f"h{j}", 0.0)
            for i in range(len(x)):
                acc += self.perceptron_hidden.get(f"h{j}_w{i}", 0.0) * x[i]
            # tanh-активация скрытого слоя
            h.append(math.tanh(acc) if acc else 0.0)
        return h

    @staticmethod
    def _sigmoid(z):
        try:
            return 1.0 / (1.0 + math.exp(-z))
        except OverflowError:
            return 0.0 if z < 0 else 1.0

    def _mlp_activation(self, x):
        """Совместный проход: вход → скрытый → выход (без сигмоиды на конце).
        Возвращает (output_activation, hidden_activations)."""
        h = self._hidden_forward(x)
        out = self.perceptron_bias
        for j in range(self.hidden_units):
            out += self.perceptron_weights.get(f"h{j}_out", 0.0) * h[j]
        return out, h

    def perceptron_train(self, query, candidate, label):
        """Обучает MLP (2 слоя) на одном примере (label = 1 хороший, -1 плохой).

        Инициализация весов первого слоя при первом вызове. Обновление —
        через градиент первого порядка (знак ошибки), как у перцептрона,
        но по обоим слоям обратным распространением.
        """
        x = self.perceptron_vectorize(query, candidate)
        nin = len(x)

        # Инициализация скрытого слоя и выходного слоя при первом вызове
        if not self.perceptron_weights:
            for j in range(self.hidden_units):
                for i in range(nin):
                    self.perceptron_hidden.setdefault(f"h{j}_w{i}", 0.0)
                self.perceptron_hidden_bias.setdefault(f"h{j}", 0.0)
                # веса выходного слоя индексируются как h{j}_out (обратная
                # совместимость с однослойной формой f{i} сохраняется ниже)
                self.perceptron_weights.setdefault(f"h{j}_out", 0.0)

        out, h = self._mlp_activation(x)
        prediction = 1 if out >= 0 else -1

        if prediction != label:
            err = label if label in (1, -1) else 0
            lr = self.perceptron_lr
            # Обновление выходного слоя
            for j in range(self.hidden_units):
                self.perceptron_weights[f"h{j}_out"] += lr * err * h[j]
            self.perceptron_bias += lr * err
            # Обратное распространение в скрытый слой (производная tanh = 1 - h^2)
            for j in range(self.hidden_units):
                d_out_j = err * self.perceptron_weights.get(f"h{j}_out", 0.0)
                g_j = d_out_j * (1 - h[j] * h[j])
                self.perceptron_hidden_bias[f"h{j}"] += lr * g_j
                for i in range(nin):
                    self.perceptron_hidden[f"h{j}_w{i}"] += lr * g_j * x[i]

        self.perceptron_trained = True
        return prediction == label

    def perceptron_predict(self, query, candidate):
        """Предсказывает релевантность ответа (0..1) через MLP."""
        x = self.perceptron_vectorize(query, candidate)
        # Инициализация при первом использовании (если ещё не тренировались)
        if not self.perceptron_weights and self.hidden_units:
            for j in range(self.hidden_units):
                for i in range(len(x)):
                    self.perceptron_hidden.setdefault(f"h{j}_w{i}", 0.0)
                self.perceptron_hidden_bias.setdefault(f"h{j}", 0.0)
                self.perceptron_weights.setdefault(f"h{j}_out", 0.0)
        out, _ = self._mlp_activation(x)
        return 1.0 / (1.0 + math.exp(-out))

    def train_from_feedback(self, query, response, liked):
        """Обучает перцептрон на feedback пользователя (лайк/дизлайк).

        Дополнительно записывает экспоненциально затухающий буст: лайк
        повышает предпочтение похожих вопросов, дизлайк понижает.
        """
        label = 1 if liked else -1
        learned = self.perceptron_train(query, response, label)
        # Копим в буфер для батч-обучения (см. train_from_history)
        self.feedback_history.append((query, response, liked))
        if len(self.feedback_history) > 500:
            self.feedback_history.pop(0)
        # Буст на ключ ответа (помогает выбирать похожие ответы в будущем)
        boost_key = self._boost_key(response)
        self._add_boost(boost_key, 0.4 if liked else -0.3)
        self._save_boost_state()
        return learned

    def train_from_history(self, batch_size=32, epochs=1):
        """Пакетное обучение перцептрона на накопленной истории feedback.

        Пере-обучает на батче оценённых пользователем (query, response, liked)
        пар. Более устойчиво, чем одиночные шаги: каждый пример обновляется
        без хрупкой последовательности (epochs проходов по батчу).
        Возвращает количество отработанных примеров.
        """
        if not self.feedback_history:
            return 0
        batch = self.feedback_history[-batch_size:]
        processed = 0
        for _ in range(max(1, epochs)):
            for query, response, liked in batch:
                label = 1 if liked else -1
                self.perceptron_train(query, response, label)
                processed += 1
        # Сохраняем одиночную персистентность модели (буст уже в JSON)
        self._save_perceptron()
        return processed

    def _save_perceptron(self):
        """Лёгкая персистентность весов MLP (выходной + скрытый слой)."""
        try:
            import json as _json
            state = {"perceptron_weights": self.perceptron_weights,
                     "perceptron_bias": self.perceptron_bias,
                     "perceptron_hidden": self.perceptron_hidden,
                     "perceptron_hidden_bias": self.perceptron_hidden_bias,
                     "hidden_units": self.hidden_units,
                     "perceptron_trained": self.perceptron_trained,
                     "auto_learned": len(self.feedback_history),
                     "updated": self._now_iso()}
            path = self.INDEX_CACHE.with_suffix(".perceptron.json")
            tmp = path.with_suffix(".tmp")
            tmp.write_text(_json.dumps(state, ensure_ascii=False), "utf-8")
            os.replace(tmp, path)
        except Exception:
            pass

    def _load_perceptron(self):
        """Восстанавливает веса MLP (включая скрытый слой) из JSON, если есть."""
        try:
            import json as _json
            path = self.INDEX_CACHE.with_suffix(".perceptron.json")
            if path.exists():
                st = _json.loads(path.read_text("utf-8"))
                self.perceptron_weights = dict(st.get("perceptron_weights", {}))
                self.perceptron_bias = float(st.get("perceptron_bias", 0.0))
                self.perceptron_hidden = dict(st.get("perceptron_hidden", {}))
                self.perceptron_hidden_bias = dict(st.get("perceptron_hidden_bias", {}))
                self.hidden_units = int(st.get("hidden_units", self.hidden_units))
                self.perceptron_trained = bool(st.get("perceptron_trained", False))
        except Exception:
            pass

    # ========================
    #  8. COMPOSE ANSWER (improved)
    # ========================
    def compose_answer(self, query, top_n=8, max_len=4000):
        """
        Полный пайплайн: кэш → поиск → фильтрация перцептроном → дедупликация → TextRank → самокоррекция.
        """
        # 0. Cache check
        cache_key = query.strip().lower()[:100]
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 1. TF-IDF search
        results = self.search_tfidf(query, top_n=top_n)
        if not results:
            self.cache[cache_key] = None
            return None

        # 2. Score candidates with perceptron + QA score (+ затухающий буст предпочтений)
        scored = []
        seen = set()
        for (inst, out, cl), tfidf_score in results:
            if not out or out[:50] in seen:
                continue
            seen.add(out[:50])
            nn_score = self.perceptron_predict(query, out)
            qa = self.qa_score(query, out)
            boost = self._decay_boost(self._boost_key(out))
            combined = 0.3 * tfidf_score + 0.3 * nn_score + 0.4 * qa + boost
            scored.append((combined, out, cl))

        if not scored:
            self.cache[cache_key] = None
            return None

        # 3. Take top 3 from different clusters
        scored.sort(key=lambda x: -x[0])
        parts = []
        used_cl = set()
        for sc, out, cl in scored:
            if len(parts) >= 3:
                break
            if cl in used_cl:
                continue
            parts.append(out[:1200].strip())
            used_cl.add(cl)

        # 4. Combine and summarize
        combined = "\n\n".join(parts)[:max_len]
        if len(combined) > 1500 and len(parts) > 1:
            combined = self.textrank_summarize(combined, ratio=0.5)

        # 5. Self-correction
        corrected, _ = self.self_correct(query, combined)

        # 6. Cache
        if len(self.cache) >= self.cache_max:
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[cache_key] = corrected
        return corrected

    # ========================
    #  AUTONOMOUS SELF-LEARNING (60-min loop)
    # ========================
    def autonomous_learn(self, cycles=30):
        """Автономное самообучение: генерирует вопросы из своей базы,
        отвечает, оценивает, корректирует перцептрон."""
        learned = 0
        import random as _rnd

        # Pick sample of examples
        sample = self.examples
        if len(sample) > 5000:
            sample = _rnd.sample(self.examples, 5000)

        for inst, out, cl in sample[:cycles]:
            if len(inst) < 8:
                continue
            # Generate answer with current model
            ans = self.compose_answer(inst, top_n=4)
            if not ans:
                continue
            # Evaluate: compare with the reference answer
            ref_words = set(self.tokenize(out))
            ans_words = set(self.tokenize(ans))
            if not ref_words:
                continue
            coverage = len(ans_words & ref_words) / len(ref_words)

            # Learn = train perceptron on this QA pair
            label = 1 if coverage > 0.3 else -1
            self.perceptron_train(inst, ans, label)
            self.perceptron_trained = True
            learned += 1

        # Реплей-буфер: пере-играем оценённые пользователем пары (feedback),
        # чтобы модель не забывала явные предпочтения.
        if self.feedback_history:
            replay = sum(
                self.perceptron_train(q, r, 1 if liked else -1)
                for q, r, liked in self.feedback_history)
            learned += replay

        return learned

    # ========================
    #  DETECT HALLUCINATION
    # ========================
    def detect_hallucination(self, question, answer):
        """Детектор галлюцинаций: проверяет, сколько фактов ответа подкреплено базой."""
        q_words = set(self.tokenize(question))
        ans_words = set(self.tokenize(answer))
        if not ans_words:
            return 1.0

        # What fraction of answer's key words appear in the index at all
        supported = 0
        for w in ans_words:
            if w in self.doc_freq and self.doc_freq[w] > 0:
                supported += 1
        coverage = supported / len(ans_words)
        # Lower = more hallucination
        risk = 1.0 - coverage
        return risk

    # ========================
    #  STATUS
    # ========================
    def status(self):
        return {
            "examples": len(self.examples),
            "vocab": len(self.vocab),
            "embeddings": len(self.cbow_vectors or self.word_vectors),
            "embedding_dim": getattr(self, "cbow_dim", 0),
            "nb_classes": dict(self.nb_priors),
            "new_algorithms": {
                "jaccard": True, "spellcheck": True,
                "query_expansion": True, "sentence_rank": True,
                "auto_learn_trigger": True,
            },
        }

    # ========================
    #  НОВЫЕ АЛГОРИТМЫ (не трогая старые)
    # ========================

    # 1. JACCARD — мера сходства текстов
    def jaccard_similarity(self, text1, text2):
        """Jaccard: |пересечение| / |объединение| на множествах слов."""
        w1 = set(self.tokenize(text1))
        w2 = set(self.tokenize(text2))
        if not w1 or not w2:
            return 0.0
        inter = len(w1 & w2)
        union = len(w1 | w2)
        return inter / union if union else 0.0

    # 2. SPELLCHECK — исправление опечаток по словарю
    def spellcheck(self, text):
        """Заменяет опечатки на ближайшие слова из вокабуляра (edit distance 1)."""
        words = _re.findall(r"[а-яёa-z]+", text.lower())
        corrections = {}
        vocab = set(self.vocab[:20000])  # ограничим для скорости
        for w in words:
            if w in vocab or len(w) < 4 or w in self.stop_words:
                continue
            # Поиск по edit-distance через префиксы
            best = self._closest_word(w, vocab)
            if best:
                corrections[w] = best
        result = text
        for wrong, right in corrections.items():
            result = _re.sub(rf"\b{wrong}\b", right, result, flags=_re.IGNORECASE)
        return result

    def _closest_word(self, word, vocab):
        """Находит ближайшее слово из словаря по edit distance <= 2."""
        from collections import deque
        best = None
        best_dist = 3
        for candidate in vocab:
            if abs(len(candidate) - len(word)) > 2:
                continue
            d = self._edit_distance(word, candidate)
            if d < best_dist:
                best_dist = d
                best = candidate
        return best if best_dist <= 2 and best != word else None

    @staticmethod
    def _edit_distance(a, b):
        """Расстояние Левенштейна (DP)."""
        dp = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            prev = dp[0]
            dp[0] = i
            for j, cb in enumerate(b, 1):
                cur = dp[j]
                cost = 0 if ca == cb else 1
                dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
                prev = cur
        return dp[-1]

    # 3. QUERY EXPANSION — расширение запроса синонимами из базы
    def query_expansion(self, query, top_terms=3):
        """Находит ассоциированные термины к запросу (со-встречающиеся)."""
        q_words = set(self.tokenize(query))
        expansions = {}
        for w in q_words:
            if w not in self.cooc_matrix:
                continue
            for assoc, cnt in self.cooc_matrix[w].most_common(3):
                if assoc not in q_words and cnt > 2:
                    expansions[assoc] = expansions.get(assoc, 0) + cnt
        # Отсортировать по силе связи
        top = sorted(expansions.items(), key=lambda x: -x[1])[:top_terms]
        return [w for w, _ in top]

    # 4. SENTENCE RANKING — ранжирование предложений по релевантности
    def sentence_rank(self, question, answer, top_k=3):
        """Разбивает ответ на предложения и возвращает самые релевантные."""
        sentences = [s.strip() for s in _re.split(r"(?<=[.!?])\s+", answer) if len(s.strip()) > 15]
        if len(sentences) <= top_k:
            return sentences
        q_words = set(self.tokenize(question))
        ranked = []
        for s in sentences:
            s_words = set(self.tokenize(s))
            score = len(q_words & s_words) + self.jaccard_similarity(question, s)
            ranked.append((score, s))
        ranked.sort(key=lambda x: -x[0])
        return [s for _, s in ranked[:top_k]]

    # 5. AUTO-LEARN TRIGGER — сигнал автообучения
    def should_auto_learn(self, question, answer):
        """Решает, нужно ли Mirro дообучиться: если ответ слабый (короткий/риск)."""
        score = self.qa_score(question, answer)
        risk = self.detect_hallucination(question, answer)
        # Учимся, если ответ слабый ИЛИ высокий риск галлюцинаций
        return (score < 0.35) or (risk > 0.8)

    # 6. COMPOSE с новыми алгоритмами (надстройка, не меняя старый compose)
    def compose_answer_v2(self, query, top_n=8, max_len=4000):
        """Улучшенный пайплайн: spellcheck → query expansion → jaccard/rank."""
        # 1. Исправляем опечатки в запросе
        clean_query = self.spellcheck(query)

        # 2. Расширяем запрос ассоциациями
        expansion = self.query_expansion(clean_query)
        search_query = clean_query + " " + " ".join(expansion)

        # 3. Ищем (старый TF-IDF)
        results = self.search_tfidf(search_query, top_n=top_n)
        if not results:
            return None

        # 4. Ранжируем по jaccard + перцептрон + qa
        scored = []
        seen = set()
        for (inst, out, cl), tfidf_score in results:
            if not out or out[:50] in seen:
                continue
            seen.add(out[:50])
            nn = self.perceptron_predict(query, out)
            ja = self.jaccard_similarity(clean_query, out)
            qa = self.qa_score(clean_query, out)
            combined = 0.25 * tfidf_score + 0.25 * nn + 0.25 * ja + 0.25 * qa
            scored.append((combined, out, cl))

        if not scored:
            return None

        scored.sort(key=lambda x: -x[0])
        parts = []
        used_cl = set()
        for sc, out, cl in scored:
            if len(parts) >= 3:
                break
            if cl in used_cl:
                continue
            # Ранжирование предложений внутри ответа
            top_sents = self.sentence_rank(clean_query, out, top_k=2)
            parts.append(" ".join(top_sents)[:1100])
            used_cl.add(cl)

        return "\n\n".join(parts)[:max_len]


# Singleton
algo = MirroAlgorithms()


def answer(query):
    return algo.compose_answer(query)

def summarize(text):
    return algo.textrank_summarize(text)

def classify(text):
    return algo.nb_classify(text)

def keywords(text):
    return algo.extract_keywords(text)

if __name__ == "__main__":
    print("Mirro Algorithms Demo")
    print()

    # Test search
    for q in [
        "Что такое НДС?",
        "Как заменить mspaint на маке?",
        "Напиши код сортировки на Python"
    ]:
        ans = answer(q)
        kw = keywords(q)
        cls = classify(q)
        if ans:
            print(f"Q: {q}")
            print(f"  Класс: {cls}")
            print(f"  Ключевые слова: {kw}")
            print(f"  Ответ ({len(ans)} chars): {ans[:200]}...")
            sc = algo.qa_score(q, ans)
            print(f"  Оценка: {sc:.3f}")
            print()