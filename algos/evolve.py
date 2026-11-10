# -*- coding: utf-8 -*-
"""Mirro Algorithms — 26 · Нейроэволюция (Neuroevolution / NEAT-lite)

Проблема: обычный градиентный спуск застревает в локальных минимумах,
особенно при творческой генерации. Решение (биологически обоснованное):
вместо обучения ОДНОЙ сети эволюционирует ПОПУЛЯЦИЯ графов.

Каждый индивид = небольшой граф узлов-перцептронов со своими уровнями
нейромедиаторов (дофамин, серотонин, ацетилхолин) и весами связей.
  * МУТАЦИЯ  — меняет веса и базовые уровни нейромедиаторов.
  * СКРЕЩИВАНИЕ — берёт веса и «химию» от двух лучших родителей.
  * ОТБОР (fitness) — выживают графы, чьи ответы физически стабильны
    (малая PINN-ошибка) и энергетически экономны.

Лучшие паттерны автоматически записываются в Базу Опыта (experience),
формируя долгосрочную память системы.

Чистый Python, без внешних библиотек — как все нейро-модули Mirro.
"""
import math
import random as _rnd


def _sigmoid(x):
    """Мешает плавно. Один return: float."""
    val = 0.0
    try:
        val = 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        val = 0.0 if x < 0 else 1.0
    return val


class PerceptronNode:
    """Локальный перцептрон узла графа. Чистый Python, один return на метод."""
    __slots__ = ("w", "b", "hidden")

    def __init__(self, input_dim, hidden_dim, rng):
        dim = input_dim
        scale = math.sqrt(2.0 / dim) if dim else 0.5
        self.w = [[rng.uniform(-scale, scale) for _ in range(hidden_dim)] for _ in range(dim)]
        self.b = [0.0 for _ in range(hidden_dim)]
        self.hidden = hidden_dim

    def forward(self, x):
        """Прямой проход (ReLU). Один return: list."""
        out = []
        for j in range(self.hidden):
            s = self.b[j]
            for i, xi in enumerate(x):
                if i < len(self.w):
                    s += xi * self.w[i][j]
            out.append(max(0.0, s))
        return out


