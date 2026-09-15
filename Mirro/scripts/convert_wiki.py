# -*- coding: utf-8 -*-
"""
Конвертер Wikipedia RU parquet -> компактные JSONL (для большого корпуса).
Не загружает всё в память: потоковая обработка по батчам.
Формат:
  {"instruction": "<заголовок статьи>", "input": "", "output": "<текст/введение>"}

Задача: из 21 файла ~4.9GB -> под-примеры (статья = 1+ примеры).
Для 30-40 млн общего пула нам не нужны все 8 млн статей целиком
каждый пример - возьмём заголовок->введение/первые абзацы.
"""
import io, json, sys, time
from pathlib import Path

RAW = Path(r"D:\Mirro\data\raw\wikipedia_ru")
OUT_DIR = Path(r"D:\Mirro\data\corpus_wiki")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def process_file(path, out, max_examples_per_file=None):
    import pyarrow.parquet as pq
    count = 0
    # потоковое чтение по батчам (row groups)
    pf = pq.ParquetFile(path)
    for i in range(pf.num_row_groups):
        table = pf.read_row_group(i)
        rows = table.to_pylist()
        for row in rows:
            title = row.get("title", "")
            text = row.get("text", "")
            if not title or not text:
                continue
            # Ограничим длину вывода, чтобы пример был компактным
            # Возьмём первые ~1200-2000 символов текста
            snippet = text[:2000].replace("\n", " ").strip()
            if len(snippet) < 40:
                continue
            entry = {
                "instruction": f"Расскажи: {title}",
                "input": "",
                "output": snippet,
            }
            out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            count += 1
            if max_examples_per_file and count >= max_examples_per_file:
                return count
    return count

def main():
    files = sorted(RAW.glob("*.parquet"))
    print(f"Файлов: {len(files)}")
    total = 0
    for f in files:
        out_path = OUT_DIR / (f.stem + ".jsonl")
        if out_path.exists() and out_path.stat().st_size > 0:
            n = sum(1 for _ in out_path.open(encoding="utf-8") if _.strip())
            print(f"  = {f.name}: уже {n}")
            total += n
            continue
        t0 = time.time()
        with open(out_path, "w", encoding="utf-8") as out:
            n = process_file(f, out)
        print(f"  {f.name}: +{n} за {time.time()-t0:.0f}s")
        total += n
    print(f"\nИтого: {total} примеров")
    print(f"Размер: {sum(p.stat().st_size for p in OUT_DIR.glob('*.jsonl'))/1e9:.2f} GB")

if __name__ == "__main__":
    main()