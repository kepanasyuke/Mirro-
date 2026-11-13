# -*- coding: utf-8 -*-
"""Очистка корпусов data/ (улучшение №35).

Проходит по маленьким JSONL-файлам (`{"instruction","input","output"}`) в
`data/self_learned` и `data/processed` (только небольшие — чтобы не трогать
гигантские ru.jsonl/generated.jsonl), и:
  * нормализует текст: нижний регистр, сжатие пробелов, вырезание управляющих
    символов и мусорной пунктуации (Porter-подобный шаг: приведение к токенам);
  * отсекает пустые/шумовые строки (слишком короткие или без содержательных слов);
  * дедуплицирует по (instruction-префикс + output-префикс);
  * считает статистику «до/после».

Чистый Python, атомарные функции, один return на функцию.
Запуск:  python scripts/clean_corpus.py [--self-learned] [--processed] [--apply]
"""
import argparse, json, re
from pathlib import Path

MIRRO = Path(r"D:\Mirro")
SELF_LEARNED = MIRRO / "data" / "self_learned"
PROCESSED = MIRRO / "data" / "processed"
MAX_BYTES = 2_000_000      # обрабатываем только файлы ≤ 2 МБ

_RE_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_RE_REPEATED = re.compile(r"(.)\1{3,}")     # "ааааа" → мусор


def _norm_ws(text):
    """Сжимает пробелы и убирает управляющие символы. Один return: str."""
    return _RE_CONTROL.sub(" ", text).strip()


def clean_and_tokenize_corpus_line(line):
    """Очищает строку датасета от мусора и возвращает токены. Один return: list."""
    lowered = (line or "").lower()
    lowered = _norm_ws(lowered)
    # оставляем только буквы/цифры/простую пунктуацию
    cleaned = "".join(ch for ch in lowered
                      if ch.isalnum() or ch in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя "
                      or ch in "!?.,;:-")
    cleaned = _RE_REPEATED.sub(r"\1\1", cleaned)
    tokens = cleaned.split()
    # отсекаем стоп-мусор (однобуквенные, точки-тире)
    return [t for t in tokens if len(t) > 1 or t.isalnum()]


def _record_key(rec):
    """Ключ дедупа: хвост instruction + начало output. Один return: str."""
    inst = rec.get("instruction", "")[:40].lower()
    out = rec.get("output", "")[:60].lower()
    return inst + "::" + out


def _is_keepable(rec):
    """Проверяет, что пример содержательный. Один return: bool."""
    inst_tok = clean_and_tokenize_corpus_line(rec.get("instruction", ""))
    out_tok = clean_and_tokenize_corpus_line(rec.get("output", ""))
    return len(inst_tok) >= 2 and len(out_tok) >= 2


def clean_jsonl(path, apply=False):
    """Чистит один JSONL-файл. Возвращает (kept, removed). Один return: tuple."""
    kept = 0
    removed = 0
    ok = True
    seen = set()
    out_rows = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped:
                    removed += 1
                else:
                    try:
                        rec = json.loads(stripped)
                    except Exception:
                        rec = None
                    key = _record_key(rec) if isinstance(rec, dict) and _is_keepable(rec) else None
                    if rec is None or not isinstance(rec, dict) or not _is_keepable(rec):
                        removed += 1
                    elif key in seen:
                        removed += 1
                    else:
                        seen.add(key)
                        out_rows.append(rec)
                        kept += 1
    except OSError:
        ok = False
    if ok and apply and out_rows:
        try:
            with open(path, "w", encoding="utf-8") as fh:
                for rec in out_rows:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            ok = False
    if not ok:
        kept = 0
        removed = 0
    return kept, removed


def clean_directory(directory, apply=False):
    """Чистит все подходящие файлы в папке. Один return: dict-отчёт."""
    total_kept = 0
    total_removed = 0
    files = 0
    if directory.exists():
        for f in sorted(directory.glob("*.jsonl")):
            try:
                if f.stat().st_size <= MAX_BYTES:
                    kept, removed = clean_jsonl(f, apply)
                    files += 1
                    total_kept += kept
                    total_removed += removed
            except OSError:
                pass
    return {"files": files, "kept": total_kept, "removed": total_removed}


def main():
    ap = argparse.ArgumentParser(description="Очистка и дедупликация корпусов data/")
    ap.add_argument("--self-learned", action="store_true", help="чистить data/self_learned")
    ap.add_argument("--processed", action="store_true", help="чистить data/processed")
    ap.add_argument("--apply", action="store_true", help="реально перезаписать (иначе сухой прогон)")
    args = ap.parse_args()
    if not args.self_learned and not args.processed:
        args.self_learned = True
    mode = "ПРИМЕНЯЕМ" if args.apply else "СУХОЙ ПРОГОН (--apply)"
    print(f"== {mode} ==")
    total = {"kept": 0, "removed": 0, "files": 0}
    if args.self_learned:
        r = clean_directory(SELF_LEARNED, args.apply)
        print(f"self_learned: {r['files']} файлов, до={r['kept']+r['removed']}, после={r['kept']}, удалено={r['removed']}")
        total["kept"] += r["kept"]; total["removed"] += r["removed"]; total["files"] += r["files"]
    if args.processed:
        r = clean_directory(PROCESSED, args.apply)
        print(f"processed:    {r['files']} файлов, до={r['kept']+r['removed']}, после={r['kept']}, удалено={r['removed']}")
        total["kept"] += r["kept"]; total["removed"] += r["removed"]; total["files"] += r["files"]
    print(f"ИТОГО: файлов {total['files']}, оставлено {total['kept']}, удалено {total['removed']}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())