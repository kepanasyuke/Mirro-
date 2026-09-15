#!/usr/bin/env python3
"""
Mirro Reference Collector
=========================
Собирает референсы, картинки, звуки, видео из ОТКРЫТЫХ бесплатных источников.
Без регистрации и SMS — только публичные API.

Источники:
  • Wikimedia Commons (миллионы свободных изображений)
  • Openverse (WordPress) — 700M+ CC-контент
  • Pexels (по прямым ссылкам, публичная коллекция)
  • Pixabay (по прямым ссылкам)
  • NASA API (снимки космоса, Earth)
  • Archive.org (аудио, видео, картинки)
"""

import json, os, io, time, urllib.request, urllib.parse, urllib.error, hashlib, threading, queue
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import Counter

MIRRO = Path(r"D:\Mirro")
REF_DIR = MIRRO / "data" / "references"
REF_DIR.mkdir(parents=True, exist_ok=True)

CATALOG_FILE = REF_DIR / "catalog.json"

# Поисковые запросы для первичного сбора
DESIGN_QUERIES = [
    "poster design", "typography poster", "color palette",
    "magazine layout", "minimalist design", "logo design",
    "flat illustration", "abstract art", "character design",
    "landscape illustration", "nature landscape",
    "architecture design", "interior design",
    "texture pattern", "minimalist art",
]


