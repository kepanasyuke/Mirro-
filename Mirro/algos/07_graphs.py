# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 07 · Графы (10 алгоритмов)
Граф: adjacency list {node: [(neighbor, weight)]}
"""

from collections import deque


def bfs(graph, start):
    """Обход в ширину: порядок обхода."""
    seen, order = {start}, [start]
    q = deque([start])
    while q:
        node = q.popleft()
        for nei, _ in graph.get(node, []):
            if nei not in seen:
                seen.add(nei)
                order.append(nei)
                q.append(nei)
    return order


def dfs(graph, start):
    """Обход в глубину (рекурсивно): порядок обхода."""
    seen, order = set(), []

    def rec(node):
        seen.add(node)
        order.append(node)
        for nei, _ in graph.get(node, []):
            if nei not in seen:
                rec(nei)

    rec(start)
    return order


def has_cycle_directed(graph):
    """Проверка на цикл в ориентированном графе."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}

    def visit(n):
        color[n] = GRAY
        for nei, _ in graph.get(n, []):
            if color.get(nei, WHITE) == GRAY:
                return True
            if color.get(nei, WHITE) == WHITE and visit(nei):
                return True
        color[n] = BLACK
        return False

    for n in graph:
        if color[n] == WHITE and visit(n):
            return True
    return False


def topological_sort(graph):
    """Топологическая сортировка (Kahn)."""
    indeg = {n: 0 for n in graph}
    for n in graph:
        for nei, _ in graph[n]:
            indeg[nei] = indeg.get(nei, 0) + 1
    q = deque([n for n, d in indeg.items() if d == 0])
    out = []
    while q:
        n = q.popleft()
        out.append(n)
        for nei, _ in graph.get(n, []):
            indeg[nei] -= 1
            if indeg[nei] == 0:
                q.append(nei)
    return out if len(out) == len(graph) else None


def dijkstra(graph, start):
    """Кратчайшие пути Дийкстры: {node: dist}."""
    import heapq
    dist = {n: float("inf") for n in graph}
    dist[start] = 0
    pq = [(0, start)]
    while pq:
        d, n = heapq.heappop(pq)
        if d > dist[n]:
            continue
        for nei, w in graph.get(n, []):
            nd = d + w
            if nd < dist[nei]:
                dist[nei] = nd
                heapq.heappush(pq, (nd, nei))
    return dist


def kruskal_mst(graph):
    """Минимальное остовное дерево (Краскал). Граф неориентированный adj list."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            return True
        return False

    edges = []
    seen = set()
    for n, neigh in graph.items():
        for m, w in neigh:
            key = tuple(sorted((n, m)))
            if key not in seen:
                seen.add(key)
                edges.append((w, n, m))
    edges.sort()
    mst = []
    for w, a, b in edges:
        if union(a, b):
            mst.append((a, b, w))
    return mst


def connected_components(graph):
    """Компоненты связности."""
    seen, comps = set(), []
    for start in graph:
        if start in seen:
            continue
        comp = bfs(graph, start)
        seen.update(comp)
        comps.append(comp)
    return comps


def bipartite_check(graph):
    """Проверка двудольности (2-раскраска BFS)."""
    color = {}

    def ok(start):
        color[start] = 0
        q = deque([start])
        while q:
            n = q.popleft()
            for nei, _ in graph.get(n, []):
                if nei not in color:
                    color[nei] = 1 - color[n]
                    q.append(nei)
                elif color[nei] == color[n]:
                    return False
        return True

    for n in graph:
        if n not in color and not ok(n):
            return False
    return True


def graph_diameter_bfs(graph):
    """Диаметр (для невзвеш. графа): максимум кратчайших путей через BFS."""
    mx = 0
    for s in graph:
        dist = {s: 0}
        q = deque([s])
        while q:
            n = q.popleft()
            for nei, _ in graph.get(n, []):
                if nei not in dist:
                    dist[nei] = dist[n] + 1
                    q.append(nei)
        mx = max(mx, max(dist.values()))
    return mx


def adjacency_matrix(graph):
    """Матрица смежности для неориентированного графа."""
    nodes = sorted(graph.keys())
    idx = {n: i for i, n in enumerate(nodes)}
    mat = [[0] * len(nodes) for _ in nodes]
    for n, neigh in graph.items():
        for m, w in neigh:
            mat[idx[n]][idx[m]] = w or 1
    return nodes, mat


def is_island(grid, r, c):
    """(задача на сетке) заливка: размер компонента из клетки."""
    if not (0 <= r < len(grid) and 0 <= c < len(grid[0])) or grid[r][c] != 1:
        return 0
    grid[r][c] = -1  # посещено
    size = 1
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        size += is_island(grid, r + dr, c + dc)
    return size


if __name__ == "__main__":
    g = {
        "a": [("b", 4), ("c", 2)],
        "b": [("c", 1), ("d", 5)],
        "c": [("d", 8)],
        "d": [],
    }
    print("bfs:", bfs(g, "a"))
    print("dfs:", dfs(g, "a"))
    print("dijkstra:", dijkstra(g, "a"))
    print("cycle:", has_cycle_directed(g))
    print("topo:", topological_sort(g))