#!/usr/bin/env python3
"""
Mirro Self-Learning Module
==========================
Mirro учится сама: ходит в открытые источники, собирает знания,
добавляет в свои кластеры. Работает планировщиком (каждые N часов).

Источники:
  - HuggingFace (новые датасеты по коду/дизайну/RU)
  - Wikipedia (свежие статьи)
  - GitHub (trending репозитории, code review)
  - Stack Overflow (свежие Q&A)
  - Хабр (свежие статьи)
  - Свой опыт (логи вызовов → дообучение)
"""

import json, os, time, random, io, gzip, hashlib, urllib.request, urllib.error, threading
from pathlib import Path
from datetime import datetime, timedelta

MIRRO = Path(r"D:\Mirro")
LEARN_DIR = MIRRO / "data" / "self_learned"
LEARN_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = MIRRO / "logs"
CORE_DIR = MIRRO / "core"

LEARN_META = LEARN_DIR / "meta.json"

# =============================================================
# Mirro's Own Knowledge — what Mirro already knows how to do
# =============================================================
MIRRO_SKILLS = [
    {"domain": "presentation", "skill": "Презентации PPTX", "desc": "Сборка .pptx с анимациями, диаграммами, картинками через PptxGenJS; корпоративные шаблоны; экспорт в PDF"},
    {"domain": "presentation", "skill": "Экспорт презентаций в PDF", "desc": "Конвертация готовых слайдов в PDF для показа и рассылки"},
    {"domain": "3d", "skill": "3D-моделирование в Blender", "desc": "Создание, редактирование, рендеринг сцен через cli-anything; экспорт в игровые движки (BeamNG, Minecraft)"},
    {"domain": "3d", "skill": "CAD-модели (FreeCAD)", "desc": "Технические модели, чертежи, экспорт в STL/STEP"},
    {"domain": "system", "skill": "Управление компьютером", "desc": "Запуск и контроль программ (GIMP, Blender, OBS, браузеры), работа с файлами, PowerShell/bash администрирование"},
    {"domain": "system", "skill": "Автоматизация задач на ПК", "desc": "Скрипты для повторяющихся операций: обработка файлов, бэкапы, конвертация"},
    {"domain": "system", "skill": "Диагностика системы", "desc": "Логи, сеть (DNS/прокси), память, базы данных, процессы"},
    {"domain": "design", "skill": "Генерация SVG-схем и графиков", "desc": "draw.io / Mermaid / inline SVG charts для отчётов"},
    {"domain": "design", "skill": "Вёрстка HTML-отчётов (дашборды)", "desc": "Полностью автономные offline HTML-страницы с CSS/SVG-чартами"},
    {"domain": "design", "skill": "Карты мыслей (mind-map)", "desc": "Интерактивная HTML-схема «Швейцарская сетка» с коллапсом веток"},
    {"domain": "design", "skill": "Презентации (PPTX)", "desc": "Корпоративные слайды с анимациями, диаграммами, картинками"},
    {"domain": "design", "skill": "Генерация изображений", "desc": "GigaChat/Kandinsky: текст → JPEG/PNG для слайдов и отчётов"},
    {"domain": "design", "skill": "Работа с графикой (GIMP)", "desc": "Кадрирование, сжатие, подписи, водяные знаки, склейка, конвертация"},
    {"domain": "design", "skill": "Обработка растровых изображений", "desc": "Через Sharp/Node.js: resize, crop, compress, watermark"},
    {"domain": "design", "skill": "CSS-стилизация и UI-верстка", "desc": "Inline CSS, grid/flexbox, темная тема, адаптивность"},
    {"domain": "document", "skill": "Word (.docx) документы", "desc": "Служебные записки, договоры, отчёты, письма — с реальными Word-стилями"},
    {"domain": "document", "skill": "Excel (.xlsx) таблицы", "desc": "Дашборды, трекеры, бюджеты, финмодели с живыми формулами"},
    {"domain": "document", "skill": "PDF документы", "desc": "Счета, акты, коммерческие предложения, отчёты в PDF"},
    {"domain": "document", "skill": "Проверка договоров по ГК РФ", "desc": "Ревью: НДС, неустойка, подсудность, автопролонгация, red flags"},
    {"domain": "document", "skill": "Оформление по ГОСТ Р 7.0.97-2016", "desc": "Приказы, письма, протоколы — правильные реквизиты, шрифты, отступы"},
    {"domain": "document", "skill": "Проверка реквизитов (ИНН/ОГРН/Счёт)", "desc": "Контрольные числа ИНН, КПП, ОГРН, БИК, ключевание счетов"},
    {"domain": "document", "skill": "Разбор выгрузок из 1С", "desc": "ОСВ, карточки счетов, анализ проводок — баланс Дт/Кт, красное сальдо"},
    {"domain": "research", "skill": "Глубокий веб-ресёрч", "desc": "Многоэтапный поиск по источникам, триангуляция, отчёт со ссылками"},
    {"domain": "research", "skill": "Анализ данных и финансовая модель", "desc": "TAM, прогнозы, cashflow, сценарии — Excel-модель с формулами"},
    {"domain": "research", "skill": "Работа со ссылками и документацией", "desc": "Чтение URL, извлечение контента, конспект, Q&A по документам"},
    {"domain": "research", "skill": "Рабочие планы (HTML)", "desc": "Чек-листы с зависимостями, ресурсами, сроками, полями-прочерками"},
    {"domain": "code", "skill": "Сборка и настройка проектов", "desc": "npm, git, Docker, Python — установка, деплой, конфигурация"},
    {"domain": "code", "skill": "Code review", "desc": "Проверка кода на баги, архитектуру, производительность, стиль"},
    {"domain": "code", "skill": "Отладка и диагностика", "desc": "Чтение логов (Node, Python, SQL, Webpack), DNS/прокси/сеть"},
    {"domain": "code", "skill": "Рефакторинг Python/JS", "desc": "Zero-dep ООП, type hints, async/await, Streamlit, FastAPI"},
    {"domain": "code", "skill": "Разработка CLI-инструментов", "desc": "Python скрипты для автоматизации, парсинга, конвертации данных"},
    {"domain": "ru", "skill": "Знание российского права (основы)", "desc": "ГК РФ, НК РФ, налоги, ООО/ИП, договорное право"},
    {"domain": "ru", "skill": "Налоговый календарь РФ", "desc": "ЕНП, НДФЛ, взносы, НДС, УСН, сроки с учётом выходных"},
]


