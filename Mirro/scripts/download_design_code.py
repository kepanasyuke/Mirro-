#!/usr/bin/env python3
"""Find and download compact JSON datasets for design & code clusters from HF."""
import json, urllib.request, sys, io
from pathlib import Path

PROC = Path(r"D:\Mirro\data\processed")
ROOT = Path(r"D:\Mirro\data\raw")
ROOT.mkdir(parents=True, exist_ok=True)

DESIGN_JSON = [
    # SVG generation datasets (JSON format)
    ("shorecode/svg-generation-6.5k-rows", "svg-generation-6.5k-rows/data.json", "design"),
    ("nyuuzyou/svgrepo", "svgrepo/data.parquet", "design"),
    # Design2Code — HTML screenshot to code
    ("michaelsyao/design_bench_data", "data.json", "design"),
    # Creative graphics
    ("creative-graphic-design/CreativePSD", "data/creative_psd.json", "design"),
]

CODE_JSON = [
    # CodeAlpaca (JSON format)
    ("sahil2801/CodeAlpaca-20k", "codealpaca.json", "code"),
    # HuggingFace Code 18k
    ("rombodawg/LimitlessCode-50k-Instruct", "data.json", "code"),
]

def try_download(ds, fname, target_cluster):
    url = f"https://huggingface.co/datasets/{ds}/resolve/main/{fname}"
    safe = ds.replace("/", "__")
    out_path = ROOT / target_cluster / safe / fname.split("/")[-1]
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"  = already have {ds} ({out_path.stat().st_size/1e6:.1f} MB)")
        return 0

    print(f"  ↓ {ds}/{fname}", end="")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=120)
        data = resp.read()
        out_path.write_bytes(data)
        print(f" → {len(data)/1e6:.1f} MB")
        return len(data)
    except Exception as e:
        err = str(e)[:60]
        print(f" → {err}")
        return 0

def check_ds_api(ds):
    """Check what files a dataset actually has via HF API."""
    url = f"https://huggingface.co/api/datasets/{ds}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        d = json.loads(resp.read())
        files = []
        for s in d.get("siblings", []):
            fn = s.get("rfilename", "")
            if not fn.startswith(".") and not fn.endswith((".md", ".txt", ".gitattributes", ".zst", ".parquet")):
                files.append(fn)
        return files[:10]
    except Exception as e:
        return [f"API error: {e}"]

def convert_file(path, cluster):
    """Convert JSON file to unified JSONL and append to cluster."""
    if not path.exists() or path.stat().st_size == 0:
        return 0
    try:
        data = json.loads(path.read_text("utf-8", errors="replace"))
    except Exception:
        return 0

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return 0

    converted = []
    for item in data:
        if not isinstance(item, dict):
            continue
        # Alpaca format
        if "instruction" in item:
            converted.append({
                "instruction": str(item.get("instruction", ""))[:1000],
                "input": str(item.get("input", ""))[:500],
                "output": str(item.get("output", item.get("response", "")))[:3000],
            })
        elif "messages" in item:
            msgs = item["messages"]
            if isinstance(msgs, list) and msgs:
                user_p = [m.get("content","") for m in msgs if isinstance(m,dict) and m.get("role") in ("user","human")]
                asst_p = [m.get("content","") for m in msgs if isinstance(m,dict) and m.get("role") in ("assistant","gpt","bot")]
                if user_p and asst_p:
                    converted.append({
                        "instruction": "\n".join(user_p)[:1000],
                        "input": "",
                        "output": "\n".join(asst_p)[:3000],
                    })
        elif "question" in item and "answer" in item:
            converted.append({
                "instruction": str(item.get("question",""))[:1000],
                "input": str(item.get("context",""))[:500],
                "output": str(item.get("answer",""))[:3000],
            })

    if converted:
        out_path = PROC / f"{cluster}.jsonl"
        with open(out_path, "a", encoding="utf-8") as f:
            for c in converted:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"      → {len(converted)} examples added to {cluster}")
        return len(converted)
    return 0

if __name__ == "__main__":
    print("=" * 60)
    print("  MIRRO — DOWNLOAD DESIGN & CODE DATASETS")
    print("=" * 60)

    # First check what files really exist for each
    for ds, fname, cluster in DESIGN_JSON + CODE_JSON:
        print(f"\n📦 {ds}")
        files = check_ds_api(ds)
        for f in files[:5]:
            print(f"    {f}")

    print("\n\n" + "=" * 60)
    print("  DOWNLOADING...")
    print("=" * 60)

    total = 0
    for ds, fname, cluster in DESIGN_JSON + CODE_JSON:
        n = try_download(ds, fname, cluster)
        total += n

    print(f"\n  Downloaded: {total/1e6:.1f} MB")

    # Convert what we can
    print("\n📊 PROCESSED CLUSTERS:")
    for f in sorted(PROC.glob("*.jsonl")):
        cnt = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
        print(f"  {f.stem:12} {cnt:>7}")