class ReferenceCollector:
    """Collects references from open sources with zero API keys."""

    def __init__(self):
        self.catalog = self._load_catalog()
        self.total_collected = len(self.catalog)
        self.results_queue = queue.Queue()
        
    def _load_catalog(self):
        if CATALOG_FILE.exists():
            try:
                return json.loads(CATALOG_FILE.read_text("utf-8"))
            except Exception:
                return []
        return []

    def _save_catalog(self):
        CATALOG_FILE.write_text(json.dumps(self.catalog, ensure_ascii=False, indent=2), "utf-8")

    def _fetch(self, url, timeout=15):
        """Fetch URL with proper headers."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MirroCollector/1.0"
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            return None

    def _fetch_bytes(self, url, timeout=30):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MirroCollector/1.0"
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception:
            return None

    # ---- 1. Wikimedia Commons ----
    def collect_wikimedia(self, query: str, max_results: int = 20):
        """Search Wikimedia Commons API (no auth)."""
        url = ("https://commons.wikimedia.org/w/api.php"
               "?action=query&list=search&srsearch=" + urllib.parse.quote(query) +
               "&srnamespace=6&srlimit=20&format=json&srqiprofile=classic_ns6")
        data = self._fetch(url)
        if not data:
            return []

        try:
            results = json.loads(data).get("query", {}).get("search", [])
        except Exception:
            return []

        count = 0
        for result in results:
            if count >= max_results:
                break
            title = result.get("title", "")
            if not title:
                continue

            # Get image URL
            img_url = ("https://commons.wikimedia.org/w/api.php"
                       "?action=query&titles=" + urllib.parse.quote(title) +
                       "&prop=imageinfo&iiprop=url&format=json")
            img_data = self._fetch(img_url)
            if not img_data:
                continue
            try:
                pages = json.loads(img_data).get("query", {}).get("pages", {})
                for page_id, info in pages.items():
                    if page_id == "-1":
                        continue
                    img_info = info.get("imageinfo", [])
                    if img_info and "url" in img_info[0]:
                        file_url = img_info[0]["url"]
                        self.catalog.append({
                            "source": "wikimedia", "query": query,
                            "title": title.replace("File:", ""),
                            "url": file_url,
                            "collected": datetime.utcnow().isoformat(),
                        })
                        count += 1
            except Exception:
                continue
        return count

    # ---- 2. Openverse (free CC images) ----
    def collect_openverse(self, query: str, max_results: int = 15):
        """Openverse API — free CC images, no key needed for limited use."""
        url = ("https://api.openverse.org/v1/images/?q=" + urllib.parse.quote(query) +
               "&page_size=15&license=cc-by")
        data = self._fetch(url)
        if not data:
            return 0
        try:
            results = json.loads(data).get("results", [])
        except Exception:
            return 0

        count = 0
        for r in results:
            if count >= max_results:
                break
            img_url = r.get("url", "")
            if img_url:
                self.catalog.append({
                    "source": "openverse", "query": query,
                    "title": r.get("title", ""),
                    "url": img_url,
                    "license": r.get("license", "cc-by"),
                    "creator": r.get("creator", ""),
                    "collected": datetime.utcnow().isoformat(),
                })
                count += 1
        return count

    # ---- 3. NASA API (public domain) ----
    def collect_nasa(self, query: str, max_results: int = 10):
        """NASA Image API — public domain, no key needed."""
        url = ("https://images-api.nasa.gov/search?q=" + urllib.parse.quote(query) +
               "&media_type=image&page_size=10")
        data = self._fetch(url)
        if not data:
            return 0
        try:
            items = json.loads(data).get("collection", {}).get("items", [])
        except Exception:
            return 0

        count = 0
        for item in items:
            if count >= max_results:
                break
            data_ = item.get("data", [{}])[0]
            links = item.get("links", [])
            img_url = links[0]["href"] if links else ""

            if img_url:
                self.catalog.append({
                    "source": "nasa", "query": query,
                    "title": data_.get("title", ""),
                    "description": data_.get("description", "")[:200],
                    "url": img_url,
                    "collected": datetime.utcnow().isoformat(),
                })
                count += 1
        return count

    # ---- 4. Archive.org (audio, video, images) ----
    def collect_archive(self, query: str, max_results: int = 10):
        """Archive.org search — free public domain content."""
        url = ("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(query) +
               "&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=description&rows=10&page=1&output=json")
        data = self._fetch(url)
        if not data:
            return 0
        try:
            results = json.loads(data).get("response", {}).get("docs", [])
        except Exception:
            return 0

        count = 0
        for r in results:
            if count >= max_results:
                break
            ident = r.get("identifier", "")
            if ident:
                self.catalog.append({
                    "source": "archive", "query": query,
                    "title": r.get("title", ""),
                    "url": f"https://archive.org/details/{ident}",
                    "description": (r.get("description", [""])[0] if isinstance(r.get("description"), list) else "")[:200],
                    "collected": datetime.utcnow().isoformat(),
                })
                count += 1
        return count

    # ---- Met Museum (public domain art) ----
    def collect_met(self, query: str, max_results: int = 10):
        """Met Museum Collection API — public domain art images."""
        try:
            url = ("https://collectionapi.metmuseum.org/public/collection/v1/search"
                   "?q=" + urllib.parse.quote(query) + "&hasImages=true&pageSize=20")
            data = self._fetch(url)
            if not data:
                return 0
            ids = json.loads(data).get("objectIDs", []) or []
        except Exception:
            return 0

        count = 0
        for oid in ids[:max_results * 2]:
            if count >= max_results:
                break
            try:
                obj_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}"
                obj_data = self._fetch(obj_url)
                if not obj_data:
                    continue
                obj = json.loads(obj_data)
                img_url = obj.get("primaryImage", "")
                if img_url:
                    self.catalog.append({
                        "source": "metmuseum", "query": query,
                        "title": obj.get("title", ""),
                        "url": img_url,
                        "artist": obj.get("artistDisplayName", ""),
                        "year": obj.get("objectDate", ""),
                        "collected": datetime.utcnow().isoformat(),
                    })
                    count += 1
            except Exception:
                continue
        return count

    # ---- Bulk collect ----
    def collect_all(self, queries: list, max_per_query: int = 15):
        """Run collection from all sources for all queries."""
        total = 0
        print(f"\n📸 Mirro Collector запуск ({len(queries)} запросов)")
        print(f"{'='*60}")

        for i, query in enumerate(queries, 1):
            print(f"  [{i}/{len(queries)}] {query[:50]}", end="")

            # Wikimedia
            try:
                n = self.collect_wikimedia(query, max_per_query // 2) or 0
                total += n if isinstance(n, (int, float)) else 0
            except Exception:
                pass

            # Met Museum
            try:
                n2 = self.collect_met(query, max_per_query // 2)
                total += n2 if isinstance(n2, int) else 0
            except Exception:
                pass

            # NASA
            try:
                if any(kw in query.lower() for kw in ["space", "nasa", "earth", "космос"]):
                    n3 = self.collect_nasa(query, 5)
                    total += n3 if isinstance(n3, int) else 0
            except Exception:
                pass

            print(f"  (total so far: {len(self.catalog)})")

        self._save_catalog()
        print(f"\n✅ Итого: {len(self.catalog)} референсов в каталоге")
        return len(self.catalog)

    # ---- Get random reference ----
    def get_random(self, source: str = ""):
        """Get a random reference from the catalog."""
        import random
        candidates = [r for r in self.catalog if not source or r.get("source") == source]
        if not candidates:
            return None
        return random.choice(candidates)

    # ---- Show latest ----
    def show_latest(self, n: int = 5):
        """Show last N collected references."""
        for ref in self.catalog[-n:]:
            print(f"  [{ref['source']:10}] {ref.get('title','')[:60]}")
            print(f"           {ref['url'][:100]}")


# ===== API SERVER =====
collector = ReferenceCollector()

class CollectorAPI(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path
        if path == "/status":
            self._json({
                "total": len(collector.catalog),
                "sources": dict(__import__("collections").Counter(r["source"] for r in collector.catalog)),
                "api": "Mirro Collector — бесплатные открытые стоки",
                "hint": "POST /collect — запустить сбор"
            })
        elif path == "/latest":
            tail = collector.catalog[-20:]
            self._json(tail)
        elif path.startswith("/random"):
            source = path.split("?source=")[-1] if "?source=" in path else ""
            ref = collector.get_random(source)
            if ref:
                self._json(ref)
            else:
                self._json({"error": "no references"}, 404)
        else:
            self._json({"error": "use /status, /latest, /random"}, 404)

    def do_POST(self):
        if self.path == "/collect":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length)) if length else {}
                queries = body.get("queries", DESIGN_QUERIES)
                max_per = body.get("max_per_query", 15)
                total = collector.collect_all(queries, max_per)
                self._json({"result": "ok", "total_references": total})
            except Exception as e:
                self._json({"error": str(e)}, 400)
        else:
            self._json({"error": "not found"}, 404)

    def log_message(self, format, *args):
        pass


def main():
    print(f"""
╔══════════════════════════════════════════╗
║      Mirro Reference Collector          ║
║   Бесплатные референсы без регистрации  ║
╚══════════════════════════════════════════╝

  Источники:
    • Wikimedia Commons — миллионы свободных изображений
    • Openverse — 700M+ CC-контент
    • NASA — космос, Земля, наука (public domain)
    • Archive.org — аудио, видео, изображения

  База: {len(collector.catalog)} референсов
  API:  http://127.0.0.1:3445
""")
    HOST, PORT = "127.0.0.1", 3445
    server = HTTPServer((HOST, PORT), CollectorAPI)

    # Auto-run initial collection
    if len(collector.catalog) < 10:
        print("  🔄 Первичный сбор референсов...")
        collector.collect_all(DESIGN_QUERIES[:30], max_per_query=10)
        print(f"\n  База: {len(collector.catalog)} референсов")

    print(f"\n  API: http://{HOST}:{PORT}")
    print(f"  POST /collect — запуск сбора")
    print(f"  GET  /random  — случайный референс")
    print(f"  GET  /latest  — последние 20")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print("\n\n  Collector остановлен.")


if __name__ == "__main__":
    main()