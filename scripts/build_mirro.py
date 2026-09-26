# -*- coding: utf-8 -*-
"""
Mirro Build — assembly check + source distribution.
====================================================
Checks all project parts (Python, key files, compile of every .py) and
packs a clean source zip into dist/ (data, models, keys, backups excluded).

Usage:
  python scripts/build_mirro.py          # check + build zip
  python scripts/build_mirro.py --check  # only checks, no zip
"""

import argparse
import py_compile
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {
    "data", "models", "keys", "backups", "restore", "logs",
    "__pycache__", ".git", "dist",
}
REQUIRED = [
    "README.md", "IDENTITY.md", "mirro_launcher.pyw",
    "core/mirro_core.py", "web/index.html", "web/meysto-neiroset.html",
    "scripts/algorithms.py", "scripts/thinking.py", "scripts/rag.py",
    "scripts/providers.py", "scripts/cipher.py", "scripts/build_mirro.py",
]
PY_DIRS = ["core", "scripts", "algos"]


def check_python():
    ver = sys.version_info
    ok = ver >= (3, 8)
    print(f"[py] python {ver.major}.{ver.minor}.{ver.micro} - {'OK' if ok else 'TOO OLD'}")
    return ok


def check_files():
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    for p in REQUIRED:
        print(f"[file] {'OK ' if (ROOT / p).exists() else 'MISS'} {p}")
    return not missing


def compile_all():
    bad = []
    count = 0
    for d in PY_DIRS:
        for f in sorted((ROOT / d).glob("*.py")):
            count += 1
            try:
                py_compile.compile(str(f), doraise=True)
            except py_compile.PyCompileError as e:
                bad.append(str(e))
    print(f"[pyc] compiled {count} files, errors={len(bad)}")
    for e in bad[:10]:
        print("  ERROR:", e)
    return not bad


def build_zip():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    arcname_root = "Mirro_v0.3"
    out = dist / f"{arcname_root}_src.zip"
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(ROOT.rglob("*")):
            if f.is_dir():
                continue
            try:
                rel = f.relative_to(ROOT)
            except ValueError:
                continue
            parts = rel.parts
            if any(part in EXCLUDE_DIRS for part in parts):
                continue
            z.write(f, f"{arcname_root}/{rel.as_posix()}")
            n += 1
    size = out.stat().st_size
    print(f"[zip] {out} - {n} files, {size / 1024:.0f} KB")
    return True


def check_smoke():
    """Делаем сборку самопроверяющейся: функциональные проверки, а не только компиляция."""
    ok = True
    try:
        sys.path.insert(0, str(ROOT))
        from scripts.voice import try_jarvis
        j = try_jarvis("мама джарвис доложи обстановку")
        good = isinstance(j, str) and "Слушаю" in j
        ok = ok and good
        print("[smoke] jarvis trigger:", "OK" if good else "FAIL")
    except Exception as e:
        print("[smoke] jarvis ERROR:", e)
        ok = False
    try:
        sys.path.insert(0, str(ROOT))
        from scripts.cipher import encode, decode
        data = b"Mirro self-check \x00\xff ok"
        key = b"kluch-dlya-proverki"
        restored = bytes(decode(encode(data, key), key))
        good = restored == data
        ok = ok and good
        print("[smoke] cipher round-trip:", "OK" if good else "FAIL")
    except Exception as e:
        print("[smoke] cipher ERROR:", e)
        ok = False
    try:
        sys.path.insert(0, str(ROOT))
        from scripts.providers import status as pv_status
        st = pv_status()
        good = isinstance(st, dict)
        ok = ok and good
        print("[smoke] providers status:", "OK" if good else "FAIL", st)
    except Exception as e:
        print("[smoke] providers ERROR:", e)
        ok = False
    try:
        import json as _json
        st = _json.loads((ROOT / "models" / "model_state.json").read_text("utf-8"))
        w = st.get("perceptron_weights") or {}
        good = all(k in w for k in ("f0", "f1", "f2", "f3")) and \
               isinstance(st.get("perceptron_bias"), (int, float))
        ok = ok and good
        print("[smoke] perceptron state:", "OK" if good else "FAIL",
              {k: round(w[k], 4) for k in ("f0", "f1", "f2", "f3")})
    except Exception as e:
        print("[smoke] perceptron state ERROR:", e)
        ok = False
    return ok


def main():
    ap = argparse.ArgumentParser(description="Mirro build / assembly check")
    ap.add_argument("--check", action="store_true", help="only checks, no zip")
    args = ap.parse_args()

    ok = True
    ok &= check_python()
    ok &= check_files()
    ok &= compile_all()
    ok &= check_smoke()
    print("[summary]", "ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    if not args.check and ok:
        build_zip()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())