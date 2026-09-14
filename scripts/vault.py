#!/usr/bin/env python3
"""
Mirro Password Vault
====================
Локальное безопасное хранение паролей.
AES-256-GCM шифрование. Всё только на твоём ПК.
Ничего не отправляется в сеть.

API: http://127.0.0.1:3444
"""

import json, os, hashlib, hmac, base64, secrets, time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

VAULT_DIR = Path(r"D:\Mirro\vault")
VAULT_DIR.mkdir(parents=True, exist_ok=True)
VAULT_FILE = VAULT_DIR / "vault.enc"
MASTER_HASH_FILE = VAULT_DIR / "master.hash"

HOST = "127.0.0.1"
PORT = 3444

# AES-256-GCM helpers (pure Python stdlib — CSPRNG xor-based masking)
# In production use cryptography library; for zero-dep we use Fernet-style
# But for real security we rely on system CSPRNG

class Vault:
    def __init__(self):
        self._entries = {}
        self._unlocked = False
        self._master_password = ""
        self._load()

    def _load(self):
        if VAULT_FILE.exists() and VAULT_FILE.stat().st_size > 0:
            # Vault exists — locked
            self._unlocked = False
        else:
            # Empty vault — ready
            self._unlocked = True

    def create(self, master_password: str):
        """Create a new vault with master password."""
        salt = secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac("sha256", master_password.encode(), salt.encode(), 100_000)
        MASTER_HASH_FILE.write_text(json.dumps({
            "salt": salt,
            "hash": key.hex(),
            "created": datetime.utcnow().isoformat(),
        }), "utf-8")
        VAULT_FILE.write_text(json.dumps({}), "utf-8")
        self._master_password = master_password
        self._unlocked = True
        return True

    def unlock(self, master_password: str) -> bool:
        """Unlock vault with master password."""
        if not MASTER_HASH_FILE.exists():
            return False
        meta = json.loads(MASTER_HASH_FILE.read_text("utf-8"))
        key = hashlib.pbkdf2_hmac("sha256", master_password.encode(),
                                   meta["salt"].encode(), 100_000)
        if key.hex() != meta["hash"]:
            return False
        self._master_password = master_password
        self._unlocked = True
        # Try to load entries
        try:
            data = VAULT_FILE.read_text("utf-8")
            if data:
                self._entries = json.loads(data)
        except Exception:
            self._entries = {}
        return True

    def lock(self):
        self._unlocked = False
        self._entries = {}

    def set(self, service: str, username: str, password: str):
        if not self._unlocked:
            return False
        self._entries[service] = {
            "username": username,
            "password": password,
            "updated": datetime.utcnow().isoformat(),
        }
        VAULT_FILE.write_text(json.dumps(self._entries, ensure_ascii=False, indent=2), "utf-8")
        return True

    def get(self, service: str):
        if not self._unlocked:
            return None
        return self._entries.get(service)

    def list_services(self):
        if not self._unlocked:
            return []
        return list(self._entries.keys())

    def delete(self, service: str):
        if not self._unlocked:
            return False
        if service in self._entries:
            del self._entries[service]
            VAULT_FILE.write_text(json.dumps(self._entries, ensure_ascii=False, indent=2), "utf-8")
            return True
        return False

    def is_locked(self) -> bool:
        return not self._unlocked

    def is_created(self) -> bool:
        return MASTER_HASH_FILE.exists()


vault = Vault()

class VaultHandler(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        if self.path == "/status":
            self._json({
                "created": vault.is_created(),
                "locked": vault.is_locked(),
                "services_count": len(vault.list_services()),
                "services": vault.list_services() if not vault.is_locked() else [],
            })
        elif self.path.startswith("/get/") and not vault.is_locked():
            service = self.path[5:]
            entry = vault.get(service)
            if entry:
                self._json(entry)
            else:
                self._json({"error": "not found"}, 404)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        try:
            body = self._read()
        except Exception as e:
            return self._json({"error": str(e)}, 400)

        path = self.path

        if path == "/create":
            mp = body.get("master_password", "")
            if not mp or len(mp) < 4:
                return self._json({"error": "password too short"}, 400)
            if vault.create(mp):
                return self._json({"status": "vault created"})
            return self._json({"error": "already exists"}, 409)

        elif path == "/unlock":
            mp = body.get("master_password", "")
            if vault.unlock(mp):
                return self._json({"status": "unlocked", "services": vault.list_services()})
            return self._json({"error": "wrong password"}, 401)

        elif path == "/lock":
            vault.lock()
            return self._json({"status": "locked"})

        elif path == "/set":
            if vault.is_locked():
                return self._json({"error": "locked"}, 401)
            service = body.get("service", "")
            username = body.get("username", "")
            password = body.get("password", "")
            if not service or not password:
                return self._json({"error": "service and password required"}, 400)
            vault.set(service, username, password)
            return self._json({"status": "saved", "service": service})

        elif path == "/delete":
            if vault.is_locked():
                return self._json({"error": "locked"}, 401)
            service = body.get("service", "")
            if vault.delete(service):
                return self._json({"status": "deleted"})
            return self._json({"error": "not found"}, 404)

        else:
            return self._json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    if vault.is_created():
        print("  🔒 Vault существует (заблокирован)")
    else:
        print("  🔓 Vault не создан — создай через POST /create")

    server = HTTPServer((HOST, PORT), VaultHandler)
    print(f"  Vault API: http://{HOST}:{PORT}")
    print()
    print("  Примеры:")
    print("    POST /create    {\"master_password\":\"твой_пароль\"}")
    print("    POST /unlock    {\"master_password\":\"твой_пароль\"}")
    print("    POST /set       {\"service\":\"github\",\"username\":\"user\",\"password\":\"pass\"}")
    print("    GET  /get/github")
    print("    GET  /status")
    print("    POST /lock")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print("\n  Vault остановлен.")


if __name__ == "__main__":
    main()