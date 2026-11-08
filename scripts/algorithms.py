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

LITE_MODE = os.environ.get("MIRRO_LITE", "").strip().lower() in ("1", "true", "yes", "on")
MAX_INMEMORY_EXAMPLES = 100_000 if LITE_MODE else 1_500_000
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"
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
        self.doc_tf = None

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
        # Словарь синонимов для поиска: разные слова -> один канонический стем.
        # Позволяет вопросам «автомобиль/машина», «сеть/нейросеть», «мозг/нервная система»
        # находить одни и те же документы.
        self.synonyms_ru = {
            "автомобиль": "машина", "авто": "машина", "машин": "машина",
            "приложение": "программ", "прога": "программ",
            "нейросеть": "нейронн", "нейро": "нейронн",
            "мозг": "мозг", "сердце": "сердц",
            "ученый": "учен", "учёный": "учен",
            "нлс": "нейронн", "ai": "ии", "ии": "ии",
            "быстрый": "быстр", "скорый": "быстр", "медленный": "медлен",
        }
        # морфологические исключения (род/число/падеж) — дополнительно к stem_exceptions
        self.morph_exceptions = {
            "дети": "ребен", "ребёнок": "ребен", "детей": "ребен",
            "люди": "человек", "человека": "человек", "человеку": "человек",
            "овцы": "овц", "овца": "овц",
            "времени": "врем", "время": "врем",
        }

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
        # Общий триггер: обучаем NB и CBOW на любом пути (сборка ИЛИ кэш),
        # чтобы status() показывал реальные nb_classes и embeddings.
        # В lite-режиме пропускаем — они сильно раздувают RAM.
        try:
            if not LITE_MODE:
                if not self.nb_priors:
                    self.nb_train()
                if not self._cbow_built:
                    self.build_cbow_embeddings(max_examples=20000)
                    # фиксируем embeddings в кэше, чтобы следующий старт
                    # не переобучал их заново (главная задержка прогрева)
                    try:
                        self._save_index()
                    except Exception:
                        pass
        except Exception as e:
            print(f"  (побочное обучение пропущено: {e})")

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
        current = 0.0
        if key in self.qa_boost:
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
                current = 0.0
            else:
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
                # CBOW-векторы из кэша: если есть — не переобучаем дорогие embeddings
                self.cbow_vectors = state.get("cbow_vectors", {}) or {}
                self._cbow_built = bool(state.get("cbow_built", False)) and bool(self.cbow_vectors)
                if state.get("cbow_dim"):
                    self.cbow_dim = state["cbow_dim"]
                self._load_boost_state()
                self._loaded = True
                if not LITE_MODE:
                    self._load_perceptron()
                self._loaded = True
                if not self._ingested_corpus_files:
                    corpus_dir = DATA_DIR / "corpus_ready"
                    if corpus_dir.exists():
                        for f in corpus_dir.glob("*.jsonl"):
                            self._ingested_corpus_files.add(f.name)
                if not LITE_MODE and self.doc_tf is None:
                    dt0 = time.time()
                    self.doc_tf = [Counter(self.tokenize(inst)) for inst, _, _ in self.examples]
                    print(f"  doc_tf пересчитан из examples за {time.time()-dt0:.1f}s")
                elif LITE_MODE:
                    self.doc_tf = None
                    self._apply_lite_cap()
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
                # CBOW-векторы: персистентны между стартами, чтобы не переобучать
                # дорогие embeddings при каждом запуске (основная задержка прогрева)
                "cbow_vectors": self.cbow_vectors,
                "cbow_built": self._cbow_built,
                "cbow_dim": self.cbow_dim,
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
            if w not in self.stop_words and len(w) >= 3:
                # Кэш стемминга (только как ускоритель; синонимизацию применяем всегда)
                cached = self._stem_cache.get(w)
                if cached is not None:
                    stemmed.append(self._apply_synonym(w, cached))
                    continue
                original_w = w
                if w in self.morph_exceptions:
                    w = self.morph_exceptions[w]
                elif w in self.stem_exceptions_ru:
                    w = self.stem_exceptions_ru[w]
                else:
                    for suffix, replacement in self.stem_rules_ru.items():
                        if w.endswith(suffix) and len(w) > len(suffix) + 2:
                            w = w[:-len(suffix)] + replacement
                            break
                w = self._apply_synonym(original_w, w)
                self._stem_cache[original_w] = w
                stemmed.append(w)
        return stemmed

    def _apply_synonym(self, word, stem):
        """Канонизирует стем через словарь синонимов (по исходному слову И по стему).
        Один return: str."""
        if word in self.synonyms_ru:
            return self.synonyms_ru[word]
        if stem in self.synonyms_ru:
            return self.synonyms_ru[stem]
        return stem

    # ========================
    #  BUILD INDEX
    # ========================
    # Приоритет кластеров: ценные сначала (по алфавиту generated шёл бы первым и съедал лимит)
    CLUSTER_PRIORITY = ["ru", "math", "code", "design", "general", "knowledge",
                        "3d", "document", "presentation", "research", "system", "generated"]

    def _cluster_priority(self, name):
        priority = 99
        try:
            priority = self.CLUSTER_PRIORITY.index(name)
        except ValueError:
            priority = 99
        return priority

    def _load_processed_files(self):
        """Файлы processed, отсортированные по приоритету кластера. Один return: list."""
        files = sorted((DATA_DIR / "processed").glob("*.jsonl"))
        files.sort(key=lambda f: self._cluster_priority(f.stem))
        return files

    def _build_doc_index(self):
        """Строит total_docs/vocab/word2idx/doc_tf. Один return: None."""
        self.total_docs = max(len(self.examples), 1)
        self.vocab = [w for w, _ in self.doc_freq.most_common(50000)]
        self.word2idx = {w: i for i, w in enumerate(self.vocab)}
        self.embedding_size = min(300, len(self.vocab))
        if not LITE_MODE:
            self.doc_tf = []
            for inst, out, cl in self.examples:
                self.doc_tf.append(Counter(self.tokenize(inst)))
        else:
            self.doc_tf = None
        return None

    def _train_side(self):
        """Побочное обучение (NB, CBOW). Один return: None."""
        try:
            if not self.nb_priors:
                self.nb_train()
            if not self._cbow_built:
                self.build_cbow_embeddings(max_examples=20000)
        except Exception as e:
            print(f"  (побочное обучение пропущено: {e})")
        return None

    def _build(self):
        print("  [Mirro Algorithms] building indexes...")
        t0 = time.time()
        for f in self._load_processed_files():
            with open(f, "r", encoding="utf-8") as fh:
                self._ingest_lines(fh, f.stem)
            if len(self.examples) >= MAX_INMEMORY_EXAMPLES:
                print(f"  Достигнут лимит памяти ({MAX_INMEMORY_EXAMPLES}) — остальное отдаётся RAG-индексу")
                break
        self._build_doc_index()
        print(f"  Index: {len(self.examples)} ex, {len(self.vocab)} vocab, {time.time()-t0:.0f}s")
        self._extend_from_corpus()
        if not LITE_MODE:
            self._train_side()

    def _ingest_example(self, inst, out, cluster):
        """Добавляет один пример в индексы. Один return: int idx добавленного."""
        idx = len(self.examples)
        self.examples.append((inst, out, cluster))
        words = self.tokenize(inst + " " + out[:200])
        self.term_freq.update(words)
        for w in set(words):
            self.doc_freq[w] += 1
            self.term_docs[w].add(idx)
        return idx

    def _ingest_lines(self, fh, cluster):
        """Добавляет примеры из файла-заглушки до лимита. Один return: int добавлено."""
        added = 0
        for line in fh:
            if len(self.examples) >= MAX_INMEMORY_EXAMPLES:
                break
            if line.strip():
                try:
                    ex = json.loads(line)
                    inst = ex.get("instruction", ex.get("user", ""))
                    out = ex.get("output", ex.get("assistant", ""))
                    if inst and out and len(out) > 5:
                        self._ingest_example(inst, out, cluster)
                        added += 1
                except Exception:
                    pass
        return added

    def _rebuild_after_extend(self, added):
        """Перестраивает doc_tf/vocab после добавления. Один return: None."""
        if not LITE_MODE and self.doc_tf is not None:
            for i in range(len(self.examples) - added, len(self.examples)):
                self.doc_tf.append(Counter(self.tokenize(self.examples[i][0])))
        self.total_docs = max(len(self.examples), 1)
        self.vocab = [w for w, _ in self.doc_freq.most_common(50000)]
        self.word2idx = {w: i for i, w in enumerate(self.vocab)}
        self.embedding_size = min(300, len(self.vocab))
        print(f"  +{added} из корпуса, итого {len(self.examples)} примеров, {len(self.vocab)} слов")
        return None

    def _ingest_jsonl_dir(self, directory, cluster):
        """Добавляет малые .jsonl из папки в индекс. Один return: int добавлено."""
        added = 0
        if directory.exists():
            for f in sorted(directory.glob("*.jsonl")):
                if f.name not in self._ingested_corpus_files:
                    if f.stat().st_size > 10_000_000:
                        self._ingested_corpus_files.add(f.name)
                    else:
                        with open(f, "r", encoding="utf-8") as fh:
                            added += self._ingest_lines(fh, cluster)
                        self._ingested_corpus_files.add(f.name)
                        if len(self.examples) >= MAX_INMEMORY_EXAMPLES:
                            break
        return added

    def _extend_from_corpus(self):
        """Добавляет примеры из corpus_ready и self_learned в индекс без полной
        пересборки (история ИИ и самообученные пары становятся искомыми).
        Один return: None."""
        added = self._ingest_jsonl_dir(DATA_DIR / "corpus_ready", "corpus")
        added += self._ingest_jsonl_dir(DATA_DIR / "self_learned", "learned")
        if added:
            self._rebuild_after_extend(added)
        return None

    # ========================
    #  1. TF-IDF SEARCH
    # ========================
    def tfidf(self, term):
        """IDF weight for a term."""
        df = self.doc_freq.get(term, 1)
        return math.log(self.total_docs / (1 + df))

    def _rare_scored_words(self, q_counts):
        """Слова запроса по редкости (IDF). Один return: list (idf, word, qt)."""
        scored_words = [(self.tfidf(w), w, qt) for w, qt in q_counts.items()]
        scored_words.sort(key=lambda x: -x[0])
        return scored_words

    def _tf_lazy(self, ex_id, w):
        """Ленивый подсчёт tf для lite-режима (doc_tf не хранится в RAM).
        Один return: int частота слова в документе."""
        cnt = Counter(self.tokenize(self.examples[ex_id][0]))
        return cnt.get(w, 0)

    def _apply_lite_cap(self):
        """Обрезает загруженный индекс под lite-режим: оставляет первые
        MAX_INMEMORY_EXAMPLES примеров и пересобирает term_docs на их основе.
        Это компактнее, чем set-of-int на весь объём. Один return: None."""
        if len(self.examples) > MAX_INMEMORY_EXAMPLES:
            keep = MAX_INMEMORY_EXAMPLES
            self.examples = self.examples[:keep]
            self.total_docs = max(len(self.examples), 1)
            self.vocab = [w for w, _ in self.doc_freq.most_common(50000)]
            self.word2idx = {w: i for i, w in enumerate(self.vocab)}
            new_term_docs = defaultdict(set)
            for idx, (inst, out, _cl) in enumerate(self.examples):
                valid = set(self.tokenize(inst + " " + out[:200]))
                for w in valid:
                    new_term_docs[w].add(idx)
            self.term_docs = new_term_docs
            # Обрезаем частотные словари до слов, реально оставшихся в индексе
            if self.doc_freq:
                self.doc_freq = Counter({w: self.doc_freq[w] for w in set(self.doc_freq) & set(new_term_docs)})
            if self.term_freq:
                self.term_freq = Counter({w: self.term_freq[w] for w in set(self.term_freq) & set(new_term_docs)})
            print(f"  lite-режим: индекс обрезан до {len(self.examples)} примеров, {len(self.doc_freq)} terms")
        return None

    def _accumulate_scores(self, scored_words):
        """Аккумулирует BM25-оценки по документам. Один return: dict ex_id->score."""
        scores = {}
        MAX_DOCS = 15000
        for idf, w, qt in scored_words:
            if idf >= 0.5:
                doc_ids = self.term_docs.get(w, set())
                for ex_id in doc_ids:
                    if ex_id in scores:
                        scores[ex_id] += qt * idf * 0.5
                    else:
                        if self.doc_tf is not None:
                            tf = self.doc_tf[ex_id].get(w, 0)
                        else:
                            tf = self._tf_lazy(ex_id, w)
                        bm25 = idf * (tf * 1.5) / (tf + 1.5)
                        scores[ex_id] = bm25 * qt
                    if len(scores) > MAX_DOCS:
                        break
                if len(scores) > MAX_DOCS:
                    break
        return scores

    def search_tfidf(self, query, top_n=5):
        """TF-IDF поиск с BM25-like нормализацией. Быстрый: использует предвычисленные TF.
        Один return: list of ((inst,out,cl), score)."""
        result = []
        q_words = self.tokenize(query)
        if q_words:
            scored_words = self._rare_scored_words(Counter(q_words))
            scores = self._accumulate_scores(scored_words)
            if scores:
                best = sorted(scores.items(), key=lambda x: -x[1])[:top_n]
                result = [(self.examples[ex_id], sc) for ex_id, sc in best]
        return result

    # ========================
    #  2. TEXT RANK — суммаризация
    # ========================
    def textrank_summarize(self, text, ratio=0.3):
        """
        TextRank: извлекает самые важные предложения через граф.
        Чистый Python, без numpy.
        """
        sentences = [s.strip() for s in _re.split(r'[.!?]', text) if len(s.strip()) > 20]
        result = text
        if len(sentences) > 3:
            # Build similarity matrix (cosine overlap)
            n = len(sentences)
            sim_matrix = [[0.0] * n for _ in range(n)]
            sent_words = [set(self.tokenize(s)) for s in sentences]

            for i in range(n):
                for j in range(i + 1, n):
                    if sent_words[i] and sent_words[j]:
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
            result = " ".join(sentences[i] for i in top_indices)
        return result

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
                if w in self.word2idx:
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

    def _init_cbow(self, rnd, vocab, dim):
        """Инициализация CBOW-векторов. Один return: (in_vec, out_vec)."""
        in_vec = {w: [rnd.uniform(-0.01, 0.01) for _ in range(dim)] for w in vocab}
        out_vec = {w: [0.0] * dim for w in vocab}
        return in_vec, out_vec

    def _iter_cbow_windows(self, window, max_examples, word2idx):
        """Генератор (target, ctx) из выборки. Один return: (через yield)."""
        for _, text, _ in self.examples[:max_examples]:
            words = self.tokenize(text)
            if len(words) >= 2:
                for i, target in enumerate(words):
                    if target in word2idx:
                        ctx = [words[j] for j in range(max(0, i - window), min(len(words), i + window + 1)) if j != i]
                        yield target, ctx

    def _train_cbow_step(self, target, ctx, in_vec, out_vec, dim, lr):
        """Один шаг обучения CBOW. Один return: None."""
        ctx = [w for w in ctx if w in self.word2idx]
        if ctx:
            avg = [sum(in_vec[w][d] for w in ctx) / len(ctx) for d in range(dim)]
            score = sum(x * y for x, y in zip(avg, out_vec[target]))
            error = (1.0 / (1.0 + math.exp(-score))) - 1.0
            for d in range(dim):
                out_vec[target][d] -= lr * error * avg[d]
            for w in ctx:
                for d in range(dim):
                    in_vec[w][d] -= (lr * error * out_vec[target][d]) / len(ctx)
        return None

    def _normalize_cbow(self, in_vec, vocab):
        """Нормирует и фиксирует CBOW-векторы. Один return: dict word->vec."""
        import math as _m
        out = {}
        for w in vocab:
            v = in_vec[w]
            norm = _m.sqrt(sum(x * x for x in v)) or 1.0
            out[w] = [x / norm for x in v]
        return out

    def build_cbow_embeddings(self, window=2, max_examples=20000):
        """Строит собственные word embeddings через CBOW (без numpy).

        Для каждого окна контекста предсказывает целевое слово по среднему
        Результат — self.cbow_vectors: word -> float[dim].
        """
        if self._cbow_built or not self.word2idx:
            return
        import random as _rnd
        rnd = _rnd.Random(42)
        vocab = list(self.word2idx.keys())
        dim = max(4, min(self.cbow_dim, len(vocab) // 2 or 1))
        in_vec, out_vec = self._init_cbow(rnd, vocab, dim)
        lr = 0.05
        for target, ctx in self._iter_cbow_windows(window, max_examples, self.word2idx):
            self._train_cbow_step(target, ctx, in_vec, out_vec, dim, lr)
        self.cbow_vectors = self._normalize_cbow(in_vec, vocab)
        self.cbow_dim = dim
        self._cbow_built = True
        print(f"  CBOW: {len(self.cbow_vectors)} векторов, dim={dim}")

    def cbow_similarity(self, word_a, word_b):
        """Косинусная близость по CBOW-векторам (0..1)."""
        sim = 0.0
        if self._cbow_built and word_a in self.cbow_vectors and word_b in self.cbow_vectors:
            va = self.cbow_vectors[word_a]
            vb = self.cbow_vectors[word_b]
            sim = sum(x * y for x, y in zip(va, vb))
        return sim

    def cosine_similarity(self, text1, text2):
        """Cosine similarity between two texts."""
        words1 = set(self.tokenize(text1))
        words2 = set(self.tokenize(text2))
        common = words1 & words2
        sim = 0.0
        if common:
            sim = len(common) / math.sqrt(len(words1) * len(words2))
        return sim

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
        result = {}
        if priors:
            vals = {cl: (p ** alpha) for cl, p in priors.items() if p > 0}
            s = sum(vals.values()) or 1.0
            result = {cl: v / s for cl, v in vals.items()}
        return result

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
        result = []
        if words:
            word_scores = {}
            total = len(words)
            for w in set(words):
                tf = words.count(w) / total
                idf = self.tfidf(w)
                word_scores[w] = tf * idf
            ranked = sorted(word_scores.items(), key=lambda x: -x[1])
            result = [w for w, _ in ranked[:top_n]]
        return result

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
        q_words = set(self.tokenize(question))
        a_words = set(self.tokenize(answer))

        score = 0.0
        if len(answer) < 20:
            score = 0.0
        elif not q_words:
            score = 0.3
        else:
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
            pr = 0.0
            if not ref_ngrams:
                pr = 1.0 if n == 1 else 0.0
            else:
                hyp_ngrams = _ngrams(hyp_tokens, n)
                if hyp_ngrams:
                    from collections import Counter as _C
                    ref_counts = _C(ref_ngrams)
                    hyp_counts = _C(hyp_ngrams)
                    clipped = sum(min(c, ref_counts.get(g, 0)) for g, c in hyp_counts.items())
                    pr = clipped / len(hyp_ngrams)
            return pr

        import re as _re
        ref_tokens = _re.findall(r"[а-яёa-z0-9]+", reference.lower())
        hyp_tokens = _re.findall(r"[а-яёa-z0-9]+", hypothesis.lower())
        score = 0.0
        if ref_tokens and hyp_tokens:
            # Средняя точность n-грамм (shift от 1 для стабильности 0..1)
            precisions = [_precision(ref_tokens, hyp_tokens, n) for n in range(1, max_n + 1)]
            avg_prec = sum(precisions) / max_n

            # Brevity penalty: штраф за слишком короткий ответ
            bp = 1.0 if len(hyp_tokens) > len(ref_tokens) else max(0.0, min(1.0, len(hyp_tokens) / max(len(ref_tokens), 1)))

            # Взвешиваем: unigram важнее, brevity-штраф умеренный
            score = min(1.0, avg_prec * (0.7 + 0.3 * bp))
        return score

    def self_eval_bleu(self, question, answer):
        """Self-eval: находит эталон из базы и сравнивает с ответом через BLEU.

        Возвращает (bleu_score, reference), где reference — ближайший эталон
        из базы (или None, если база пуста). Высокий балл = ответ хорошо
        совпадает с эталоном знаний.
        """
        results = self.search_tfidf(question, top_n=1)
        bleu = 0.0
        ref = None
        if results:
            (inst, ref, cl), sc = results[0]
            bleu = self.bleu_score(ref, answer)
        return bleu, ref

    # ========================
    #  7. SELF-CORRECTION
    # ========================
    def self_correct(self, question, initial_answer):
        """
        Самокоррекция: проверяет ответ, ищет лучше.
        """
        # Check quality
        score = self.qa_score(question, initial_answer)
        best_text = initial_answer
        best_score = score
        if score <= 0.6:
            # Try to improve: search for better examples
            results = self.search_tfidf(question, top_n=8)
            if results:
                found_text = ""
                found_score = 0
                for (inst, out, cl), sc in results:
                    if out and len(out) > 50:
                        s = self.qa_score(question, out)
                        if s > found_score:
                            found_score = s
                            found_text = out
                if found_text and found_score > score:
                    best_text = found_text
                    best_score = found_score
        return best_text, best_score

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
        val = 0.0
        try:
            val = 1.0 / (1.0 + math.exp(-z))
        except OverflowError:
            val = 0.0 if z < 0 else 1.0
        return val

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
        # Негативное обучение: ЗАПОМИНАЕМ плохой ответ (дизлайк), чтобы в будущем
        # он не предлагался снова — понижаем сильнее, чем простой буст, и держим
        # в отдельной «чёрной» памяти (с экспоненциальным забыванием давних).
        if not liked and response:
            self._remember_bad_answer(query, response)
        self._save_boost_state()
        return learned

    def _remember_bad_answer(self, query, response, decay_hours=72.0):
        """Память о плохих ответах: запоминает (вопрос → не-подходящий ответ)
        с меткой времени; находит при поиске и понижает. Один return: None."""
        try:
            if not hasattr(self, "bad_answers"):
                self.bad_answers = {}
            key = (self._boost_key(query), self._boost_key(response))
            self.bad_answers[key] = time.time()
            # забываем давние (дольше decay_hours) — чтобы отсев не был вечным
            cutoff = time.time() - decay_hours * 3600
            keep = {k: ts for k, ts in self.bad_answers.items() if ts > cutoff}
            if len(keep) < len(self.bad_answers):
                self.bad_answers = keep
        except Exception:
            pass
        return None

    def _interest_boost(self, candidate):
        """Персонализация по интересам: если ответ перекликается с любимыми
        темами пользователя (из профиля user_profile.json), повышает score.
        Один return: float (0..0.3)."""
        boost = 0.0
        try:
            from algos.user_profile import load_profile
        except Exception:
            try:
                import os as _os_mod
                sys.path.insert(0, _os_mod.path.dirname(_os_mod.path.dirname(_os_mod.path.abspath(__file__))))
                from algos.user_profile import load_profile
            except Exception:
                load_profile = None
        if load_profile is None or not candidate:
            return boost
        try:
            prof = load_profile()
            topics = prof.get("topics") or []
            if not topics:
                return boost
            cand_low = (candidate or "").lower()
            for t in topics:
                t_low = (t or "").lower().strip()
                core = t_low.split()[0] if t_low else ""
                if core and len(core) >= 4:
                    for w in self.tokenize(core):
                        if w and w in cand_low:
                            boost = max(boost, 0.15)
                            break
                    if boost >= 0.15:
                        break
            if boost >= 0.15:
                boost += 0.15  # заметный приоритет любимой темы
        except Exception:
            boost = 0.0
        return min(boost, 0.3)

    def _bad_penalty(self, query, candidate):
        """Штраф, если (вопрос,кандидат) похож на ранее отмеченный как плохой.
        Один return: float (>=0)."""
        penalty = 0.0
        try:
            bad = getattr(self, "bad_answers", {}) or {}
            if not bad:
                return penalty
            qk = self._boost_key(query)
            ck = self._boost_key(candidate)
            for (bqk, bck) in bad:
                if bck == ck or (bqk == qk and bck.split()[:3] == ck.split()[:3]):
                    penalty += 0.5
        except Exception:
            penalty = 0.0
        return penalty

    def train_from_history(self, batch_size=32, epochs=1):
        """Пакетное обучение перцептрона на накопленной истории feedback.

        Пере-обучает на батче оценённых пользователем (query, response, liked)
        пар. Более устойчиво, чем одиночные шаги: каждый пример обновляется
        без хрупкой последовательности (epochs проходов по батчу).
        Возвращает количество отработанных примеров.
        """
        processed = 0
        if self.feedback_history:
            batch = self.feedback_history[-batch_size:]
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
    def _cache_get(self, query):
        """Поиск в кэше по ключу. Один return: str-ответ или None."""
        cache_key = query.strip().lower()[:100]
        result = None
        if cache_key in self.cache:
            result = self.cache[cache_key]
        return result

    def _cache_put(self, query, value):
        """Кладёт ответ в кэш с ограничением размера. Один return: None."""
        cache_key = query.strip().lower()[:100]
        if len(self.cache) >= self.cache_max:
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[cache_key] = value
        return None

    # ----- FAQ-ускорение: тёплый кэш частых запросов с готовыми ответами -----
    def _faq_key(self, query):
        """Нормализованный ключ FAQ. Один return: str."""
        return _re.sub(r"[^а-яёa-z0-9 ]+", " ", (query or "").lower()).strip()[:80]

    def _faq_get(self, query):
        """Ищет готовый ответ в FAQ-кэше. Один return: str|None."""
        result = None
        key = self._faq_key(query)
        if key and key in getattr(self, "faq_cache", {}):
            result = self.faq_cache[key]
        return result

    def _faq_put(self, query, answer, min_hits=3):
        """Накапливает популярные пары: при частом повторе вопроса кэширует
        готовый ответ, чтобы отвечать мгновенно. Один return: None."""
        key = self._faq_key(query)
        if not key:
            return None
        if not hasattr(self, "faq_cache"):
            self.faq_cache = {}
        if not hasattr(self, "faq_hits"):
            self.faq_hits = {}
        self.faq_hits[key] = self.faq_hits.get(key, 0) + 1
        if self.faq_hits[key] >= min_hits:
            if len(self.faq_cache) >= self.cache_max:
                # вытесняем первый (по порядку вставки)
                self.faq_cache = dict(list(self.faq_cache.items())[-self.cache_max:])
            self.faq_cache[key] = answer
        return None

    def _score_answers(self, query, results):
        """Оценивает кандидатов (перцептрон+qa+буст предпочтений). Один return: list."""
        scored = []
        seen = set()
        for (inst, out, cl), tfidf_score in results:
            if out and out[:50] not in seen:
                seen.add(out[:50])
                nn_score = self.perceptron_predict(query, out)
                qa = self.qa_score(query, out)
                boost = self._decay_boost(self._boost_key(out))
                combined = 0.3 * tfidf_score + 0.3 * nn_score + 0.4 * qa + boost
                # негативное обучение: ранее отмеченный дизлайком ответ понижается
                combined -= self._bad_penalty(query, out)
                # персонализация по интересам: ответы, перекликающиеся с любимыми
                # темами пользователя (из профиля), ранжируются чуть выше
                combined += self._interest_boost(out)
                scored.append((combined, out, cl))
        return scored

    def _semantic_rerank(self, query, candidates):
        """Второй проход: переоценивает кандидатов по ОХВАТУ ТЕМЫ вопроса
        (доля стем-слов вопроса, найденных в ответе), а не только по
        сырому score. Возвращает отранжированный список (score, out, cl),
        где итоговый = 0.6*старый + 0.4*покрытие темы. Мягкий: если нет
        пересечения слов — оставляет исходный порядок. Один return: list."""
        q_set = {self.tokenize(w)[0] for w in query.split() if self.tokenize(w)} if query else set()
        if not q_set:
            return candidates
        ranked = []
        # нормируем raw score к [0,1] для стабильного веса
        scores = [c[0] for c in candidates] or [0.0]
        lo, hi = min(scores), max(scores)
        rng = (hi - lo) or 1.0
        for sc, out, cl in candidates:
            out_set = set(self.tokenize(out)) if out else set()
            cov = len(q_set & out_set) / max(len(q_set), 1) if out_set else 0.0
            norm = (sc - lo) / rng
            # нулевой охват темы = явно мимо → штраф, чтобы релевантность не проигрывала
            penalty = 0.25 if cov < 0.1 else 0.0
            final = 0.5 * norm + 0.5 * min(cov, 1.0) - penalty
            ranked.append((final, out, cl))
        ranked.sort(key=lambda x: -x[0])
        return ranked

    def _pick_3_parts(self, scored):
        """Берёт топ-3 ответа из разных кластеров. Один return: list строк."""
        scored.sort(key=lambda x: -x[0])
        parts = []
        used_cl = set()
        for sc, out, cl in scored:
            if len(parts) >= 3:
                break
            if cl not in used_cl:
                parts.append(out[:1200].strip())
                used_cl.add(cl)
        return parts

    def _summarize_parts(self, parts, max_len):
        """Склеивает и при необходимости суммаризирует. Один return: str."""
        combined = "\n\n".join(parts)[:max_len]
        if len(combined) > 1500 and len(parts) > 1:
            combined = self.textrank_summarize(combined, ratio=0.5)
        return combined

    def compose_answer(self, query, top_n=8, max_len=4000):
        """
        Полный пайплайн: FAQ-кэш → кэш → поиск → фильтрация перцептроном → дедупликация → TextRank → самокоррекция.
        Один return: str-ответ или None.
        """
        result = None
        cached = self._faq_get(query)
        if cached is not None:
            result = cached
        else:
            cached = self._cache_get(query)
        if cached is not None:
            result = cached
        else:
            results = self.search_tfidf(query, top_n=top_n)
            if results:
                scored = self._score_answers(query, results)
                if scored:
                    parts = self._pick_3_parts(self._semantic_rerank(query, scored))
                    if parts:
                        combined = self._summarize_parts(parts, max_len)
                        corrected, _ = self.self_correct(query, combined)
                        self._cache_put(query, corrected)
                        # FAQ-ускорение: накапливаем популярные пары для мгновенных ответов
                        self._faq_put(query, corrected)
                        result = corrected
                    else:
                        self._cache_put(query, None)
                else:
                    self._cache_put(query, None)
            else:
                self._cache_put(query, None)
        return result

    # ========================
    #  AUTONOMOUS SELF-LEARNING (60-min loop)
    # ========================
    def autonomous_learn(self, cycles=30):
        """Автономное самообучение: генерирует вопросы из своей базы,
        отвечает, оценивает, корректирует перцептрон.

        Умный отбор: редкие кластеры (которые редко спрашивали) получают
        приоритет, чтобы наука росла равномерно, а не только к популярному."""
        learned = 0
        import random as _rnd

        # Считаем, как часто отвечалось на кластер (балансировка)
        cluster_use = dict(self.cluster_calls) if hasattr(self, "cluster_calls") else {}
        use_counts = {}
        for _, _, cl in self.examples:
            use_counts[cl] = use_counts.get(cl, 0) + 1
        total = sum(use_counts.values()) or 1
        # кластеры с долей использования < половины средней — «редкие»
        avg_share = 1.0 / max(1, len(use_counts))
        rare = [cl for cl, n in use_counts.items() if n / total < avg_share * 0.7]

        # Pick sample of examples, preferring rare clusters
        sample = self.examples
        if len(sample) > 5000:
            if rare:
                rare_examples = [e for e in self.examples if e[2] in rare]
                rest = [e for e in self.examples if e[2] not in rare]
                take_rare = min(len(rare_examples), int(cycles * 0.6))
                sample = (_rnd.sample(rare_examples, take_rare) if rare_examples else []) + \
                         (_rnd.sample(rest, cycles - take_rare) if rest and cycles > take_rare else [])
            else:
                sample = _rnd.sample(self.examples, 5000)

        for inst, out, cl in sample[:cycles]:
            if len(inst) >= 8:
                # Generate answer with current model
                ans = self.compose_answer(inst, top_n=4)
                if ans:
                    # Evaluate: compare with the reference answer
                    ref_words = set(self.tokenize(out))
                    ans_words = set(self.tokenize(ans))
                    if ref_words:
                        coverage = len(ans_words & ref_words) / len(ref_words)

                        # Learn = train perceptron on this QA pair
                        label = 1 if coverage > 0.3 else -1
                        self.perceptron_train(inst, ans, label)
                        # Хебб-закрепление опыта: успех/каша → укрепление/ослабление
                        # рёбер графа, через которые прошёл ответ (автономный цикл).
                        try:
                            from algos.knowledge_graph import kg as _kg
                            from algos.neural_electric import hebbian_update_path, fire
                            start = self.tokenize(inst)
                            anchor = None
                            for w in start:
                                if w in _kg.nodes:
                                    anchor = w
                                    break
                            if anchor:
                                chain = fire(_kg, anchor, max_hops=2)
                                path = [n for n, _h, _v in chain]
                                if len(path) >= 2:
                                    hebbian_update_path(_kg, path,
                                                        feedback_sign=1.0 if label > 0 else -1.0,
                                                        learning_rate=0.005)
                        except Exception:
                            pass
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
        risk = 1.0
        if ans_words:
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
    # ========================
    #  СОЗНАНИЕ КАК СВЯЗНОСТЬ (IIT) — уровень интегрированности знаний
    # ========================
    def _integrated_info(self, max_terms=6000):
        """Аналог «интегрированной информации» IIT (Тониони): насколько кластеры
        знаний связаны между собой через общие слова, а не изолированы.

        Берём уже построенный term_docs (слово -> set id примеров), по каждому
        частотному слову смотрим, в скольких кластерах оно встречается. Мера
        интеграции φ ∈ [0..1] = доля «перекрёстных» слов (слово есть в ≥2
        кластерах). Дёшево и мгновенно — без повторной токенизации.

        Один return: dict {phi, shared_terms, checked_terms, cluster_pairs, clusters}.
        """
        # топ-слова по частоте документов, ограниченно — чтобы не обходить всё
        top_terms = dict(sorted(self.doc_freq.items(), key=lambda x: -x[1])[:max_terms])
        pairs = {}
        checked = 0
        shared = 0
        for w in top_terms:
            ids = self.term_docs.get(w)
            if ids:
                cls = set()
                seen = 0
                for ex_id in ids:
                    if ex_id < len(self.examples):
                        cls.add(self.examples[ex_id][2])
                        seen += 1
                    if seen >= 200:
                        break
                checked += 1
                if len(cls) >= 2:
                    shared += 1
                    cl_list = sorted(cls)[:4]
                    key = f"{cl_list[0]}↔{cl_list[1]}" + (f"+{len(cl_list)-2}" if len(cl_list) > 2 else "")
                    pairs[key] = pairs.get(key, 0) + 1
        phi = (shared / checked) if checked else 0.0
        return {
            "phi": round(phi, 4),
            "shared_terms": shared,
            "checked_terms": checked,
            "cluster_pairs": dict(sorted(pairs.items(), key=lambda x: -x[1])[:12]),
            "clusters": len(set(c for _i, _o, c in self.examples)),
            "notes": "аналог IIT: доля частотных слов, связывающих два и более кластера",
        }

    def status(self):
        state = {
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
        # «Уровень сознания» как связность кластеров (аналог IIT).
        try:
            state["consciousness_phi"] = self._integrated_info()
        except Exception as e:
            state["consciousness_phi"] = {"phi": 0.0, "error": str(e)}
        return state

    # ========================
    #  НОВЫЕ АЛГОРИТМЫ (не трогая старые)
    # ========================

    # 1. JACCARD — мера сходства текстов
    def jaccard_similarity(self, text1, text2):
        """Jaccard: |пересечение| / |объединение| на множествах слов."""
        w1 = set(self.tokenize(text1))
        w2 = set(self.tokenize(text2))
        sim = 0.0
        if w1 and w2:
            inter = len(w1 & w2)
            union = len(w1 | w2)
            sim = inter / union if union else 0.0
        return sim

    # 2. SPELLCHECK — исправление опечаток по словарю
    def spellcheck(self, text):
        """Заменяет опечатки на ближайшие слова из вокабуляра (edit distance 1)."""
        words = _re.findall(r"[а-яёa-z]+", text.lower())
        corrections = {}
        vocab = set(self.vocab[:20000])  # ограничим для скорости
        for w in words:
            if w not in vocab and len(w) >= 4 and w not in self.stop_words:
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
            if abs(len(candidate) - len(word)) <= 2:
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
            if w in self.cooc_matrix:
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
        result = sentences
        if len(sentences) > top_k:
            q_words = set(self.tokenize(question))
            ranked = []
            for s in sentences:
                s_words = set(self.tokenize(s))
                score = len(q_words & s_words) + self.jaccard_similarity(question, s)
                ranked.append((score, s))
            ranked.sort(key=lambda x: -x[0])
            result = [s for _, s in ranked[:top_k]]
        return result

    # 5. AUTO-LEARN TRIGGER — сигнал автообучения
    def should_auto_learn(self, question, answer):
        """Решает, нужно ли Mirro дообучиться: если ответ слабый (короткий/риск)."""
        score = self.qa_score(question, answer)
        risk = self.detect_hallucination(question, answer)
        # Учимся, если ответ слабый ИЛИ высокий риск галлюцинаций
        return (score < 0.35) or (risk > 0.8)

    # 6. COMPOSE с новыми алгоритмами (надстройка, не меняя старый compose)
    def _expanded_query(self, query):
        """Spellcheck + query expansion. Один return: строка запроса."""
        clean_query = self.spellcheck(query)
        expansion = self.query_expansion(clean_query)
        search_query = clean_query + " " + " ".join(expansion)
        return search_query

    def _score_candidates(self, query, clean_query, results):
        """Ранжирует кандидатов (перцептрон+jaccard+qa). Один return: список."""
        scored = []
        seen = set()
        for (inst, out, cl), tfidf_score in results:
            if out and out[:50] not in seen:
                seen.add(out[:50])
                nn = self.perceptron_predict(query, out)
                ja = self.jaccard_similarity(clean_query, out)
                qa = self.qa_score(clean_query, out)
                combined = 0.25 * tfidf_score + 0.25 * nn + 0.25 * ja + 0.25 * qa
                scored.append((combined, out, cl))
        return scored

    def _pick_parts(self, clean_query, scored, max_len):
        """Собирает до 3 частей из разных кластеров. Один return: строка."""
        scored.sort(key=lambda x: -x[0])
        parts = []
        used_cl = set()
        for sc, out, cl in scored:
            if len(parts) >= 3:
                break
            if cl not in used_cl:
                top_sents = self.sentence_rank(clean_query, out, top_k=2)
                parts.append(" ".join(top_sents)[:1100])
                used_cl.add(cl)
        return "\n\n".join(parts)[:max_len]

    def compose_answer_v2(self, query, top_n=8, max_len=4000):
        """Улучшенный пайплайн: spellcheck → query expansion → jaccard/rank."""
        search_query = self._expanded_query(query)
        results = self.search_tfidf(search_query, top_n=top_n)
        answer_parts = None
        if results:
            scored = self._score_candidates(query, self.spellcheck(query), results)
            if scored:
                answer_parts = self._pick_parts(self.spellcheck(query), scored, max_len)
        return answer_parts


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