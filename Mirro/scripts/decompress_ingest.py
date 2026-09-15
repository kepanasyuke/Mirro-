#!/usr/bin/env python3
"""Decompress .zst datasets and ingest into clusters."""
import json, sys
from pathlib import Path

RAW = Path(r"D:\Mirro\data\raw")
PROC = Path(r"D:\Mirro\data\processed")
PROC.mkdir(parents=True, exist_ok=True)

def load_zst(path):
    import zstandard
    dctx = zstandard.ZstdDecompressor()
    data = dctx.decompress(path.read_bytes())
    return data.decode("utf-8", errors="replace")

def convert_item(item):
    if not isinstance(item, dict):
        return None
    if "instruction" in item:
        return {
            "instruction": str(item.get("instruction", ""))[:1000],
            "input": str(item.get("input", ""))[:500],
            "output": str(item.get("output", item.get("response", "")))[:3000],
        }
    for key in ("messages", "conversations"):
        msgs = item.get(key)
        if isinstance(msgs, list) and msgs:
            user_p, asst_p = [], []
            for m in msgs:
                if isinstance(m, dict):
                    role = str(m.get("role", m.get("from", ""))).lower()
                    content = m.get("content", m.get("value", ""))
                    if role in ("user", "human"):
                        user_p.append(str(content))
                    elif role in ("assistant", "gpt", "bot"):
                        asst_p.append(str(content))
            if user_p and asst_p:
                return {"instruction": "\n".join(user_p)[:1000], "input": "", "output": "\n".join(asst_p)[:3000]}
    if "question" in item and "answer" in item:
        return {
            "instruction": str(item.get("question", ""))[:1000],
            "input": str(item.get("system_prompt", ""))[:500],
            "output": str(item.get("answer", item.get("response", "")))[:3000],
        }
    return None

def main():
    total = 0
    # Process all .zst files in raw tree
    for zst in RAW.rglob("*.zst"):
        cluster = zst.parts[-4] if len(zst.parts) >= 4 else "general"
        # Determine cluster by path
        rel = zst.relative_to(RAW)
        parts = rel.parts
        cluster = parts[0] if parts else "general"
        # Show human readable
        print(f"\n📦 {zst.name} ({zst.stat().st_size/1e6:.1f} MB) -> cluster '{cluster}'")

        text = load_zst(zst)
        items = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except Exception:
                    pass
        converted = [convert_item(i) for i in items if convert_item(i)]
        if converted:
            out_path = PROC / f"{cluster}.jsonl"
            with open(out_path, "a", encoding="utf-8") as f:
                for item in converted:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            total += len(converted)
            print(f"  ✅ {len(converted)} examples -> {out_path}")

        # Mark done by renaming? No, keep. Just move on.

    print(f"\n{'='*60}")
    print(f"Total ingested: {total}")
    print("CLUSTER SIZES:")
    for f in sorted(PROC.glob("*.jsonl")):
        cnt = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
        print(f"  {f.stem:12} {cnt:>7}")

if __name__ == "__main__":
    main()