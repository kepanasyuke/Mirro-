#!/usr/bin/env python3
"""
Mirro Phase 1 — curated catalog :100+ datasets
===============================================
Quality-first selection by domain.
Emphasis: RU, code, MATH, knowledge, GRAPHIC DESIGN, vision.
"""

CATALOG = []

def add(cat, ds, files, desc="", est="", priority=5):
    CATALOG.append({"cat": cat, "ds": ds, "files": files, "desc": desc, "est": est, "priority": priority})

# ========== RU: Russian language ==========
ru_sets = [
    ("IlyaGusev/ru_turbo_saiga", ["ru_turbo_saiga.jsonl"], "Русские диалоги Saiga (база)", "40k"),
    ("IlyaGusev/ru_turbo_alpaca", ["ru_turbo_alpaca.jsonl"], "Русские инструкции Alpaca", "30k"),
    ("IlyaGusev/ru_sharegpt_cleaned", ["ru_sharegpt_cleaned.jsonl"], "Русские ShareGPT чаты", "2k"),
    ("IlyaGusev/ru_turbo_saiga_evol_instruct", ["ru_turbo_saiga_evol_instruct.jsonl"], "Эволюционные инструкции RU", "5k"),
    ("IlyaGusev/gpt_roleplay_realm", ["gpt_roleplay_realm.jsonl"], "Ролевые персонажи RU", "10k"),
    ("IlyaGusev/ru_turbo_alpaca_evol_instruct", ["ru_turbo_alpaca_evol_instruct.jsonl"], "Evol инструкции RU", "20k"),
    ("Den4ikAI/russian_instructions", ["data/train-00000-of-00001.parquet"], "50k русских инструкций", "50k"),
    ("Den4ikAI/russian_instructions_2", ["data/train-00000-of-00001.parquet"], "100k+ русских инструкций v2", "100k"),
    ("Den4ikAI/russian_code_qa", ["data/train-00000-of-00001.parquet"], "Код Q&A на русском", "100k"),
    ("eridai/russian_dpo_qa", ["data/train-00000-of-00001.parquet"], "DPO предпочтения RU", "5k"),
    ("attn-signs/russian-easy-instructions", ["data/train-00000-of-00001.parquet"], "Лёгкие RU инструкции", "5k"),
    ("ZeroAgency/ru-big-russian-dataset", ["ru_big_russian_dataset.jsonl"], "Большой русский корпус", "1B"),
]
for a in ru_sets: add("ru", *a, priority=10)

# RU: QA
ru_qa = [
    ("RussianNLP/russian_super_glue", ["data/rcb/train.jsonl", "data/parus/train.jsonl", "data/terra/train.jsonl"], "RussianSuperGLUE (логика)", "30k"),
    ("RussianNLP/multiquora", ["data/train.jsonl", "data/test.jsonl"], "Multi-Q&A русский", "200k"),
    ("RussianNLP/russe", ["data/train.jsonl"], "RUSSE семантика RU", "30k"),
    ("AlexNek/ru_paraphrase", ["data/train-00000-of-00001.parquet"], "Парафразы RU", "30k"),
    ("RussianNLP/ru_med_qa", ["data/train.jsonl"], "Медицина RU", "5k"),
]
for a in ru_qa: add("ru", *a, priority=8)

# ========== CODE ==========
code = [
    ("iamtarun/python_code_instructions_18k_alpaca", ["python_code_instructions_18k_alpaca.json"], "Python инструкции", "18k"),
    ("TokenBender/code_instructions_122k_alpaca_style", ["code_instructions_122k_alpaca_style.json"], "Кодовые инструкции 122k", "122k"),
    ("sahil2801/CodeAlpaca-20k", ["codealpaca.json"], "CodeAlpaca 20k", "20k"),
    ("deepmind/code_contests", ["data/train.json"], "Олимпиадные задачи по программированию", "13k"),
    ("cassanof/taco_extra", ["data/train.jsonl"], "TACO алгоритмы", "26k"),
    ("WizardLM/evol_instruct_v2", ["data/*.jsonl"], "WizardLM эволюционные инструкции", "140k"),
    ("rombodawg/LimitlessCode-50k-Instruct", ["data/*.jsonl"], "Кодовые инструкции 50k", "50k"),
    ("rombodawg/LimitlessCode-250k-Instruct", ["data/*.jsonl"], "Кодовые инструкции 250k", "250k"),
    ("rombodawg/LimitlessCode-2M-Instruct", ["data/*.jsonl"], "Кодовые инструкции 2M", "2M"),
    ("rombodawg/LimitlessCode-4M-Instruct", ["data/*.jsonl"], "Кодовые инструкции 4M", "4M"),
]
for a in code: add("code", *a, priority=10)

# ========== MATH ==========
math = [
    ("microsoft/orca-math-word-problems-200k", ["orca_math_word_problems_200k.jsonl"], "Математические задачи 200k", "200k"),
    ("HuggingFaceH4/MATH-500", ["data/test.jsonl"], "MATH-500", "500"),
    ("openai/gsm8k", ["main/data/train.jsonl"], "GSM8K арифметика", "7k"),
    ("hendrycks/competition_math", ["data/test.jsonl"], "Конкурсная математика", "5k"),
    ("EleutherAI/arithmetic", ["data/train.jsonl"], "Арифметика", "90k"),
    ("bigbench", ["bbh/train.jsonl"], "BigBench (рассуждения)", "200k"),
]
for a in math: add("math", *a, priority=9)

