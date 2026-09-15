# -*- coding: utf-8 -*-
"""
Надёжный чанкованный загрузчик HuggingFace.
- Запросы по Range (продолжение с места обрыва)
- Параллельные сегменты (4 потока)
- Таймауты и retry на каждый сегмент
- Идёт быстро даже на нестабильной сети
"""
import os, sys, threading, time, urllib.request, json, signal
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/1.0"
CHUNK = 8 * 1024 * 1024   # 8 MB на сегмент
NUM_THREADS = 6
RETRIES = 5

def get_size(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": "bytes=0-0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            total = int(resp.headers.get("Content-Range", "/0").split("/")[-1])
            return total
    except Exception as e:
        print(f"  ! get_size: {e}")
        return None

def download_range(url, out_path, start, end, idx, status):
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Range": f"bytes={start}-{end}",
            })
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            with open(out_path, "r+b") as f:
                f.seek(start)
                f.write(data)
            status[idx] = end - start + 1
            return True
        except Exception as e:
            if attempt == RETRIES - 1:
                print(f"  ! сегмент {idx} http {start}-{end}: {e}")
                return False
            time.sleep(2 + attempt * 2)
    return False

def download_chunked(url, out_path):
    """Скачивает файл чанками с продолжением и параллелью."""
    out_path = Path(out_path)
    total = get_size(url)
    if total is None or total <= 0:
        print(f"  ! не удалось узнать размер, файл: {url.split('/')[-1]}")
        return False

    # сколько уже скачано
    have = out_path.stat().st_size if out_path.exists() else 0
    if have >= total:
        print(f"  = уже есть {out_path.name} ({have/1e6:.0f} MB)")
        return True

    if have == 0:
        # создать файл нужного размера
        with open(out_path, "wb") as f:
            f.truncate(total)
    else:
        print(f"  = продолжение: {have/1e6:.0f}/{total/1e6:.0f} MB")

    # cегменты
    segments = []
    for start in range(have, total, CHUNK):
        end = min(start + CHUNK - 1, total - 1)
        segments.append((start, end))

    print(f"  ↓ {url.split('/')[-1]}: {total/1e6:.0f} MB, сегментов {len(segments)} ({NUM_THREADS} потоков)")

    status = [0] * len(segments)
    t0 = time.time()
    for i in range(0, len(segments), NUM_THREADS):
        batch = segments[i:i + NUM_THREADS]
        threads = []
        for j, (s, e) in enumerate(batch):
            idx = i + j
            th = threading.Thread(target=download_range, args=(url, out_path, s, e, idx, status), daemon=True)
            th.start()
            threads.append(th)
        for th in threads:
            th.join()

    # Проверка
    downloaded = sum(status)
    ok = downloaded >= (total - 1 - have) * 0.99
    if ok:
        print(f"  ✓ {out_path.name}: {total/1e6:.0f} MB за {time.time()-t0:.0f}с")
    else:
        print(f"  ! неполный: {downloaded/1e6:.0f}/{total/1e6:.0f} MB (повтори запуск — продолжит)")
    return ok

def main():
    # Получить список файлов
    ds = "wikimedia/wikipedia"
    req = urllib.request.Request(f"https://huggingface.co/api/datasets/{ds}", headers={"User-Agent": UA})
    d = json.loads(urllib.request.urlopen(req, timeout=20).read())
    files = [s.get("rfilename", "") for s in d.get("siblings", [])]
    files = [f for f in files if f.startswith("20231101.ru/train-") and f.endswith(".parquet")]

    dest = Path(r"D:\Mirro\data\raw\wikipedia_ru")
    dest.mkdir(parents=True, exist_ok=True)

    print(f"Файлов: {len(files)}")
    done = 0
    for f in files:
        url = f"https://huggingface.co/datasets/{ds}/resolve/main/{f}"
        ok = download_chunked(url, dest / os.path.basename(f))
        if ok:
            done += 1
    print(f"\nГотово: {done}/{len(files)} файлов")
    total = sum(p.stat().st_size for p in dest.glob("*.parquet"))
    print(f"Всего скачано: {total/1e9:.2f} GB")

if __name__ == "__main__":
    main()