class Genome:
    """Индивид: граф перцептронов + нейромедиаторы + веса межузловых связей.
    Мутация/скрещивание производят новые геномы."""
    def __init__(self, num_nodes, input_dim, hidden_dim, rng):
        if num_nodes < 1:
            num_nodes = 1
        if hidden_dim < 1:
            hidden_dim = 1
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        self.nodes = [PerceptronNode(input_dim, hidden_dim, rng) for _ in range(num_nodes)]
        # межузловые веса: w_g[i][j] — из i в j
        self.w_graph = [[rng.uniform(-0.5, 0.5) for _ in range(num_nodes)] for _ in range(num_nodes)]
        # нейромедиаторы: уровни [0..1], их порог активации
        self.dopamine = rng.uniform(0.0, 1.0)
        self.serotonin = rng.uniform(0.5, 1.0)
        self.acetylcholine = rng.uniform(0.5, 1.0)
        self.gsr = rng.uniform(0.2, 0.9)      # виртуальное «возбуждение»
        self.decoder = [rng.uniform(-0.5, 0.5) for _ in range(hidden_dim)]

    # ---------- генетические операторы ----------
    def mutate(self, strength=0.3, rng=_rnd):
        """Мутация весов и уровней нейромедиаторов. Один return: self."""
        for node in self.nodes:
            for i in range(len(node.w)):
                for j in range(len(node.w[i])):
                    if rng.random() < strength:
                        node.w[i][j] += rng.uniform(-0.5, 0.5)
                    if rng.random() < 0.02:
                        node.w[i][j] = rng.uniform(-0.5, 0.5)
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                if rng.random() < strength:
                    self.w_graph[i][j] += rng.uniform(-0.5, 0.5)
        # нейромедиаторы: ступенчатая мутация уровней
        self.dopamine = self._mutate_level(self.dopamine, rng)
        self.serotonin = self._mutate_level(self.serotonin, rng)
        self.acetylcholine = self._mutate_level(self.acetylcholine, rng)
        self.gsr = self._mutate_level(self.gsr, rng)
        # декодер
        for i in range(len(self.decoder)):
            if rng.random() < strength:
                self.decoder[i] += rng.uniform(-0.5, 0.5)
        return self

    @staticmethod
    def _mutate_level(val, rng):
        nv = val + rng.uniform(-0.2, 0.2)
        return max(0.0, min(2.0, nv))

    def crossover(self, other, rng=_rnd):
        """Скрещивание: каждый параметр — случайно от одного из родителей.
        Один return: новый Genome."""
        child = Genome(self.num_nodes, len(self.nodes[0].w), self.hidden_dim, rng)
        for i in range(len(child.nodes)):
            src = self if rng.random() < 0.5 else other
            cn = child.nodes[i]
            sn = src.nodes[i]
            for r in range(len(cn.w)):
                for c in range(len(cn.w[r])):
                    cn.w[r][c] = sn.w[r][c]
                cn.b[r] = sn.b[r]
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                src = self if rng.random() < 0.5 else other
                child.w_graph[i][j] = src.w_graph[i][j]
        # химия тоже скрещивается
        child.dopamine = self.dopamine if rng.random() < 0.5 else other.dopamine
        child.serotonin = self.serotonin if rng.random() < 0.5 else other.serotonin
        child.acetylcholine = self.acetylcholine if rng.random() < 0.5 else other.acetylcholine
        child.gsr = self.gsr if rng.random() < 0.5 else other.gsr
        for i in range(self.hidden_dim):
            src = self if rng.random() < 0.5 else other
            child.decoder[i] = src.decoder[i]
        return child

    # ---------- инференс ----------
    def forward(self, A, X):
        """Одна эпоха: инференс + физическая оценка. Один return: dict."""
        n, h = self.num_nodes, self.hidden_dim
        latent = [self.nodes[i].forward(X[i]) for i in range(n)]
        # Message passing: ацетилхолин масштабирует силу внимания соседей,
        # серотонин стабилизирует, GSR при «стрессе» повышает проводимость.
        flow = [[0.0] * h for _ in range(n)]
        for i in range(n):
            for j in range(n):
                w_eff = A[i][j] * self.acetylcholine * (1.0 + self.gsr)
                if w_eff > 0:
                    for k in range(h):
                        flow[i][k] += w_eff * latent[j][k]
        state = [[0.0] * h for _ in range(n)]
        for i in range(n):
            for k in range(h):
                s = flow[i][k]
                for j in range(n):
                    s += self.w_graph[j][i] * latent[j][k]
                s = s * self.serotonin + self.dopamine * 0.5
                state[i][k] = s * _sigmoid(s)
        # декодер: агрегировать объём графа в ответ
        agg = [0.0] * h
        for i in range(n):
            for k in range(h):
                agg[k] += state[i][k]
        for k in range(h):
            agg[k] /= n
        response = sum(agg[k] * self.decoder[k] for k in range(h))
        # энергия и физичность (PINN-стиль)
        actual_energy = sum(state[i][k] ** 2 for i in range(n) for k in range(h))
        return {
            "latent": state,
            "embedding": agg,
            "response": response,
            "energy": actual_energy,
            "nodes": n,
        }