class SelfLearner:
    """Autonomous learning loop — Mirro grows forever."""

    def __init__(self):
        self.meta = self._load_meta()
        self.session = 0

    def _load_meta(self):
        try:
            return json.loads(LEARN_META.read_text("utf-8"))
        except Exception:
            return {"total_sessions": 0, "total_learned": 0, "domains": {}, "last_run": None}

    def _save_meta(self):
        LEARN_META.write_text(json.dumps(self.meta, ensure_ascii=False, indent=2), "utf-8")

    def _fetch_json(self, url, timeout=20):
        """Fetch JSON from a URL."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MirroSelfLearner/1.0"
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _fetch_text(self, url, timeout=20):
        """Fetch text from a URL."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MirroSelfLearner/1.0"
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            return None

    # ---- HuggingFace trends ----
    def learn_from_hf_trending(self):
        """Find trending/new datasets on HuggingFace and add to catalog."""
        print("  📡 HuggingFace: checking trending datasets...")
        try:
            data = self._fetch_json("https://huggingface.co/api/datasets?sort=trendingScore&limit=20")
            if not data:
                return 0

            existing = set()
            cat_path = MIRRO / "data" / "catalog_phase1.json"
            if cat_path.exists():
                for entry in json.loads(cat_path.read_text("utf-8")):
                    existing.add(entry["ds"])

            new_count = 0
            new_entries = []
            for ds in data:
                ds_id = ds.get("id", "")
                if ds_id in existing or not ds_id:
                    continue
                # Skip very small ones
                downloads = ds.get("downloads", 0)
                if downloads < 100:
                    continue
                tags = " ".join(ds.get("tags", []))
                # Classify by tags
                cat = "general"
                if any(t in tags for t in ["russian", "ru", "русский"]):
                    cat = "ru"
                elif any(t in tags for t in ["code", "programming", "python", "js"]):
                    cat = "code"
                elif any(t in tags for t in ["design", "svg", "html", "css", "ui", "graphic"]):
                    cat = "design"
                elif any(t in tags for t in ["math", "mathematics"]):
                    cat = "math"
                elif any(t in tags for t in ["wikipedia", "wiki", "knowledge", "science"]):
                    cat = "knowledge"

                # Get a file to download
                files = []
                for s in ds.get("siblings", []):
                    fn = s.get("rfilename", "")
                    if any(fn.endswith(ext) for ext in [".jsonl", ".json", ".parquet"]):
                        files.append(fn)
                    if len(files) >= 3:
                        break

                if files:
                    new_entries.append({
                        "cat": cat, "ds": ds_id, "files": [files[0]],
                        "desc": ds.get("description", "")[:80],
                        "est": f"{downloads}dl", "priority": 5
                    })
                    new_count += 1

            if new_entries:
                # Add to catalog
                cat = json.loads(cat_path.read_text("utf-8"))
                cat.extend(new_entries)
                cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2), "utf-8")
                for e in new_entries[:5]:
                    print(f"    + {e['ds']} ({e['cat']})")

            return new_count
        except Exception as e:
            print(f"    ERROR: {e}")
            return 0

    # ---- Learn from logs (own experience) ----
    def learn_from_logs(self):
        """Mirro учится на своих же вызовах — повторно использует лучшие."""
        log_path = LOG_DIR / "calls.jsonl"
        if not log_path.exists():
            return 0

        lines = log_path.read_text("utf-8").strip().split("\n")
        if len(lines) < 10:
            return 0

        # Sample successful calls and save as examples
        examples = []
        for line in lines[-100:]:
            try:
                entry = json.loads(line)
                if entry.get("success") and entry.get("prompt_len", 0) > 20:
                    examples.append({
                        "instruction": f"[Mirro self-log] Task: {entry.get('cluster','?')}",
                        "input": f"provider={entry.get('provider','?')} latency={entry.get('latency_ms',0)}ms",
                        "output": f"Call #{entry.get('ts','?')} — cluster: {entry.get('cluster')}, "
                                  f"tokens: {entry.get('tokens',0)}, latency: {entry.get('latency_ms',0)}ms"
                    })
            except Exception:
                pass

        if examples:
            cluster = "general"
            out_path = LEARN_DIR / f"selflog_{cluster}.jsonl"
            with open(out_path, "a", encoding="utf-8") as f:
                for ex in examples:
                    f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            return len(examples)
        return 0

    # ---- Wikipedia (new articles) ----
    def learn_from_wikipedia(self):
        """Скачивает свежие статьи из Wikipedia RU."""
        print("  📖 Wikipedia RU: checking recent changes...")
        try:
            # Random articles for variety
            url = "https://ru.wikipedia.org/w/api.php?action=query&list=random&rnnamespace=0&rnlimit=5&format=json"
            data = self._fetch_json(url)
            if not data or "query" not in data:
                return 0

            examples = []
            for page in data["query"].get("random", []):
                title = page.get("title", "")
                if not title:
                    continue
                # Get the article content
                content_url = (
                    "https://ru.wikipedia.org/w/api.php"
                    f"?action=query&titles={urllib.request.quote(title)}"
                    "&prop=extracts&exintro&explaintext&format=json"
                )
                content_data = self._fetch_json(content_url)
                if not content_data:
                    continue
                pages = content_data.get("query", {}).get("pages", {})
                for pid, info in pages.items():
                    if pid == "-1":
                        continue
                    text = info.get("extract", "")
                    if text and len(text) > 200:
                        examples.append({
                            "instruction": f"Расскажи про: {title}",
                            "input": "",
                            "output": text[:4000],
                        })

            if examples:
                out_path = LEARN_DIR / "wikipedia_ru.jsonl"
                with open(out_path, "a", encoding="utf-8") as f:
                    for ex in examples:
                        f.write(json.dumps(ex, ensure_ascii=False) + "\n")
                return len(examples)
            return 0
        except Exception as e:
            print(f"    ERROR: {e}")
            return 0

    # ---- Collect Mirro's own skills as knowledge ----
    def build_skills_knowledge(self):
        """Save Mirro's own skills as a permanent knowledge file."""
        out_path = LEARN_DIR / "mirro_own_skills.jsonl"
        count = 0
        with open(out_path, "w", encoding="utf-8") as f:
            for skill in MIRRO_SKILLS:
                entry = {
                    "instruction": f"Как сделать/создать: {skill['skill']}",
                    "input": f"domain={skill['domain']}",
                    "output": f"Инструкция: {skill['desc']}",
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                count += 1

        # Also save them in the knowledge cluster system
        proc_dir = MIRRO / "data" / "processed"
        for domain in set(s["domain"] for s in MIRRO_SKILLS):
            cluster_file = proc_dir / f"{domain}.jsonl"
            with open(cluster_file, "a", encoding="utf-8") as f:
                for skill in MIRRO_SKILLS:
                    if skill["domain"] == domain:
                        entry = {
                            "instruction": skill["skill"],
                            "input": "",
                            "output": skill["desc"],
                        }
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"  🧠 Mirro: {count} навыков записано в knowledge base")
        return count

    # ---- Main learning loop ----
    def learn_once(self):
        """Run one full learning cycle."""
        self.session += 1
        print(f"\n{'='*60}")
        print(f"🧬 Mirro Self-Learning #{self.session}")
        print(f"{'='*60}")

        total = 0

        # 1. HuggingFace trending
        n = self.learn_from_hf_trending()
        total += n
        print(f"  → {n} новых датасетов найдено")

        # 2. Own logs
        n = self.learn_from_logs()
        total += n
        print(f"  → {n} примеров из собственных вызовов")

        # 3. Wikipedia
        n = self.learn_from_wikipedia()
        total += n
        print(f"  → {n} статей из Wikipedia")

        # 4. Build skills knowledge (run once)
        skills_meta = LEARN_META if LEARN_META.exists() else None
        if not self.meta.get("skills_built"):
            self.build_skills_knowledge()
            self.meta["skills_built"] = True
            total += len(MIRRO_SKILLS)

        self.meta["total_sessions"] += 1
        self.meta["total_learned"] += total
        self.meta["last_run"] = datetime.utcnow().isoformat()
        self._save_meta()

        print(f"\n✅ Learning cycle complete: +{total} новых знаний")
        print(f"   Всего знаний: {self.meta['total_learned']}")
        return total

    def start_loop(self, interval_hours=12):
        """Run learning forever every N hours."""
        print(f"🔄 Self-learning loop every {interval_hours}h")
        print("   (learn_once for single run, Ctrl+C to stop)\n")
        self.learn_once()
        while True:
            print(f"\n⏰ Next run in {interval_hours}h ({datetime.now() + timedelta(hours=interval_hours):%H:%M})")
            time.sleep(interval_hours * 3600)
            self.learn_once()


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"

    learner = SelfLearner()

    if mode == "once":
        print("🧬 Mirro Self-Learning (single run)")
        learner.learn_once()
    elif mode == "loop":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 12
        learner.start_loop(hours)
    elif mode == "skills":
        n = learner.build_skills_knowledge()
        print(f"✅ {n} навыков сохранено")
    else:
        print("Usage: python self_learn.py [once|loop|skills]")