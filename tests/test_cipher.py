# -*- coding: utf-8 -*-
"""Юнит-тесты десятичного поточного шифра (scripts/cipher.py).

Проверяем на реальных функциях:
  - симметричность: оригинал → шифр → расшифровка == оригинал (как через CLI, так и через ту же transform_bytes_to_cipher);
  - стойкость: зашифрованные данные ≠ исходным;
  - генератор ключа выдаёт строку заданной длины;
  - пустой ключ кидает ошибку (расширять нечего).

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.cipher import (
    transform_bytes_to_cipher, try_generate_secure_key, try_load_secure_key,
    encode, decode,
)


class TestMirroCipher(unittest.TestCase):
    def setUp(self):
        self.original = b"Mirro Quantum Knowledge Graph Data 2026"
        self.test_key = "QuantumSaltKey2026"

    def test_symmetric_cycle(self):
        enc = transform_bytes_to_cipher(self.original, self.test_key, decrypt=False)
        self.assertNotEqual(enc, self.original, "шифр обязан отличаться от исходника")
        dec = transform_bytes_to_cipher(enc, self.test_key, decrypt=True)
        self.assertEqual(dec, self.original, "расшифровка должна вернуть оригинал")

    def test_symmetric_via_encode_decode(self):
        # десятичный массив encode() ↔ bytes decode() — тоже симметрично
        nums = encode(self.original, self.test_key.encode("utf-8"))
        self.assertIsInstance(nums, list)
        restored = decode(nums, self.test_key.encode("utf-8"))
        self.assertEqual(restored, self.original)

    def test_key_generation_length(self):
        key = try_generate_secure_key(key_length=16, seed=1)
        self.assertEqual(len(key), 16)
        self.assertTrue(key.isalnum(), "ключ должен быть alnum-строкой")

    def test_empty_key_raises(self):
        # пустой ключ расширять нечем — обязана упасть при шифровании
        with self.assertRaises(ValueError):
            encode(self.original, b"")

    def test_load_generates_if_missing(self):
        import tempfile
        p = os.path.join(tempfile.gettempdir(), "mt_secret_missing.key")
        if os.path.exists(p):
            os.remove(p)
        key = try_load_secure_key(key_filepath=p)
        self.assertTrue(len(key) >= 8, "сгенерированный ключ не должен быть пустым")
        if os.path.exists(p):
            os.remove(p)


if __name__ == "__main__":
    unittest.main()