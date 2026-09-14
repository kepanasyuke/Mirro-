#!/usr/bin/env python3
"""
Mirro Core AI — собственные алгоритмы
=====================================
Без внешних API, без марковских цепей, без зависимостей.
Алгоритмы:
  1. TF-IDF поиск — находит лучшие примеры по вопросу
  2. Self-question — берёт вопросы из своей базы и учится на них
  3. Self-evaluation — оценивает качество своего ответа
  4. Adaptive scoring — запоминает, какие совпадения работают лучше
"""

import json, random, math, time, re as _re
from pathlib import Path
from collections import Counter, defaultdict

PROC = Path(r"D:\Mirro\data\processed")
STATE_FILE = Path(r"D:\Mirro\data\ai_state.json")


class MirroAI:
    """
    Ядро Mirro: собственные алгоритмы поиска, генерации и обучения.
    """

    def __init__(self):
        self.term_freq = Counter()      # term -> total occurrences
        self.doc_freq = Counter()       # term -> docs containing term  
        self.total_docs = 0
        self.examples = []              # all (instruction, output) pairs
        self.self_questions = []        # (question, best_answer_id)
        self.boost_map = {}             # normalized query hash -> score boost
        self._loaded = False
        self._load_state()
        self._build_index()

    def _load_state(self):
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text("utf-8"))
                self.boost_map = data.get("boost_map", {})
            except Exception:
                pass

    def _save_state(self):
        STATE_FILE.write_text(json.dumps({
            "boost_map": self.boost_map,
            "updated": time.time(),
        }, ensure_ascii=False), "utf-8")

    def _tokenize(self, text):
        return [w for w in _re.findall(r"[а-яёa-z0-9]+", text.lower()) if len(w) > 1]

    def _build_index(self):
        """Строит TF-IDF индекс по всем данным."""
        print("Building Mirro AI index...")
        if self._loaded:
            return
        total = 0
        for f in sorted(PROC.glob("*.jsonl")):
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        try:
                            ex = json.loads(line)
                            inst = ex.get("instruction", ex.get("user", ""))
                            out = ex.get("output", ex.get("assistant", ""))
                            if inst and out and len(out) > 20:
                                idx = len(self.examples)
                                self.examples.append((inst, out, f.stem))
                                words = self._tokenize(inst)
                                self.term_freq.update(words)
                                for w in set(words):
                                    self.doc_freq[w] += 1
                                total += 1
                        except Exception:
                            pass
        self.total_docs = max(total, 1)
        self._load_self_questions()
        self._loaded = True
        print(f"  Index: {total} examples, {len(self.term_freq)} unique terms")

    def _tfidf(self, term, doc_count):
        """TF-IDF вес термина в документе."""
        if term not in self.doc_freq:
            return 0
        df = self.doc_freq[term]
        idf = math.log(self.total_docs / (1 + df))
        return doc_count * idf

    def search(self, query: str, top_n=5) -> list:
        """TF-IDF поиск: находит лучшие примеры под вопрос."""
        query_words = self._tokenize(query)
        if not query_words:
            return []

        query_tfidf = {w: self._tfidf(w, query_words.count(w)) for w in set(query_words)}
        scored = []
        for idx, (inst, output, cluster) in enumerate(self.examples):
            inst_words = self._tokenize(inst)
            if not inst_words:
                continue
            # Term overlap with TF-IDF weighting
            common = set(query_words) & set(inst_words)
            if not common:
                continue
            score = sum(query_tfidf.get(w, 0) for w in common)
            # Normalize by doc length
            score /= math.sqrt(len(inst_words))
            # Boost from previous success
            boost = self.boost_map.get(hash(inst) % 100000, 0)
            score += boost
            if score > 0:
                scored.append((score, output, inst, cluster))

        scored.sort(key=lambda x: -x[0])
        return scored[:top_n]

    def compose_answer(self, results, max_len=4000):
        """Компонует ответ из найденных результатов."""
        if not results:
            return None
        seen = set()
        parts = []
        for score, output, inst, cluster in results:
            if output[:80] in seen:
                continue
            seen.add(output[:80])
            parts.append(output[:1200].strip())
        if parts:
            combined = "\n\n".join(parts)[:max_len]
            return combined
        return None

    def self_question_loop(self, count=10):
        """Генерирует вопросы из своих данных и отвечает на них."""
        if len(self.examples) == 0:
            return 0
        learned = 0
        for _ in range(count):
            # Pick a random example
            inst, output, cluster = random.choice(self.examples[:10000])
            if len(inst) < 10:
                continue
            # Search for best answer
            results = self.search(inst, top_n=3)
            if results and results[0][0] > 0.01:
                # Evaluate: how much of the original answer does our response cover?
                answer = self.compose_answer(results)
                if answer:
                    orig_words = set(self._tokenize(output[:500]))
                    gen_words = set(self._tokenize(answer[:500]))
                    if orig_words:
                        coverage = len(gen_words & orig_words) / len(orig_words)
                        if coverage > 0.3:
                            # Good match — save as learned
                            boost_key = hash(inst) % 100000
                            self.boost_map[boost_key] = self.boost_map.get(boost_key, 0) + 0.1
                            learned += 1
        self._save_state()
        return learned

    def learn_from_feedback(self, query, response, liked):
        """Учится на лайках/дизлайках пользователя."""
        key = hash(query.strip().lower()) % 100000
        if liked:
            self.boost_map[key] = self.boost_map.get(key, 0) + 0.5
        else:
            self.boost_map[key] = max(0, self.boost_map.get(key, 0) - 0.3)
        self._save_state()

    def _load_self_questions(self):
        """Формирует список вопросов из инструкций."""
        seen = set()
        for inst, out, cluster in self.examples[:5000]:
            if len(inst) > 10 and inst[:60] not in seen:
                seen.add(inst[:60])
                self.self_questions.append(inst)

    def status(self):
        return {
            "indexed": len(self.examples),
            "unique_terms": len(self.term_freq),
            "self_questions": len(self.self_questions),
            "boost_entries": len(self.boost_map),
        }


ai = MirroAI()


def generate_answer(query: str, cluster: str = "") -> str:
    """Главная функция: поиск + компоновка ответа."""
    results = ai.search(query, top_n=5)
    answer = ai.compose_answer(results)
    if answer:
        return answer
    return None


def run_self_learning(cycles=20):
    """Запускает самообучение Mirro."""
    learned = ai.self_question_loop(cycles)
    return learned


if __name__ == "__main__":
    print("Mirro AI — Self-learning test")
    print(f"Index: {ai.status()['indexed']} examples")

    # Test search
    for q in ["Что такое НДС?", "Как заменить mspaint на маке?", "Напиши код сортировки"]:
        results = ai.search(q, top_n=3)
        answer = ai.compose_answer(results)
        if answer:
            print(f"\nQ: {q}")
            print(f"A ({len(answer)} chars): {answer[:300]}")
        else:
            print(f"\nQ: {q}  → не найдено")

    # Self-learning
    print("\n\nSelf-learning...")
    n = run_self_learning(50)
    print(f"Learned from {n} self-questions")
    print(f"Boosts: {ai.status()['boost_entries']}")