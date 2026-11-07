# -*- coding: utf-8 -*-
"""Mirro CLI — внешние вызовы Mirro из консоли/скриптов.

Позволяет обращаться к локальному серверу Mirro без браузера:
   python scripts/mirro_cli.py ask "что такое нейрон"
   python scripts/mirro_cli.py search "налог на добавленную стоимость"
   python scripts/mirro_cli.py graph "память"
   python scripts/mirro_cli.py health
   python scripts/mirro_cli.py chat [--json]

Работает через REST API сервера (/v1/chat/completions, /v1/search, /v1/graph,
/health). Один return-путь, вывод в stdout.
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.parse

DEFAULT_API = os.environ.get("MIRRO_API", "http://127.0.0.1:3443")
DEFAULT_TOKEN = os.environ.get("MIRRO_TOKEN", "test-secret-123")


def _request(path, method="GET", payload=None):
    url = DEFAULT_API + path
    headers = {"Authorization": "Bearer " + DEFAULT_TOKEN}
    data = None
    if method == "POST" and payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def _cmd_ask(args):
    q = " ".join(args.query)
    body = {"messages": [{"role": "user", "content": q}]}
    d = _request("/v1/chat/completions", method="POST", payload=body)
    msg = d.get("choices", [{}])[0].get("message", {})
    out = msg.get("content") or "Нет ответа"
    if args.json:
        print(json.dumps({"query": q, "content": out,
                          "source": msg.get("source"),
                          "confidence": msg.get("confidence")}, ensure_ascii=False))
    else:
        print(out)
    return 0


def _cmd_search(args):
    q = " ".join(args.query)
    d = _request("/v1/search?q=" + urllib.parse.quote(q) + "&top=" + str(args.top))
    results = d.get("results", [])
    if args.json:
        print(json.dumps(d, ensure_ascii=False))
    else:
        print(f"Найдено {d.get('count', 0)} результатов:")
        for r in results:
            print(f"  [{r['cluster']}] {r['question'][:50]} → {r['answer'][:80]} (score {r['score']})")
    return 0


def _cmd_graph(args):
    concept = " ".join(args.concept) if args.concept else ""
    path = "/v1/graph"
    if concept:
        path += "?concept=" + urllib.parse.quote(concept)
    d = _request(path)
    if args.json:
        print(json.dumps(d, ensure_ascii=False))
    else:
        print(f"Граф: {d.get('nodes')} узлов, {d.get('edges')} рёбер")
        if d.get("concept"):
            print(f"Связи «{d['concept']}»:")
            for ln in d.get("links", []):
                print("  " + ln)
        else:
            print("Центральные понятия:", ", ".join(d.get("central", [])))
    return 0


def _cmd_health(args):
    d = _request("/health")
    if args.json:
        print(json.dumps(d, ensure_ascii=False))
    else:
        kg = d.get("algorithms", {}).get("knowledge_graph", {})
        print(f"Mirro OK: {d.get('total_calls')} вызовов, граф {kg.get('nodes')} узлов / {kg.get('edges')} рёбер")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Mirro CLI")
    ap.add_argument("--json", action="store_true", help="вывод в JSON (для скриптов)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_ask = sub.add_parser("ask", help="задать вопрос Mirro (chat)")
    p_ask.add_argument("query", nargs="+")

    p_chat = sub.add_parser("chat", help="то же, что ask (обратная совместимость)")
    p_chat.add_argument("query", nargs="+")

    p_search = sub.add_parser("search", help="поиск по базе знаний")
    p_search.add_argument("query", nargs="+")
    p_search.add_argument("--top", type=int, default=5)

    p_graph = sub.add_parser("graph", help="данные графа знаний")
    p_graph.add_argument("concept", nargs="*")

    sub.add_parser("health", help="проверить здоровье сервера")

    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "ask" or args.cmd == "chat":
        return _cmd_ask(args)
    if args.cmd == "search":
        return _cmd_search(args)
    if args.cmd == "graph":
        return _cmd_graph(args)
    if args.cmd == "health":
        return _cmd_health(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())