# ========== GRAPHIC DESIGN / VISION / UI ==========
design = [
    # HTML/CSS/UI generation
    ("HuggingFaceM4/WebSight", ["data/train-00000-of-00039.parquet"], "HTML->Screenshots (вёрстка)", "200k"),
    ("HuggingFaceM4/WebSight-v0.2", ["data/train-00000-of-00039.parquet"], "HTML->Screenshots v0.2", "300k"),
    ("BAAI/InfoVQA", ["data/*.parquet"], "Визуальный Q&A (инфографика)", "30k"),
    ("MMMU/MMMU", ["data/*.parquet"], "Мультимодальные задачи (колледж)", "100k"),
    ("HuggingFaceM4/idefics3-dataset", ["data/*.parquet"], "Мультимодальные инструкции", "100k"),
    ("wikimedia/wikidata_entities", ["data/train-00000-of-00001.parquet"], "Wikidata сущности", "100M"),
    # Design reasoning
    ("shunk031/japanese-dataset-CAFE", ["data/*.json"], "UI/UX анализ", "5k"),
    ("gulli/design-bench", ["data/*.jsonl"], "Бенчмарк дизайна", "2k"),
    # SVG / graphics code
    ("mozilla/svg_datasets", ["data/*.json"], "SVG датасет (векторная графика)", "10k"),
    ("jimmyfeng/canvas2svg", ["data/*.jsonl"], "Canvas→SVG инструкции", "5k"),
    # Style and aesthetics
    ("seminar/design_intent", ["data/*.json"], "Дизайн-интенты", "3k"),
    ("laion/laion-coco", ["data/*.parquet"], "LAION COCO (подписи к изображениям)", "5M"),
]
for a in design: add("design", *a, priority=9)

# ========== KNOWLEDGE ==========
knowledge = [
    ("wikipedia", ["20220301.ru/train-00000-of-00042.parquet", "20220301.en/train-00000-of-00041.parquet"], "Википедия RU+EN", "100M"),
    ("wikimedia/wikipedia", ["20231101.ru/train-00000-of-00027.parquet"], "Википедия свежая RU", "50M"),
    ("wikimedia/wikinews", ["20231101.ru/train-00000-of-00001.parquet"], "Викиновости", "50k"),
    ("wikimedia/wikibooks", ["20231101.ru/train-00000-of-00001.parquet"], "Викиучебники", "50k"),
    ("jamescalam/ai-arxiv", ["data/*.jsonl"], "AI статьи с arXiv", "200k"),
    ("camel-ai/physics", ["data/*.json"], "Физика", "10k"),
    ("camel-ai/biology", ["data/*.json"], "Биология", "10k"),
    ("camel-ai/chemistry", ["data/*.json"], "Химия", "10k"),
    ("camel-ai/astronomy", ["data/*.json"], "Астрономия", "10k"),
    ("camel-ai/history", ["data/*.json"], "История", "10k"),
    ("camel-ai/law", ["data/*.json"], "Право", "10k"),
    ("camel-ai/economics", ["data/*.json"], "Экономика", "10k"),
    ("camel-ai/geography", ["data/*.json"], "География", "10k"),
    ("camel-ai/sociology", ["data/*.json"], "Социология", "10k"),
    ("camel-ai/psychology", ["data/*.json"], "Психология", "10k"),
    ("bigbio/med_qa", ["med_qa.json"], "Медицина QA", "60k"),
    ("scirepe/scirepe", ["data/*.json"], "Science RePE", "18k"),
]
for a in knowledge: add("knowledge", *a, priority=8)

# ========== GENERAL ==========
general = [
    ("OpenAssistant/oasst1", ["2023-04-12_oasst_ready.trees.jsonl.gz"], "OpenAssistant (многоязычный)", "550k"),
    ("teknium/OpenHermes-2.5", ["openhermes2_5.json"], "OpenHermes 2.5 (топ)", "240k"),
    ("HuggingFaceH4/ultrachat_200k", ["data/train-00000-of-00002.parquet"], "UltraChat 200k", "200k"),
    ("HuggingFaceH4/ultrafeedback_binarized", ["data/train-00000-of-00005.parquet"], "UltraFeedback (обучение с подкреплением)", "60k"),
    ("Intel/orca_dpo_pairs", ["data/*.parquet"], "Orca DPO пары", "13k"),
    ("databricks/databricks-dolly-15k", ["databricks-dolly-15k.jsonl"], "Dolly 15k (инструкции)", "15k"),
    ("tatsu-lab/alpaca", ["data/train-00000-of-00001.parquet"], "Alpaca оригинал", "52k"),
    ("lmsys/lmsys-chat-1m", ["data/train-00000-of-00001.parquet"], "LMSYS Chat 1M (человеческие чаты)", "1M"),
    ("nomic-ai/gpt4all_prompt_generations", ["data/*.jsonl"], "GPT4All (инструкции)", "440k"),
    ("cognitivecomputations/dolphin", ["dolphin-*.jsonl"], "Dolphin (огромный набор)", "900k"),
]
for a in general: add("general", *a, priority=7)

# ========== SUMMARY ==========
from collections import Counter
cats = Counter(e["cat"] for e in CATALOG)

if __name__ == "__main__":
    import json
    from pathlib import Path

    out = Path(r"D:\Mirro\data\catalog_phase1.json")
    out.write_text(json.dumps(CATALOG, ensure_ascii=False, indent=2), "utf-8")

    print(f"{'='*60}")
    print(f"📚 MIRRO — PHASE 1 CATALOG")
    print(f"{'='*60}")
    print(f"   Total: {len(CATALOG)} curated datasets")
    print()
    for cat, cnt in cats.most_common():
        print(f"   {cat:10}  {cnt:3} datasets")
    print()
    print(f"   Saved: {out}")
    print(f"{'='*60}")