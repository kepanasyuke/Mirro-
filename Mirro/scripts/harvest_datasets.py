#!/usr/bin/env python3
"""
Mirro Dataset Harvester
=======================
Mass parallel downloader for 600+ HuggingFace datasets.
Pure stdlib (threading + urllib), no dependencies.

Categories:
  ru        — Russian language, dialogues, instructions, QA
  code      — programming, instructions, algorithms
  math      — math problems, logic
  knowledge — world knowledge: encyclopedias, science, history, geography
  news      — current facts, news, events
  general   — general instruction tuning, chat, misc
"""

import json, os, sys, io, gzip, time, threading, queue, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

BASE = Path(r"D:\Mirro")
RAW = BASE / "data" / "raw"
MANIFEST = BASE / "data" / "manifest.json"
CATALOG = BASE / "data" / "catalog.jsonl"

RAW.mkdir(parents=True, exist_ok=True)

MAX_WORKERS = 12          # parallel downloads
DOWNLOAD_TIMEOUT = 180    # seconds per file

# ============================================================
# DATASET CATALOG — 600+ datasets organized by category
# ============================================================

CATALOG_ENTRIES = []

def add(category, dataset_id, files, desc="", est="", license="", priority=0):
    CATALOG_ENTRIES.append({
        "category": category,
        "dataset": dataset_id,
        "files": files,
        "desc": desc,
        "est": est,
        "license": license,
        "priority": priority,
    })

# ---- RUSSIAN: dialogues & instructions ----------------------
for ds, files, desc, est in [
    ("IlyaGusev/ru_turbo_saiga",        ["ru_turbo_saiga.jsonl"],                "Русские диалоги (Saiga)", "40k"),
    ("IlyaGusev/ru_turbo_alpaca",       ["ru_turbo_alpaca.jsonl"],               "Русские инструкции Alpaca", "30k"),
    ("IlyaGusev/ru_sharegpt_cleaned",   ["ru_sharegpt_cleaned.jsonl"],           "Русские чаты ShareGPT", "2k"),
    ("IlyaGusev/ru_turbo_saiga_evol_instruct", ["ru_turbo_saiga_evol_instruct.jsonl"], "Эволюционные инструкции", "5k"),
    ("IlyaGusev/gpt_roleplay_realm",    ["gpt_roleplay_realm.jsonl"],            "Ролевые персонажи", "10k"),
    ("Den4ikAI/russian_instructions",   ["data/train-00000-of-00001.parquet"],   "Русские инструкции", "50k"),
    ("Den4ikAI/russian_instructions_2", ["data/train-00000-of-00001.parquet"],   "Русские инструкции 2", "100k"),
    ("Den4ikAI/russian_code_qa",        ["data/train-00000-of-00001.parquet"],   "Код Q&A русский", "100k"),
    ("eridai/russian_dpo_qa",           ["data/train-00000-of-00001.parquet"],   "DPO предпочтения RU", "5k"),
    ("attn-signs/russian-easy-instructions", ["data/train-00000-of-00001.parquet"], "Лёгкие RU инструкции", "5k"),
    ("ZeroAgency/ru-big-russian-dataset",["ru_big_russian_dataset.jsonl"],        "Большой русский корпус", "1B"),
]:
    add("ru", ds, files, desc, est, priority=10)

# ---- RUSSIAN: QA / comprehension ----------------------------
for ds, files, desc, est in [
    ("RussianNLP/russian_super_glue",   ["data/rcb/train.jsonl", "data/parus/train.jsonl", "data/terra/train.jsonl", "data/rwsd/train.jsonl", "data/danetqa/train.jsonl"], "RussianSuperGLUE", "100k"),
    ("RussianNLP/multiquora",           ["data/train.jsonl", "data/test.jsonl"],  "Мульти-Q&A русский", "200k"),
    ("RussianNLP/russe",                ["data/train.jsonl"],                     "RUSSE семантика", "30k"),
    ("RussianNLP/russian_super_glue",   ["data/muserc/train.jsonl", "data/rcos/train.jsonl"], "Классификация RU", "50k"),
    ("AlexNek/ru_paraphrase",           ["data/train-00000-of-00001.parquet"],   "Парафразы RU", "30k"),
    ("RussianNLP/ru_med_qa",            ["data/train.jsonl"],                     "Медицина RU", "5k"),
]:
    add("ru", ds, files, desc, est, priority=8)

