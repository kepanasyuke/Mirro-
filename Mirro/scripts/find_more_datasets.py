#!/usr/bin/env python3
"""Find downloadable JSON/JSONL datasets for Mirro clusters."""
import urllib.request, urllib.parse, json, sys

queries = [
    "russian+instructions", "russian+qa", "russian+dialogues",
    "code+instructions", "code+qa", "coding+tasks",
    "design+prompts", "svg+generation", "creative+coding",
    "math+problems", "science+qa", "general+instructions",
]

seen = set()
found = []

for q in queries:
    url = "https://huggingface.co/api/datasets?search=" + urllib.parse.quote(q) + "&sort=downloads&limit=15"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=12).read())
    except Exception as e:
        print(f"[{q}] err {str(e)[:40]}")
        continue

    for item in data:
        ds_id = item.get("id", "")
        if not ds_id or ds_id in seen:
            continue
        dl = item.get("downloads", 0)
        if dl < 80:
            continue
        siblings = item.get("siblings", [])
        # want a direct json/jsonl file
        json_files = [s.get("rfilename", "") for s in siblings
                      if s.get("rfilename", "").endswith((".jsonl", ".json"))
                      and not s.get("rfilename", "").startswith(".")]
        if not json_files:
            continue
        tags = " ".join(item.get("tags", []))
        cat = "general"
        tl = tags.lower()
        if any(t in tl for t in ["russian", "ru", "рус"]):
            cat = "ru"
        elif any(t in tl for t in ["code", "programming", "coding"]) or "code" in ds_id.lower():
            cat = "code"
        elif any(t in tl for t in ["design", "svg", "graphic", "creative", "art", "ui"]):
            cat = "design"
        elif any(t in tl for t in ["math", "mathematics"]):
            cat = "math"
        seen.add(ds_id)
        found.append((cat, dl, ds_id, json_files[0]))

# Sort by downloads
found.sort(key=lambda x: -x[1])
print(f"Найдено {len(found)} доступных датасетов с JSON/JSONL:\n")
for cat, dl, ds_id, fname in found[:40]:
    print(f"  [{cat}] {dl:>8}  {ds_id}  → {fname}")