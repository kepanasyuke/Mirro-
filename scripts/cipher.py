# -*- coding: utf-8 -*-
"""
Mirro Decimal Cipher — гибридное шифрование для защищённого бэкапа.
====================================================================
Принцип: каждый байт данных -> его десятичное значение, сдвинутое по модулю 256
на байт ключа (шифр Виженера). Ключ берётся из файла-документа (или фразы)
и повторяется по длине данных. Результат — строки десятичных чисел.

Обратимо: decode возвращает исходные байты, если подан тот же ключ.
Ключ (документ) НЕ должен попадать в репозиторий — см. .gitignore (keys/).

Без внешних зависимостей: только стандартная библиотека.

Примеры:
  python scripts/cipher.py encode core/stats.json keys/m1u2_doc.txt backups/stats.json.dec
  python scripts/cipher.py decode backups/stats.json.dec keys/m1u2_doc.txt backups/stats.restored.json
  python scripts/cipher.py test                     # самопроверка: round-trip
"""

import argparse
import sys
from pathlib import Path

NUMBERS_PER_LINE = 32


def load_key(key_source):
    """Ключ: путь к файлу-документу или фраза через --phrase."""
    if isinstance(key_source, tuple):  # (is_phrase, value)
        is_phrase, value = key_source
        if is_phrase:
            return value.encode("utf-8")
        return Path(value).read_bytes()
    p = Path(key_source)
    return p.read_bytes()


def expand_key(key, length):
    """Повторяем ключ по длине данных."""
    if not key:
        raise ValueError("Пустой ключ - шифрование невозможно")
    return (key * ((length // len(key)) + 1))[:length]


def encode(data, key):
    k = expand_key(key, len(data))
    return [((b + kb) % 256) for b, kb in zip(data, k)]


def decode(values, key):
    k = expand_key(key, len(values))
    return bytes(((n - kb) % 256) for n, kb in zip(values, k))


def parse_numbers(text):
    out = []
    for tok in text.split():
        tok = tok.strip()
        if not tok or tok.startswith("#"):
            continue
        try:
            out.append(int(tok))
        except ValueError:
            raise ValueError(f"Не число: {tok!r}")
    return out


def main():
    ap = argparse.ArgumentParser(description="Mirro Decimal Cipher (гибрид, ключ из документа)")
    ap.add_argument("mode", choices=["encode", "decode", "test"])
    ap.add_argument("input", nargs="?", help="входной файл (для test — не нужен)")
    ap.add_argument("key", nargs="?", help="файл-документ (ключ) ИЛИ для --phrase игнорируется")
    ap.add_argument("output", nargs="?", help="выходной файл")
    ap.add_argument("--phrase", action="store_true", help="считать аргумент key фразой, а не файлом")
    ap.add_argument("--list", action="store_true", help="выводить числа в одну строку через пробел")
    args = ap.parse_args()

    if args.mode == "test":
        _run_selftest()
        return

    if not (args.input and args.key and args.output):
        ap.error("encode/decode нужны: input, key, output")

    key = (args.phrase, args.key) if args.phrase else args.key
    key_bytes = load_key(key)

    data = Path(args.input).read_bytes()

    if args.mode == "encode":
        result = encode(data, key_bytes)
        lines = []
        if args.list:
            lines.append(" ".join(map(str, result)))
        else:
            line = []
            for i, n in enumerate(result):
                line.append(str(n))
                if (i + 1) % NUMBERS_PER_LINE == 0:
                    lines.append(" ".join(line))
                    line = []
            if line:
                lines.append(" ".join(line))
        Path(args.output).write_text("\n".join(lines) + "\n", "utf-8")
        sys.stdout.write(f"Зашифровано {len(result)} байт -> {args.output}\n")
    else:  # decode
        values = parse_numbers(Path(args.input).read_text("utf-8"))
        restored = decode(values, key_bytes)
        Path(args.output).write_bytes(restored)
        sys.stdout.write(f"Расшифровано {len(restored)} байт -> {args.output}\n")


def _run_selftest():
    import tempfile
    sample = b"Mirro Decimal Cipher test \x00\xff\nhello \xd0\x9c\xd0\xb8\xd1\x80\xd1\x80\xd0\xbe!"
    phrase = "Роль Задача Контекст Формат Рамка - формула сильного промта"
    key = phrase.encode("utf-8")
    enc = encode(sample, key)
    dec = decode(enc, key)
    assert dec == sample, "round-trip failed"
    # устойчивость к разбиению на строки
    text = " ".join(map(str, enc))
    assert decode(parse_numbers(text), key) == sample, "parse failed"
    # несовпадение ключа даёт другой результат (меняем первый байт ключа)
    other = decode(enc, b"Z" + key[1:])
    assert other != sample, "ключ не влияет?!"
    sys.stdout.write(f"OK: round-trip {len(sample)} байт, ключ {len(key)} байт\n")


if __name__ == "__main__":
    main()