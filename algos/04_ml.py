# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 04 · Машинное обучение (10 алгоритмов)
Чистый Python.
"""

import math, random
from collections import Counter, defaultdict


def euclidean(a, b):
    """Евклидово расстояние."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def linear_regression(X, y):
    """Простая линейная регрессия y = kx + b (метод наименьших квадратов)."""
    n = len(X)
    mx, my = sum(X) / n, sum(y) / n
    num = sum((x - mx) * (yy - my) for x, yy in zip(X, y))
    den = sum((x - mx) ** 2 for x in X)
    k = num / den if den else 0
    b = my - k * mx
    return k, b


def predict_line(k, b, x):
    """Предсказание линейной регрессии."""
    return k * x + b


def kmeans(X, k=2, iters=20):
    """Кластеризация k-means. X: список точек. Возвращает центры и метки."""
    random.seed(1)
    centers = random.sample(list(X), min(k, len(X)))
    for _ in range(iters):
        clusters = [[] for _ in centers]
        for p in X:
            d = [euclidean(p, c) for c in centers]
            clusters[d.index(min(d))].append(p)
        new_centers = []
        for cl in clusters:
            if cl:
                new_centers.append(tuple(sum(c[i] for c in cl) / len(cl) for i in range(len(cl))))
            else:
                new_centers.append(centers[clusters.index(cl)] if clusters[clusters.index(cl)] else cl[0])
        if new_centers == centers:
            break
        centers = new_centers
    labels = []
    for p in X:
        d = [euclidean(p, c) for c in centers]
        labels.append(d.index(min(d)))
    return centers, labels


def knn(X, y, point, k=3):
    """k ближайших соседей (классификация)."""
    d = sorted((euclidean(point, x), label) for x, label in zip(X, y))
    votes = Counter(label for _, label in d[:k])
    return votes.most_common(1)[0][0]


class NaiveBayes:
    """Наивный Байес для категориального/текстового признака."""

    def __init__(self):
        self.priors = {}
        self.likelihoods = defaultdict(Counter)
        self.classes = []

    def fit(self, X, y):
        n = len(y)
        self.classes = list(set(y))
        yc = Counter(y)
        for c in self.classes:
            self.priors[c] = yc[c] / n
        for xi, yi in zip(X, y):
            for w in set(str(xi).split()):
                self.likelihoods[yi][w] += 1
        # сглаживание — добавим фиктивное слово в каждый класс
        for c in self.classes:
            self.likelihoods[c]["__vocab__"] = sum(self.likelihoods[c].values())

    def predict(self, text):
        best, best_p = None, -1
        for c in self.classes:
            total = self.likelihoods[c].get("__vocab__", 1)
            p = math.log(self.priors[c])
            for w in str(text).split():
                p += math.log((self.likelihoods[c].get(w, 0) + 1) / (total + 1))
            if p > best_p:
                best_p, best = p, c
        return best


def logistic(x):
    """Сигмоида."""
    return 1 / (1 + math.exp(-x))


def logistic_train(X, y, lr=0.01, iters=100):
    """Логистическая регрессия (2 класса, бинарный признак x)."""
    w, b = 0.1, 0.0
    for _ in range(iters):
        for xi, yi in zip(X, y):
            pred = logistic(w * xi + b)
            err = yi - pred
            w += lr * err * xi
            b += lr * err
    return w, b


def decision_tree_stump(X, y):
    """Пень дерева решений: выбор порога по одному признаку."""
    best = (None, None, -1)
    for th in sorted(set(X)):
        left = [l for x, l in zip(X, y) if x <= th]
        right = [l for x, l in zip(X, y) if x > th]
        if not left or not right:
            continue
        imp = 0.0
        for grp in (left, right):
            p = grp.count(1) / len(grp) if grp else 0
            gini = 1 - p * p - (1 - p) * (1 - p)
            imp += (len(grp) / len(y)) * gini
        if imp < best[2] or best[2] == -1:
            best = (th, 1 if sum(left) >= len(left) / 2 else 0, imp)
    return best[0], best[1]


def gradient_descent(grad, start, lr=0.1, iters=100):
    """Общий градиентный спуск."""
    x = start
    for _ in range(iters):
        x = x - lr * grad(x)
    return x


def feature_scale(X):
    """Нормализация признаков (z-score)."""
    n = len(X)
    means = [sum(p[i] for p in X) / n for i in range(len(X[0]))]
    sds = []
    for i in range(len(X[0])):
        m = means[i]
        v = sum((p[i] - m) ** 2 for p in X) / n
        sds.append(math.sqrt(v) or 1)
    return [[(p[i] - means[i]) / sds[i] for i in range(len(X[0]))] for p in X]


def train_test_split(X, y, frac=0.8, seed=1):
    """Разделение на обучающую/тестовую выборки."""
    random.seed(seed)
    idx = list(range(len(X)))
    random.shuffle(idx)
    cut = int(len(idx) * frac)
    tr, te = idx[:cut], idx[cut:]
    return [X[i] for i in tr], [X[i] for i in te], [y[i] for i in tr], [y[i] for i in te]


if __name__ == "__main__":
    k, b = linear_regression([1, 2, 3, 4, 5], [3, 5, 7, 9, 11])
    print("reg:", k, b, "pred(6)=", predict_line(k, b, 6))
    X = [(1, 1), (2, 2), (5, 5), (6, 6)]
    centers, labels = kmeans(X, k=2)
    print("kmeans labels:", labels)
    data = [(0, 0), (0, 1), (10, 10), (11, 11)]
    labs = [0, 0, 1, 1]
    print("knn:", knn(data, labs, (0.5, 0.5)))
    nb = NaiveBayes()
    nb.fit(["хороший день", "плохой день", "хороший фильм"], ["pos", "neg", "pos"])
    print("nb predict:", nb.predict("хороший фильм"))