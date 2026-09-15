# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 06 · Строки и текст (10 алгоритмов)
"""

import re
from collections import Counter


def reverse_string(s):
    return s[::-1]


def is_palindrome(s):
    t = re.sub(r"[^a-zа-яё0-9]", "", s.lower())
    return t == t[::-1]


def longest_common_prefix(strs):
    if not strs:
        return ""
    prefix = strs[0]
    for s in strs[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix


def levenshtein(a, b):
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev = dp[0]
        dp[0] = i
        for j, cb in enumerate(b, 1):
            cur = dp[j]
            cost = 0 if ca == cb else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = cur
    return dp[-1]


def anagram(a, b):
    return Counter(a.replace(" ", "").lower()) == Counter(b.replace(" ", "").lower())


def atbash(s):
    """Шифр Атбаш (a→z, b→y...)."""
    ru_lower = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    ru_rev = ru_lower[::-1]
    en_lower = "abcdefghijklmnopqrstuvwxyz"
    en_rev = en_lower[::-1]
    out = []
    for ch in s:
        if ch.islower() and ch in ru_lower:
            out.append(ru_rev[ru_lower.index(ch)])
        elif ch.islower() and ch in en_lower:
            out.append(en_rev[en_lower.index(ch)])
        elif ch.isupper() and ch.lower() in ru_lower:
            out.append(ru_rev[ru_lower.index(ch.lower())].upper())
        elif ch.isupper() and ch.lower() in en_lower:
            out.append(en_rev[en_lower.index(ch.lower())].upper())
        else:
            out.append(ch)
    return "".join(out)


def caesar(s, shift=3):
    out = []
    for ch in s:
        if ch.islower() and "а" <= ch <= "я":
            out.append(chr((ord(ch) - ord("а") + shift) % 32 + ord("а")))
        elif ch.isupper() and "А" <= ch <= "Я":
            out.append(chr((ord(ch) - ord("А") + shift) % 32 + ord("А")))
        elif ch.islower() and "a" <= ch <= "z":
            out.append(chr((ord(ch) - ord("a") + shift) % 26 + ord("a")))
        elif ch.isupper() and "A" <= ch <= "Z":
            out.append(chr((ord(ch) - ord("A") + shift) % 26 + ord("A")))
        else:
            out.append(ch)
    return "".join(out)


def substring_kmp(text, pattern):
    """Поиск подстроки алгоритмом Кнута-Морриса-Пратта."""
    if not pattern:
        return 0
    # префикс-функция
    pi = [0] * len(pattern)
    for i in range(1, len(pattern)):
        j = pi[i - 1]
        while j > 0 and pattern[i] != pattern[j]:
            j = pi[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j
    # поиск
    j = 0
    for i, ch in enumerate(text):
        while j > 0 and ch != pattern[j]:
            j = pi[j - 1]
        if ch == pattern[j]:
            j += 1
        if j == len(pattern):
            return i - j + 1
    return -1


def word_count(text):
    return len(re.findall(r"[a-zа-яё0-9]+", text.lower()))


def truncate(s, n=100, suffix="..."):
    return s[:n] + suffix if len(s) > n else s


def char_freq(text):
    return Counter(ch.lower() for ch in text if ch.strip())


if __name__ == "__main__":
    print("pal:", is_palindrome("А роза упала на лапу Азора"))
    print("lcp:", longest_common_prefix(["abc", "abd", "abf"]))
    print("lev:", levenshtein("кот", "котенок"))
    print("kmp:", substring_kmp("hello world", "world"))
    print("atbash:", atbash("abc"))