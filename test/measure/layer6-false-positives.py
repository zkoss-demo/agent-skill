#!/usr/bin/env python3
"""Layer 6 false-positive sweep: run the validator over an external corpus and
count only Layer 6 verdicts.  Other layers will legitimately fail on a corpus a
major version ahead of the schema; Layer 6 reads markup semantics only, so a
Layer 6 failure on ZK's own documentation examples is a false positive."""
import subprocess, sys, re
from pathlib import Path
V = Path(__file__).resolve().parent.parent.parent / "skills" / "zul-writer" / "scripts" / "validate-zul.py"
root = Path(sys.argv[1])
files = sorted(root.rglob("*.zul"))
fired, absent, ran = [], 0, 0
for f in files:
    r = subprocess.run([sys.executable, str(V), str(f)], capture_output=True, text=True)
    m = re.search(r"Layer 6: Runtime Semantics\.\.\. (✓ PASS|✗ FAIL)(.*?)(?=\nLayer |\n=|\Z)", r.stdout, re.S)
    if not m:
        absent += 1
        continue
    ran += 1
    if m.group(1).startswith("✗"):
        fired.append((f, m.group(2).strip()))
print(f"{len(files)} files; Layer 6 executed on {ran}, not reached on {absent} "
      f"(earlier layer aborted the run)")
print(f"Layer 6 FIRED on {len(fired)} file(s):")
for f, msg in fired:
    print(f"  {f}\n     {msg}")
