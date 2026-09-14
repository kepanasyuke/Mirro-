#!/usr/bin/env python3
"""Test Mirro AI index build speed."""
import time, sys
t0 = time.time()
sys.path.insert(0, r'D:\Mirro')
from scripts.generative_engine import MirroAI
ai = MirroAI()
elapsed = time.time() - t0
st = ai.status()
print("Index built in {:.1f}s".format(elapsed))
print("Examples: {}".format(st["indexed"]))
print("Terms: {}".format(st["unique_terms"]))