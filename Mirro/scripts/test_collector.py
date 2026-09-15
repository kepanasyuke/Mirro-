#!/usr/bin/env python3
"""Quick test of collector API endpoints."""
import sys, json, urllib.request
sys.path.insert(0, r'D:\Mirro\scripts')

# Test Openverse
# Test Wikimedia (confirmed working)
print("Testing Wikimedia Commons...")
try:
    import urllib.request, json
    req = urllib.request.Request(
        'https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=poster+design&srnamespace=6&srlimit=3&format=json',
        headers={'User-Agent': 'MirroCollector/1.0'}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    d = json.loads(resp.read())
    hits = len(d.get('query', {}).get('search', []))
    print("  OK: {} results".format(hits))
except Exception as e:
    print("  FAIL: {}".format(e))

# Test Openverse with email header (required)
print("\nTesting Openverse...")
for q in ["logo+design", "poster+design", "ui+interface"]:
    try:
        req = urllib.request.Request(
            'https://api.openverse.org/v1/images?q={}&page_size=3'.format(q),
            headers={'User-Agent': 'MirroCollector/1.0 (mirro@local)'}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        results = data.get('results', [])
        print("  {}: {} results".format(q, len(results)))
        for img in results[:1]:
            print("    {} :: {}".format(img.get('title','?')[:40], img.get('url','')[:60]))
    except Exception as e:
        print("  {}: FAIL {}".format(q, e))

print("\nDone.")

print("\nAll tests done.")