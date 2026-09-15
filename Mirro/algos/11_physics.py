# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 11 · Физика: трёх тел, спектры, небесная механика
Задача трёх тел — численное интегрирование Ньютоновской гравитации (RK4).
Спектры — формула Ридберга, серии Бальмера/Лаймана/Пашена.
"""

import math

G = 6.674e-11     # гравитационная постоянная
M_SUN = 1.989e30  # масса Солнца
AU = 1.496e11     # астрономическая единица


def gravitational_force(m1, m2, r):
    """Сила гравитационного притяжения."""
    return G * m1 * m2 / (r * r)


def orbital_period(a, m_central):
    """Период орбиты (3-й закон Кеплера)."""
    return 2 * math.pi * math.sqrt(a ** 3 / (G * m_central))


def escape_velocity(m, r):
    """Вторая космическая скорость."""
    return math.sqrt(2 * G * m / r)


def kinetic_energy(m, v):
    return 0.5 * m * v * v


def potential_energy_grav(m1, m2, r):
    return -G * m1 * m2 / r


def free_fall_time(h, g=9.81):
    """Время падения с высоты (без учёта сопротивления)."""
    return math.sqrt(2 * h / g)


def pendulum_period(L, g=9.81):
    """Период математического маятника."""
    return 2 * math.pi * math.sqrt(L / g)


def rydberg_wavelength(n1, n2, Z=1):
    """
    Длина волны перехода по формуле Ридберга (спектр атома водорода).
    n1 < n2. Возвращает длину волны в метрах.
    """
    R = 1.097373e7  # постоянная Ридберга (м^-1)
    inv = R * (Z ** 2) * (1 / (n1 * n1) - 1 / (n2 * n2))
    return 1 / inv if inv > 0 else None


def balmer_series(n_max, n1=2):
    """Серия Бальмера: длины волн переходов n→2 (нм)."""
    out = []
    for n in range(n1 + 1, n_max + 1):
        wl = rydberg_wavelength(n1, n)
        if wl:
            out.append((n, wl * 1e9))  # нм
    return out


def lyman_series(n_max):
    """Серия Лаймана: переходы n→1 (нм)."""
    return [(n, rydberg_wavelength(1, n) * 1e9) for n in range(2, n_max + 1)]


def hydrogen_level_energy(n):
    """Энергия уровня атома водорода (эВ)."""
    return -13.6 / (n * n)


def photon_energy_from_wavelength(wl_m):
    """Энергия фотона по длине волны (Дж)."""
    h = 6.626e-34
    c = 3e8
    return h * c / wl_m


def de_broglie_wavelength(m, v):
    """Длина волны де Бройля."""
    h = 6.626e-34
    return h / (m * v)


def dv_dt(states):
    """Производная ускорений для N тел (задача многих тел)."""
    n = len(states)
    deriv = []
    for i in range(n):
        ax = ay = az = 0.0
        for j in range(n):
            if i == j:
                continue
            dx = states[j]["x"] - states[i]["x"]
            dy = states[j]["y"] - states[i]["y"]
            dz = states[j]["z"] - states[i]["z"]
            r3 = (dx * dx + dy * dy + dz * dz) ** 1.5
            if r3 < 1e-9:
                continue
            ax += G * states[j]["m"] * dx / r3
            ay += G * states[j]["m"] * dy / r3
            az += G * states[j]["m"] * dz / r3
        deriv.append({"ax": ax, "ay": ay, "az": az})
    return deriv


def three_body_step(states, dt):
    """
    Задача трёх тел: один шаг численного интегрирования (РК4).
    states: [{"m":..,"x":..,"y":..,"z":..,"vx":..,"vy":..,"vz":..}]
    Возвращает новые состояния.
    """
    def accel(s):
        d = dv_dt(s)
        return d

    # k1
    a1 = accel(states)
    s2 = []
    for i, st in enumerate(states):
        s2.append({**st, "x": st["x"] + 0.5 * dt * st["vx"], "y": st["y"] + 0.5 * dt * st["vy"],
                   "z": st["z"] + 0.5 * dt * st["vz"], "vx": st["vx"] + 0.5 * dt * a1[i]["ax"],
                   "vy": st["vy"] + 0.5 * dt * a1[i]["ay"], "vz": st["vz"] + 0.5 * dt * a1[i]["az"]})
    a2 = accel(s2)
    s3 = []
    for i, st in enumerate(states):
        s3.append({**st, "x": st["x"] + 0.5 * dt * s2[i]["vx"], "y": st["y"] + 0.5 * dt * s2[i]["vy"],
                   "z": st["z"] + 0.5 * dt * s2[i]["vz"], "vx": s2[i]["vx"] + 0.5 * dt * a2[i]["ax"],
                   "vy": s2[i]["vy"] + 0.5 * dt * a2[i]["ay"], "vz": s2[i]["vz"] + 0.5 * dt * a2[i]["az"]})
    a3 = accel(s3)
    s4 = []
    for i, st in enumerate(states):
        s4.append({**st, "x": st["x"] + dt * s3[i]["vx"], "y": st["y"] + dt * s3[i]["vy"],
                   "z": st["z"] + dt * s3[i]["vz"], "vx": s3[i]["vx"] + dt * a3[i]["ax"],
                   "vy": s3[i]["vy"] + dt * a3[i]["ay"], "vz": s3[i]["vz"] + dt * a3[i]["az"]})
    a4 = accel(s4)

    out = []
    for i, st in enumerate(states):
        out.append({
            "m": st["m"],
            "x": st["x"] + dt / 6 * (st["vx"] + 2 * s2[i]["vx"] + 2 * s3[i]["vx"] + s4[i]["vx"]),
            "y": st["y"] + dt / 6 * (st["vy"] + 2 * s2[i]["vy"] + 2 * s3[i]["vy"] + s4[i]["vy"]),
            "z": st["z"] + dt / 6 * (st["vz"] + 2 * s2[i]["vz"] + 2 * s3[i]["vz"] + s4[i]["vz"]),
            "vx": st["vx"] + dt / 6 * (a1[i]["ax"] + 2 * a2[i]["ax"] + 2 * a3[i]["ax"] + a4[i]["ax"]),
            "vy": st["vy"] + dt / 6 * (a1[i]["ay"] + 2 * a2[i]["ay"] + 2 * a3[i]["ay"] + a4[i]["ay"]),
            "vz": st["vz"] + dt / 6 * (a1[i]["az"] + 2 * a2[i]["az"] + 2 * a3[i]["az"] + a4[i]["az"]),
        })
    return out


def simulate_three_body(states, dt, steps):
    """Симуляция трёх тел: список позиций через каждый шаг."""
    cur = [dict(s) for s in states]
    history = [[(s["x"], s["y"], s["z"]) for s in cur]]
    for _ in range(steps):
        cur = three_body_step(cur, dt)
        history.append([(s["x"], s["y"], s["z"]) for s in cur])
    return history


def three_body_energy(states):
    """Полная энергия системы (кинетическая + потенциальная)."""
    ke = sum(0.5 * s["m"] * (s["vx"] ** 2 + s["vy"] ** 2 + s["vz"] ** 2) for s in states)
    pe = 0.0
    n = len(states)
    for i in range(n):
        for j in range(i + 1, n):
            dx = states[j]["x"] - states[i]["x"]
            dy = states[j]["y"] - states[i]["y"]
            dz = states[j]["z"] - states[i]["z"]
            r = math.sqrt(dx * dx + dy * dy + dz * dz)
            if r > 1e-12:
                pe -= G * states[i]["m"] * states[j]["m"] / r
    return ke + pe


if __name__ == "__main__":
    # Водород: серия Бальмера
    print("Бальмер (нм):", balmer_series(6))
    print("Лайман (нм):", lyman_series(4))
    print("Уровни энергии:", [hydrogen_level_energy(n) for n in range(1, 5)])

    # Три тела: Солнце-Земля-Луна (упрощённо)
    def body(m, x, y, vx=0.0, vy=0.0):
        return {"m": m, "x": x, "y": y, "z": 0.0, "vx": vx, "vy": vy, "vz": 0.0}

    s = [
        body(M_SUN, 0, 0),
        body(5.97e24, AU, 0, 0, 29780),   # Земля
        body(7.34e22, AU + 3.84e8, 0, 29780, 1020),  # Луна
    ]
    hist = simulate_three_body(s, dt=3600 * 24 * 3, steps=10)
    print("Три тела: 10 шагов по 3 дня, позиция Земли x:", round(hist[-1][1][0] / 1e9, 3), "e9 м")
    print("Энергия системы:", round(three_body_energy(s) / 1e30, 3), "e30 Дж")