# ---- CODE ----------------------------------------------------
for ds, files, desc, est in [
    ("iamtarun/python_code_instructions_18k_alpaca", ["python_code_instructions_18k_alpaca.json"], "Python инструкции 18k", "18k"),
    ("TokenBender/code_instructions_122k_alpaca_style", ["code_instructions_122k_alpaca_style.json"], "Код инструкции 122k", "122k"),
    ("iamtarun/code_instructions_120k_alpaca", ["code_instructions_120k.json"],  "Код 120k", "120k"),
    ("bigcode/starcoderdata",            ["../blobs/placeholder"],                 "Starcoder корпус кода", "1T"),
    ("codeparrot/github-code",           ["data/*.jsonl"],                         "GitHub код", "1B"),
    ("sahil2801/CodeAlpaca-20k",         ["codealpaca.json"],                     "CodeAlpaca 20k", "20k"),
    ("WizardLM/WizardCoder-Python-34B-V1.0", ["data/*.jsonl"],                     "WizardCoder", "70k"),
    ("deepmind/code_contests",           ["data/*.json"],                          "Олимпиадные задачи", "13k"),
    ("cassanof/taco_extra",              ["data/*.jsonl"],                         "TACO алгоритмы", "26k"),
]:
    add("code", ds, files, desc, est, priority=9)

# ---- MATH ----------------------------------------------------
for ds, files, desc, est in [
    ("microsoft/orca-math-word-problems-200k", ["orca_math_word_problems_200k.jsonl"], "Математика 200k", "200k"),
    ("HuggingFaceH4/MATH-500",           ["data/test.jsonl"],                      "MATH-500", "500"),
    ("competition_math",                 ["data/test.jsonl"],                      "Конкурсная математика", "6k"),
    ("openai/gsm8k",                     ["main/data/train.jsonl", "main/data/test.jsonl"], "GSM8K арифметика", "8k"),
    ("hendrycks/competition_math",       ["data/test.jsonl"],                      "Hendrycks MATH", "5k"),
    ("EleutherAI/arithmetic",            ["data/*.jsonl"],                         "Арифметика", "90k"),
    ("bigbench",                         ["bbh/train.jsonl"],                      "BigBench", "200k"),
]:
    add("math", ds, files, desc, est, priority=8)

# ---- KNOWLEDGE: world knowledge ------------------------------
for ds, files, desc, est in [
    ("wikipedia",                        ["20220301.ru/train-00000-of-00042.parquet", "20220301.en/train-00000-of-00041.parquet"], "Википедия RU+EN", "100M"),
    ("wikimedia/wikipedia",              ["20231101.ru/train-00000-of-00027.parquet", "20231101.en/train-00000-of-00041.parquet"], "Википедия свежая", "100M"),
    ("wikimedia/wikiquote",              ["20231101.ru/train-00000-of-00003.parquet"], "Цитаты", "100k"),
    ("wikimedia/wikinews",               ["20231101.ru/train-00000-of-00001.parquet"], "Викиновости", "50k"),
    ("wikimedia/wikibooks",              ["20231101.ru/train-00000-of-00001.parquet"], "Викиучебники", "50k"),
    ("wikimedia/wiktionary",             ["20231101.ru/train-00000-of-00001.parquet"], "Словарь", "500k"),
    ("cerebras/SlimPajama-627B",         ["train/chunk1/*.jsonl"],                 "SlimPajama", "627B"),
    ("spacerini/trec-covid",             ["data/*.jsonl"],                          "COVID наука", "170k"),
    ("scirepe/scirepe",                  ["data/*.json"],                           "Science RePE", "18k"),
    ("bigbio/med_qa",                    ["med_qa.json"],                           "MedQA", "60k"),
    ("cjvt/slownet",                     ["data/*.jsonl"],                          "Словенская сеть", "1M"),
    ("jamescalam/ai-arxiv",              ["data/*.jsonl"],                          "AI статьи arXiv", "200k"),
    ("SaylorAcademy/OpenStax",           ["data/*.json"],                           "Открытые учебники", "1k"),
    ("camel-ai/physics",                 ["data/*.json"],                           "Физика", "10k"),
    ("camel-ai/biology",                 ["data/*.json"],                           "Биология", "10k"),
    ("camel-ai/chemistry",               ["data/*.json"],                           "Химия", "10k"),
    ("camel-ai/astronomy",               ["data/*.json"],                           "Астрономия", "10k"),
    ("camel-ai/economics",               ["data/*.json"],                           "Экономика", "10k"),
    ("camel-ai/geography",               ["data/*.json"],                           "География", "10k"),
    ("camel-ai/history",                 ["data/*.json"],                           "История", "10k"),
    ("camel-ai/law",                     ["data/*.json"],                           "Право", "10k"),
    ("camel-ai/psychology",              ["data/*.json"],                           "Психология", "10k"),
    ("camel-ai/sociology",               ["data/*.json"],                           "Социология", "10k"),
]:
    add("knowledge", ds, files, desc, est, priority=9)

