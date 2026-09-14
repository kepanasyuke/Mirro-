# -*- coding: utf-8 -*-
"""
Скачивание Wikipedia RU (все 21 файл parquet).
Потом конвертация: текст статьи -> entries.
"""
import urllib.request, json, os, time
from pathlib import Path

DS = "wikimedia/wikipedia"
PREFIX = "20231101.ru/train-"
DEST = Path(r"D:\Mirro\data\raw\wikipedia_ru")
DEST.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/1.0"

def list_files():
    req = urllib.request.Request(f"https://huggingface.co/api/datasets/{DS}", headers={"User-Agent": UA})
    d = json.loads(urllib.request.urlopen(req, timeout=15).read())
    files = [s.get("rfilename", "") for s in d.get("siblings", [])]
    return [f for f in files if f.startswith(PREFIX) and f.endswith(".parquet")]

def download_one(fname):
    url = f"https://huggingface.co/datasets/{DS}/resolve/main/{fname}"
    out = DEST / os.path.basename(fname)
    if out.exists() and out.stat().st_size > 0:
        return out
    # Stream download
    print(f"  ↓ {fname} ...", end="", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as resp:
        size = 0
        with open(out, "wb") as f:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                size += len(chunk)
    print(f" {size/1e6:.1f} MB")
    return out

def main():
    files = list_files()
    print(f"Найдено файлов: {len(files)}")
    downloaded = 0
    for f in files:
        try:
            download_one(f)
            downloaded += 1
        except Exception as e:
            print(f"  ! {f}: {str(e)[:60]}")
        time.sleep(0.3)
    print(f"\nГотово: {downloaded}/{len(files)} файлов")
    total = sum(p.stat().st_size for p in DEST.glob("*.parquet"))
    print(f"Всего: {total/1e9:.2f} GB")

if __name__ == "__main__":
    main()