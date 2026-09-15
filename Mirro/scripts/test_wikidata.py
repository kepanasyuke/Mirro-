# -*- coding: utf-8 -*-
"""Test Wikidata as knowledge source: search -> qid -> russian description."""
import json, urllib.request, urllib.parse

UA = "Mirro/0.2 (personal test)"

def fetch(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))

def wikidata_search(q):
    url = ("https://www.wikidata.org/w/api.php?action=wbsearchentities"
           f"&search={urllib.parse.quote(q)}&language=ru&uselang=ru&format=json&limit=3")
    d = fetch(url)
    return d.get("search", [])

def wikidata_desc(qid, lang="ru"):
    url = ("https://www.wikidata.org/w/api.php?action=wbgetentities"
           f"&ids={qid}&props=descriptions|labels|aliases&languages={lang}&format=json")
    d = fetch(url)
    ent = d.get("entities", {}).get(qid, {})
    desc = ent.get("descriptions", {}).get(lang, {}).get("value", "")
    label = ent.get("labels", {}).get(lang, {}).get("value", "")
    aliases = ent.get("aliases", {}).get(lang, [])
    return label, desc, [a["value"] for a in aliases][:3]

for q in ["Александр Пушкин", "Налог на добавленную стоимость", "Python язык", "Ломоносов"]:
    try:
        results = wikidata_search(q)
        print(f"Q: {q} → {len(results)} результатов")
        for r in results[:2]:
            qid = r.get("id", "")
            lbl, desc, aliases = wikidata_desc(qid)
            print(f"  {qid} {lbl}: {desc[:100]} (ал. {aliases})")
        print()
    except Exception as e:
        print(f"Q: {q} → ERROR {e}")