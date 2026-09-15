# -*- coding: utf-8 -*-
"""Check size of RU Wikipedia section and LMSYS - what we can actually store."""
import json, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/1.0"

def get_files(ds, prefix=""):
    try:
        req = urllib.request.Request(f"https://huggingface.co/api/datasets/{ds}", headers={"User-Agent": UA})
        d = json.loads(urllib.request.urlopen(req, timeout=15).read())
        files = [s.get("rfilename", "") for s in d.get("siblings", [])]
        if prefix:
            files = [f for f in files if f.startswith(prefix)]
        return files
    except Exception as e:
        print(f"  ERR {e}")
        return []

def file_size(ds, fname):
    try:
        # HEAD request для размера
        url = f"https://huggingface.co/datasets/{ds}/resolve/main/{fname}"
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return int(resp.headers.get("Content-Length", 0))
    except Exception as e:
        return 0

print("=" * 60)
print("  РАЗМЕРЫ ДЛЯ 30-40 МЛН ПРИМЕРОВ")
print("=" * 60)

# 1. Wikipedia RU - весь раздел
print("\n[1] Wikipedia RU (20231101.ru):")
ru_files = get_files("wikimedia/wikipedia", "20231101.ru/train-")
print(f"  файлов: {len(ru_files)}")
total = 0
for f in ru_files[:27]:
    sz = file_size("wikimedia/wikipedia", f)
    total += sz
# если не все 27 - показать пример
print(f"  ~{total/1e9:.2f} GB (первые {min(27, len(ru_files))} файлов из {len(ru_files)})")
print(f"  пример файла: {ru_files[0] if ru_files else '?'}")

# 2. LMSYS Chat 1M
print("\n[2] LMSYS Chat 1M:")
lm_files = get_files("lmsys/lmsys-chat-1m", "data/train-")
print(f"  файлов: {len(lm_files)}")
total_lm = 0
for f in lm_files[:6]:
    total_lm += file_size("lmsys/lmsys-chat-1m", f)
print(f"  ~{total_lm/1e9:.2f} GB")
print(f"  пример: {lm_files[0] if lm_files else '?'}")

# 3. Диск
import shutil
total_gb, used_gb, free_gb = shutil.disk_usage("D:\\")
print(f"\n[3] Диск D: свободно {free_gb/1e9:.0f} GB")
print(f"    Можно хранить ~{free_gb/1e9 - 10:.0f} GB данных")

# 4. Что поместится
print("\n" + "=" * 60)
print("  ПЛАН 30-40 МЛН ПРИМЕРОВ")
print("=" * 60)
print(f"  Wikipedia RU: ~{len(ru_files)} файлов ≈ {total/1e9:.1f} GB (5-10 млн статей)")
print(f"  LMSYS Chat 1M: ~1 млн диалогов ≈ {total_lm/1e9:.2f} GB")
print(f"  Math 200k + Design 6.6k + RU 650k + Code 20k + Dolly 30k ≈ 1 млн")
print(f"  RefinedWeb sample: можно добрать ещё 10-30 млн за {free_gb/1e9:.0f} GB")
print(f"  При 3-6 тыс примеров/МБ → 30 млн ≈ 5-10 GB jsonl")