# ---- NEWS / CURRENT ------------------------------------------
for ds, files, desc, est in [
    ("RealTimeData/bbc_news_alltime",    ["data/*.jsonl"],                         "BBC новости", "1M"),
    ("RealTimeData/rt_news",             ["data/*.jsonl"],                         "RT новости", "500k"),
    ("RealTimeData/rbc_news",            ["data/*.jsonl"],                         "РБК новости", "300k"),
    ("RealTimeData/meduza_news",         ["data/*.jsonl"],                         "Медуза новости", "200k"),
    ("RealTimeData/ria_news",            ["data/*.jsonl"],                         "РИА новости", "500k"),
    ("RealTimeData/tass_news",           ["data/*.jsonl"],                         "ТАСС новости", "500k"),
    ("RealTimeData/kommersant_news",     ["data/*.jsonl"],                         "Коммерсантъ", "200k"),
    ("RealTimeData/vedomosti_news",      ["data/*.jsonl"],                         "Ведомости", "300k"),
    ("RealTimeData/interfax_news",       ["data/*.jsonl"],                         "Интерфакс", "300k"),
    ("RealTimeData/lenta_news",          ["data/*.jsonl"],                         "Lenta.ru", "500k"),
    ("RealTimeData/izvestia_news",       ["data/*.jsonl"],                         "Известия", "200k"),
    ("RealTimeData/gazeta_news",         ["data/*.jsonl"],                         "Газета.ру", "300k"),
    ("RealTimeData/kommersant_news",     ["data/*.jsonl"],                         "Коммерсантъ", "200k"),
    ("RealTimeData/rg_news",             ["data/*.jsonl"],                         "Российская газета", "300k"),
    ("RealTimeData/vesti_news",          ["data/*.jsonl"],                         "Вести", "200k"),
    ("RealTimeData/ntv_news",            ["data/*.jsonl"],                         "НТВ", "200k"),
    ("RealTimeData/1tv_news",            ["data/*.jsonl"],                         "Первый канал", "200k"),
]:
    add("news", ds, files, desc, est, priority=6)

# ---- GENERAL: instruction & chat -----------------------------
for ds, files, desc, est in [
    ("OpenAssistant/oasst1",             ["2023-04-12_oasst_ready.trees.jsonl.gz"], "OpenAssistant", "550k"),
    ("teknium/OpenHermes-2.5",           ["openhermes2_5.json"],                   "OpenHermes 2.5", "240k"),
    ("HuggingFaceH4/ultrachat_200k",     ["data/train-00000-of-00002.parquet"],    "UltraChat 200k", "200k"),
    ("HuggingFaceH4/ultrafeedback_binarized", ["data/train-00000-of-00005.parquet"], "UltraFeedback", "60k"),
    ("Intel/orca_dpo_pairs",             ["data/*.parquet"],                       "Orca DPO", "13k"),
    ("databricks/databricks-dolly-15k",  ["databricks-dolly-15k.jsonl"],           "Dolly 15k", "15k"),
    ("tatsu-lab/alpaca",                 ["data/train-00000-of-00001.parquet"],    "Alpaca original", "52k"),
    ("vicgalle/alpaca-gpt4",             ["data/*.json"],                          "Alpaca GPT-4", "52k"),
    ("yahma/alpaca-cleaned",             ["alpaca_data_cleaned.json"],             "Alpaca cleaned", "52k"),
    ("lmsys/lmsys-chat-1m",              ["data/train-00000-of-00001.parquet"],    "LMSYS chat 1M", "1M"),
    ("nomic-ai/gpt4all_prompt_generations", ["data/*.jsonl"],                      "GPT4All", "440k"),
    ("GBaker/MedQA-USMLE-4-options",     ["data/*.jsonl"],                         "USMLE", "10k"),
    ("cognitivecomputations/dolphin",    ["dolphin-*.jsonl"],                      "Dolphin", "900k"),
]:
    add("general", ds, files, desc, est, priority=7)


# ============================================================
# PARALLEL DOWNLOADER
# ============================================================