class MirroEvolver:
    """Популяция геномов + эволюционный отбор. Один return на метод."""
    def __init__(self, num_nodes=3, input_dim=3, hidden_dim=4, pop_size=12,
                 target_energy=0.6, rng=None, seed=42):
        self.num_nodes = num_nodes
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.pop_size = pop_size
        self.target_energy = target_energy
        self.rng = _rnd.Random(seed) if rng is None else rng
        self.population = [
            Genome(num_nodes, input_dim, hidden_dim, self.rng) for _ in range(pop_size)
        ]
        self.generation = 0
        self.experience_base = []       # успешные эмбеддинги (память)
        self.max_experience = 50
        self._best = None
        self._best_fitness = float("-inf")
        self.fitness_history = []       # лучший fitness по поколениям (для дашборда)

    # ---------- отбор ----------
    def _physics_loss(self, energy):
        """Отклонение энергобаланса от цели сцены. Один return: float."""
        return abs(energy - self.target_energy)

    def _fitness(self, genome, A, X, energy_cost=0.2):
        """Оценка: качество ответа + физичность − метабол. энергия.
        energy_cost клампится в [0,1]. Один return: float."""
        try:
            energy_cost = max(0.0, min(1.0, float(energy_cost or 0.2)))
        except Exception:
            energy_cost = 0.2
        out = genome.forward(A, X)
        phys = self._physics_loss(out["energy"])
        # физичность: чем меньше отклонение от физики, тем лучше
        # энергэкономичность: чем меньше потребление при хорошем ответе
        quality = abs(out["response"])
        cost = out["energy"] * energy_cost
        return quality - phys * 0.8 - cost

    def evolve_step(self, A, X, mutation=0.3, elite=2):
        """Один шаг эволюции: оценить, отобрать, скрестить, смутировать.
        mutation клампится в [0,1]. Один return: dict (статистика поколения)."""
        try:
            mutation = max(0.0, min(1.0, float(mutation or 0.3)))
        except Exception:
            mutation = 0.3
        scored = []
        for g in self.population:
            fit = self._fitness(g, A, X)
            scored.append((fit, g))
        scored.sort(key=lambda x: -x[0])
        if not scored:
            # пустая популяция — нет данных для эволюции
            return {"generation": self.generation, "best_fit": 0.0, "avg_fit": 0.0,
                    "best_dopamine": None, "best_serotonin": None,
                    "experience": len(self.experience_base),
                    "history": list(self.fitness_history[-30:])}
        # запомнить глобально лучшего
        if scored[0][0] > self._best_fitness:
            self._best_fitness = scored[0][0]
            self._best = scored[0][1]
        # сохранить успешные (физически стабильные) эмбеддинги в опыт
        for fit, g in scored[:max(1, elite)]:
            if fit > 0:
                emb = g.forward(A, X)["embedding"]
                self.save_experience(emb)
        # элита проходит дальше без изменений (минимум 1, чтобы не опустеть)
        elite = max(1, min(int(elite or 1), len(scored)))
        new_pop = [g for _fit, g in scored[:elite]]
        # остальные — скрещивание лучших + мутация
        while len(new_pop) < self.pop_size:
            p1 = scored[self.rng.randint(0, max(1, elite + 1))][1]
            p2 = scored[self.rng.randint(0, max(1, elite + 1))][1]
            child = p1.crossover(p2, self.rng).mutate(mutation, self.rng)
            new_pop.append(child)
        self.population = new_pop or self.population
        self.generation += 1
        avg_fit = sum(f for f, _ in scored) / len(scored) if scored else 0.0
        # фиксируем лучший fitness этого поколения в историю (для прогресса на дашборде)
        self.fitness_history.append(round(scored[0][0], 4))
        if len(self.fitness_history) > 200:
            self.fitness_history = self.fitness_history[-200:]
        return {
            "generation": self.generation,
            "best_fit": round(scored[0][0], 4),
            "avg_fit": round(avg_fit, 4),
            "best_dopamine": round(self._best.dopamine, 3) if self._best else None,
            "best_serotonin": round(self._best.serotonin, 3) if self._best else None,
            "experience": len(self.experience_base),
            "history": list(self.fitness_history[-30:]),
        }

    def save_experience(self, embedding):
        """Фиксирует стабильный паттерн в базу опыта.
        Пустой/None-эмбеддинг пропускается. Один return: None."""
        if not embedding:
            return None
        if len(self.experience_base) >= self.max_experience:
            self.experience_base.pop(0)
        self.experience_base.append(list(embedding))
        return None

    def best_genome(self):
        """Текущий лучший геном (в популяции или за всю эволюцию).
        Один return: Genome или None."""
        best = self._best
        # если лучший ещё не отдельно сохранён — ищем в текущей популяции
        if best is None and self.population:
            best = self.population[0]
        return best


