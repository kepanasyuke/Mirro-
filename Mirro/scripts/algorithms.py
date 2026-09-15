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

import json, math, re as _re, collections, random, time
from pathlib import Path
from collections import Counter, defaultdict

MAX_INMEMORY_EXAMPLES = 800_000
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
        self.qa_boost = {}          # query hash -> boost value
        self.cache = {}             # query -> cached answer
        self.cache_max = 200
        self._ingested_corpus_files = set()

        # Перцептрон (1-слойная нейросеть)
        self.perceptron_weights = {}  # word -> weight
        self.perceptron_bias = 0.0
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

        # TextRank graph
        self.graph_ready = False

        # Naive Bayes
        self.nb_priors = Counter()
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
                self.doc_tf = state["doc_tf"]
                self._stem_cache = state.get("stem_cache", {})
                self.nb_priors = state.get("nb_priors", Counter())
                self.nb_word_probs = state.get("nb_word_probs", defaultdict(Counter))
                self.nb_total_words = state.get("nb_total_words", Counter())
                self._ingested_corpus_files = state.get("ingested_corpus_files", set())
                self._loaded = True
                if not self._ingested_corpus_files:
                    corpus_dir = DATA_DIR / "corpus_ready"
                    if corpus_dir.exists():
                        for f in corpus_dir.glob("*.jsonl"):
                            self._ingested_corpus_files.add(f.name)
                print(f"  Индекс загружен из кэша за {time.time()-t0:.1f}s ({len(self.examples)} ex, {len(self.doc_freq)} terms)")
        except Exception as e:
            print(f"  Кэш индекса не загрузился: {e}")

    def _save_index(self):
        """Сохраняет индекс в pickle для быстрого старта."""
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
                "doc_tf": self.doc_tf,
                "stem_cache": self._stem_cache,
                "nb_priors": self.nb_priors,
                "nb_word_probs": self.nb_word_probs,
                "nb_total_words": self.nb_total_words,
                "ingested_corpus_files": self._ingested_corpus_files,
            }
            with open(self.INDEX_CACHE, "wb") as f:
                pickle.dump(state, f, protocol=4)
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

        # После сборки индекса подгружаем корпусные сегменты
        self._extend_from_corpus()

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

        print(f"  {len(self.nb_priors)} classes trained")

    def nb_classify(self, text):
        """Naive Bayes классификация текста по кластерам."""
        words = self.tokenize(text)
        best_cl = None
        best_log = -1e9

        for cl, prior in self.nb_priors.items():
            log_prob = math.log(prior)
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
        """Преобразует вопрос+кандидат в вектор признаков."""
        q_words = set(self.tokenize(query))
        c_words = set(self.tokenize(candidate))
        common = q_words & c_words

        f1 = len(common) / max(len(q_words), 1)                    # overlap ratio
        f2 = len(common) / max(len(c_words), 1)                    # recall
        f3 = math.log(len(candidate) + 1) / 10                     # length bonus
        f4 = 1.0 if any(w in candidate.lower() for w in q_words) else 0.0  # exact hit
        return [f1, f2, min(f3, 1.0), f4]

    def perceptron_train(self, query, candidate, label):
        """Обучает перцептрон на одном примере (label = 1 хороший, -1 плохой)."""
        x = self.perceptron_vectorize(query, candidate)
        features = [f"f{i}" for i in range(len(x))]
        # Инициализация весов при первом вызове
        for fname in features:
            if fname not in self.perceptron_weights:
                self.perceptron_weights[fname] = 0.0

        # Прямой проход
        activation = sum(self.perceptron_weights.get(f, 0) * x[i] for i, f in enumerate(features)) + self.perceptron_bias
        prediction = 1 if activation >= 0 else -1

        # Обновление весов если ошибка
        if prediction != label:
            for i, fname in enumerate(features):
                self.perceptron_weights[fname] += self.perceptron_lr * label * x[i]
            self.perceptron_bias += self.perceptron_lr * label

        return prediction == label

    def perceptron_predict(self, query, candidate):
        """Предсказывает релевантность ответа (0..1)."""
        x = self.perceptron_vectorize(query, candidate)
        features = [f"f{i}" for i in range(len(x))]
        activation = sum(self.perceptron_weights.get(f, 0) * x[i] for i, f in enumerate(features)) + self.perceptron_bias
        # Sigmoid-like scaling to 0..1
        return 1.0 / (1.0 + math.exp(-activation))

    def train_from_feedback(self, query, response, liked):
        """Обучает перцептрон на feedback пользователя (лайк/дизлайк)."""
        label = 1 if liked else -1
        return self.perceptron_train(query, response, label)

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

        # 2. Score candidates with perceptron + QA score
        scored = []
        seen = set()
        for (inst, out, cl), tfidf_score in results:
            if not out or out[:50] in seen:
                continue
            seen.add(out[:50])
            nn_score = self.perceptron_predict(query, out)
            qa = self.qa_score(query, out)
            combined = 0.3 * tfidf_score + 0.3 * nn_score + 0.4 * qa
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
            "embeddings": len(self.word_vectors),
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