# -*- coding: utf-8 -*-
"""
Mirro Corpus Generator — генерация 30-40 млн примеров локально.
================================================================
Источники расширения:
  1. Парафразы существующих пар (RU 650k, math 200k, code 20k…)
  2. Морфология: подстановка словоформ («что такое X», «объясни X»)
  3. Математический генератор: уравнения + решения
  4. Шаблонные QA: определение/применение/примеры

Выход: потоковая запись в сегменты JSONL, по ~100k на файл.
Цель: 30-40 млн примеров, ~45-60 GB на диске.

Дизайн: НЕ загружаем всё в память, пишем сегменты по мере генерации.
"""
import json, random, re, math, time, sys
from pathlib import Path

SRC_PROC = Path(r"D:\Mirro\data\processed")     # исходные кластеры
OUT_DIR = Path(r"D:\Mirro\data\corpus_big")     # большой корпус
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =============== ПАРАФРАЗЫ/МОРФОЛОГИЯ ===============
PREFACES_RU = [
    "Расскажи", "Объясни", "Что такое", "Что означает", "Как понять",
    "Подробнее о", "Расскажи про", "Что известно о", "Дай определение",
    "Что из себя представляет", "Почему важно", "В чём суть",
]
MIDDLES = ["можно подробнее", "кратко", "простыми словами", "в двух словах"]
SUFFIXES = ["?", " пожалуйста", "? с примером", "? и объясни"]

def paraphrase(inst, count=3, rng=None):
    """Генерирует вариации вопроса."""
    r = rng or random
    variants = [inst]
    # удалить лишние вопросительные хвосты
    base = re.sub(r"\s*\?.*$", "", inst).strip()
    for _ in range(count - 1):
        pf = r.choice(PREFACES_RU)
        sf = r.choice(SUFFIXES)
        variants.append(f"{pf} {base}{sf}")
    return variants

# =============== МАТЕМАТИЧЕСКИЙ ГЕНЕРАТОР ===============
def gen_math(rng):
    """Генерирует {инструкция, ответ} с решением."""
    kind = rng.randint(0, 4)
    if kind == 0:  # сложение/вычитание
        a, b = rng.randint(1, 999), rng.randint(1, 999)
        op = rng.choice(["+", "-"])
        if op == "-" and b > a:
            a, b = b, a
        ans = a + b if op == "+" else a - b
        q = f"Сколько будет {a} {op} {b}?"
    elif kind == 1:  # умножение
        a, b = rng.randint(2, 30), rng.randint(2, 30)
        ans = a * b
        q = f"Сколько будет {a} × {b}?"
    elif kind == 2:  # уравнение x + a = b
        a = rng.randint(1, 100)
        b = rng.randint(a + 1, a + 200)
        x = b - a
        ans = x
        q = f"Реши уравнение: x + {a} = {b}. Чему равно x?"
    elif kind == 3:  # проценты
        p = rng.choice([10, 20, 25, 30, 50])
        v = rng.randint(100, 2000)
        ans = v * p // 100
        q = f"Сколько будет {p}% от {v}?"
    else:  # площадь прямоугольника
        a, b = rng.randint(2, 50), rng.randint(2, 50)
        ans = a * b
        q = f"Найди площадь прямоугольника со сторонами {a} и {b}."
    a_text = f"{ans}"
    return {"instruction": q, "input": "", "output": a_text}

# =============== ШАБЛОННЫЕ QA ИЗ СУЩЕСТВУЮЩИХ ПАР ===============
def load_base_examples(limit_each=6000):
    """Загружает выборку исходных пар для шаблонной генерации."""
    base = []
    for f in sorted(SRC_PROC.glob("*.jsonl")):
        n = 0
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                if len(base) >= limit_each * 6:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    ex = json.loads(line)
                    if ex.get("instruction") and ex.get("output"):
                        base.append(ex)
                        n += 1
                        if n >= limit_each:
                            break
                except Exception:
                    pass
    print(f"  база для шаблонов: {len(base)} пар")
    return base

def gen_from_base(base, rng):
    """Из базы генерирует компактные QA с переформулировкой."""
    ex = rng.choice(base)
    inst = ex.get("instruction", "")
    out = ex.get("output", "")
    if not inst or not out:
        return None
    # переформулируем вопрос и чуть обрежем ответ
    q_variants = paraphrase(inst, count=2, rng=rng)
    q = rng.choice(q_variants)
    a = out[:1200]
    return {"instruction": q[:600], "input": "", "output": a}

# =============== ГЛАВНЫЙ ЦИКЛ ===============
def main():
    target_million = int(sys.argv[1]) if len(sys.argv) > 1 else 34
    target = target_million * 1_000_000
    print(f"Цель: {target_million} млн примеров")
    print(f"Папка: {OUT_DIR}")
    print()

    # база для шаблонов (загрузим выборку)
    base = load_base_examples()

    rng = random.Random(42)  # воспроизводимость

    # гендерный микс:
    #  - парафразы базы ~60%
    #  - математика ~25%
    #  - прочее 15%
    written = 0
    t0 = time.time()
    buf = []
    SEEN = set()              # дедупликация на уровне первых 60 символов инструкции
    total_bytes = 0           # аккумулятор записанных байт

    def flush():
        """Записывает буфер в текущий сегмент-файл (200k примеров на файл)."""
        nonlocal total_bytes
        if not buf:
            return 0
        fname = OUT_DIR / f"corpus-{written // per_file:06d}.jsonl"
        with open(fname, "a", encoding="utf-8") as f:
            for entry in buf:
                line = json.dumps(entry, ensure_ascii=False) + "\n"
                f.write(line)
                total_bytes += len(line.encode("utf-8"))
        n = len(buf)
        buf.clear()
        return n

    # запускаем потоковую генерацию
    per_file = 200_000        # сегменты по 200k (≈300 MB каждый)
    batch_size = 100_000
    while written < target:
        entry = None
        roll = rng.random()
        if roll < 0.60 and base:
            entry = gen_from_base(base, rng)
        elif roll < 0.85:
            entry = gen_math(rng)
        else:
            # шаблонные определения
            entry = gen_from_base(base, rng) if base else gen_math(rng)

        if entry is None:
            continue

        # дедуп по началу вопроса (не храним все - только кэш последних)
        key = entry["instruction"][:50].lower()
        if key in SEEN:
            continue
        if len(SEEN) > 2_000_000:
            SEEN.clear()
        SEEN.add(key)

        buf.append(entry)
        written += 1

        if written % batch_size == 0:
            flush()
            speed = written / (time.time() - t0)
            print(f"  {written/1e6:.1f}M примеров, {speed:.0f}/с, "
                  f"диск {total_bytes/1e9:.1f} GB")

    flush()
    elapsed = time.time() - t0
    print(f"\n\nГотово: {written} примеров за {elapsed/60:.1f} мин")
    print(f"Объём: {total_bytes/1e9:.1f} GB")
    print(f"Файлов: {len(list(OUT_DIR.glob('*.jsonl')))}")

if __name__ == "__main__":
    main()