# Глобальный эволюционер (синглтон для try_evolve)
_evolver = None


def get_evolver():
    """Лениво создаёт глобальный эволюционер. Один return: MirroEvolver."""
    global _evolver
    if _evolver is None:
        _evolver = MirroEvolver(seed=42)
    return _evolver


def _default_A(n):
    """Граф связей по умолчанию (полный, с диагональю). Один return: list."""
    return [[1.0 if i == j else 0.4 for j in range(n)] for i in range(n)]


def _default_X(n, dim=3):
    """Биометрия узлов по умолчанию: [пульс, возбуждение, энергия].
    Возвращает ровно n строк по dim значений. Один return: list."""
    rows = []
    for i in range(n):
        values = [0.7 + 0.1 * i, 0.4 + 0.1 * i, 0.8 + 0.05 * i]
        rows.append(values[:dim])
    return rows[:n]


def _integrated_fitness(ev, genome, A, X):
    """Fitness с учётом живого состояния: размера графа знаний и уровня
    нейромедиаторов (спаек). Адаптация входов по текущему состоянию системы.
    Один return: float."""
    fit = ev._fitness(genome, A, X)
    boost = 0.0
    try:
        from algos.knowledge_graph import kg
        # больше знаний в графе => чуть легче получить хороший ответ
        boost += min(0.5, len(kg.nodes) / 5000.0) * 0.05
    except Exception:
        pass
    try:
        from algos.neuromodulators import nm
        lvl = getattr(nm, "level", {})
        dop = lvl.get("dopamine", 0.0)
        # дофамин как «ошибка предсказания награды» стимулирует поиск
        boost += max(0.0, dop - 0.5) * 0.1
    except Exception:
        pass
    return fit + boost


def try_evolve(query):
    """Точка входа: запускает шаг эволюции только по явному запросу
    («эволюция», «поколение», «нейроэволюция», «развивайся»).
    Иначе возвращает None, чтобы не перехватывать обычный диалог.
    Один return: str|None."""
    ans = None
    q = (query or "").lower()
    want_evolve = any(w in q for w in ("эволюц", "поколени", "нейроэволюц",
                                       "развивайся", "мутац", "скрещива"))
    if want_evolve:
        ev = get_evolver()
        n = ev.num_nodes
        A = _default_A(n)
        X = _default_X(n, ev.input_dim)
        ev.evolve_step(A, X)  # обычный шаг с базовым фитнесом внутри
        # дополнительно усилим связь с системой: подмешаем живые факторы
        fit_base = max(ev._fitness(ev.best_genome(), A, X), 0.0)
        boost = 0.0
        try:
            boost = _integrated_fitness(ev, ev.best_genome(), A, X) - fit_base
        except Exception:
            boost = 0.0
        ans = (f"Эволюция поколение {ev.generation}: лучший fitness "
               f"{fit_base:.3f} (+{boost:.3f} от знаний и медиаторов), "
               f"в популяции {len(ev.population)} графов, "
               f"опыт: {len(ev.experience_base)} паттернов.")
    return ans


def report(query=""):
    """Статус текущей эволюции. Один return: str."""
    ev = get_evolver()
    g = ev.best_genome()
    chem = ""
    if g:
        chem = (f"дофамин {g.dopamine:.2f}, серотонин {g.serotonin:.2f}, "
                f"ацетилхолин {g.acetylcholine:.2f}")
    return (f"Популяция {len(ev.population)} графов, поколение {ev.generation}, "
            f"база опыта {len(ev.experience_base)}. Лучший: {chem or 'ещё не оценён'}.")


if __name__ == "__main__":
    e = MirroEvolver(num_nodes=3, input_dim=3, hidden_dim=4, pop_size=10, seed=42)
    AA = _default_A(3)
    XX = _default_X(3, 3)
    print("старт:", report.__doc__ if False else report())
    for _ in range(5):
        print(try_evolve(""))
    print("финал:", report())