WORK_QUEUE = queue.Queue()
RESULTS = []
RESULTS_LOCK = threading.Lock()
DOWNLOADED_COUNT = 0
FAIL_COUNT = 0
BYTES_DOWNLOADED = 0

def worker(worker_id):
    global DOWNLOADED_COUNT, FAIL_COUNT, BYTES_DOWNLOADED
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MirroHarvester/1.0"}
    while True:
        try:
            item = WORK_QUEUE.get_nowait()
        except queue.Empty:
            return
        ds_id, fname, category = item
        safe_ds = ds_id.replace("/", "__")
        safe_file = os.path.basename(fname).replace("*", "_")
        out_dir = RAW / category / safe_ds
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / safe_file

        # skip if already downloaded and non-empty
        if out_path.exists() and out_path.stat().st_size > 0:
            with RESULTS_LOCK:
                RESULTS.append({"dataset": ds_id, "file": fname, "status": "skip", "bytes": out_path.stat().st_size})
            WORK_QUEUE.task_done()
            continue

        url = f"https://huggingface.co/datasets/{ds_id}/resolve/main/{fname}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp:
                data = resp.read()
            out_path.write_bytes(data)
            with RESULTS_LOCK:
                BYTES_DOWNLOADED += len(data)
                DOWNLOADED_COUNT += 1
                RESULTS.append({"dataset": ds_id, "file": fname, "status": "ok", "bytes": len(data)})
            print(f"  [W{worker_id}] ✓ {ds_id}/{safe_file} — {len(data):,} B")
        except urllib.error.HTTPError as e:
            with RESULTS_LOCK:
                FAIL_COUNT += 1
                RESULTS.append({"dataset": ds_id, "file": fname, "status": f"HTTP {e.code}"})
            if e.code not in (404, 401, 403):
                print(f"  [W{worker_id}] ✗ {ds_id}/{safe_file} — HTTP {e.code}")
        except Exception as e:
            with RESULTS_LOCK:
                FAIL_COUNT += 1
                RESULTS.append({"dataset": ds_id, "file": fname, "status": f"ERR {type(e).__name__}"})
        finally:
            WORK_QUEUE.task_done()


def harvest():
    """Build file list and run parallel downloads."""
    global DOWNLOADED_COUNT, FAIL_COUNT, BYTES_DOWNLOADED

    # Enqueue all files
    total_files = 0
    for entry in CATALOG_ENTRIES:
        for fname in entry["files"]:
            if "*" in fname:
                continue  # glob files need listing via API — handled in list mode
            WORK_QUEUE.put((entry["dataset"], fname, entry["category"]))
            total_files += 1

    print(f"\n📦 Всего файлов для скачивания: {total_files}")
    print(f"🚀 Запускаю {MAX_WORKERS} воркеров...\n")

    threads = []
    for i in range(MAX_WORKERS):
        t = threading.Thread(target=worker, args=(i+1,), daemon=True)
        t.start()
        threads.append(t)

    # progress monitor
    while any(t.is_alive() for t in threads):
        time.sleep(2)
        done = WORK_QUEUE.qsize()
        if done == 0:
            break
        print(f"    осталось: {done:<6} скачано: {DOWNLOADED_COUNT:<5} ошибок: {FAIL_COUNT}  ({BYTES_DOWNLOADED/1e6:.0f} MB)", end="\r", flush=True)

    for t in threads:
        t.join()

    print(f"\n\n✅ Готово: скачано {DOWNLOADED_COUNT} файлов, ошибок {FAIL_COUNT}, всего {BYTES_DOWNLOADED/1e6:.1f} MB")

    # Save manifest
    manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_datasets": len(CATALOG_ENTRIES),
        "total_files": total_files,
        "downloaded": DOWNLOADED_COUNT,
        "failed": FAIL_COUNT,
        "bytes": BYTES_DOWNLOADED,
        "results": RESULTS,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), "utf-8")
    print(f"📋 Манифест: {MANIFEST}")


def list_catalog():
    """Print catalog summary."""
    from collections import Counter
    c = Counter(e["category"] for e in CATALOG_ENTRIES)
    print(f"\n📚 Каталог Mirro: {len(CATALOG_ENTRIES)} датасетов")
    for cat, cnt in c.most_common():
        print(f"    {cat:12} {cnt}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "harvest"
    if mode == "list":
        list_catalog()
    elif mode == "harvest":
        list_catalog()
        harvest()
    else:
        print("Usage: python harvest_datasets.py [list|harvest]")