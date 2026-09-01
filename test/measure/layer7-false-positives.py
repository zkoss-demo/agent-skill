#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["lxml"]
# ///
"""Layer 7 false-positive sweep over an external corpus.

Layer 7 is the only new rule that can accuse correct code, so its precision is
the number that decides whether it should exist.  This pairs each .zul with the
controller its own markup names (apply= / viewModel=), resolves the FQCN to a
file under any src/main/java root in the corpus, and runs the cross-check.
Every finding on ZK's own documentation examples is a candidate false positive.
"""
import re, subprocess, sys
from pathlib import Path
from lxml import etree

V = Path(__file__).resolve().parent.parent.parent / "skills" / "zul-writer" / "scripts" / "validate-zul.py"
root = Path(sys.argv[1])

java_index: dict[str, Path] = {}
for j in root.rglob("*.java"):
    parts = j.parts
    for i, p in enumerate(parts):
        if p == "java" and i >= 2 and parts[i-1] == "main" and parts[i-2] == "src":
            fqcn = ".".join(parts[i+1:])[:-len(".java")]
            java_index[fqcn] = j
            break

ZUL_NS = "{http://www.zkoss.org/2005/zul}"
pairs, unresolved = [], 0
for z in sorted(root.rglob("*.zul")):
    try:
        tree = etree.parse(str(z))
    except etree.XMLSyntaxError:
        continue
    for el in tree.iter():
        if not isinstance(el.tag, str):
            continue
        for a in ("apply", "viewModel"):
            v = el.get(a)
            if not v:
                continue
            m = re.search(r"[\w.]+\.[A-Z]\w*", v)
            if not m:
                continue
            fq = m.group(0)
            if fq in java_index:
                pairs.append((z, java_index[fq]))
            else:
                unresolved += 1
            break

seen, findings, wired = set(), [], 0
for z, j in pairs:
    if (z, j) in seen:
        continue
    seen.add((z, j))
    wired += len(re.findall(r"@Wire\b", j.read_text(errors="ignore")))
    r = subprocess.run([sys.executable, str(V), str(z), "--controller", str(j)],
                       capture_output=True, text=True)
    m = re.search(r"Layer 7: Controller Cross-Check\.\.\. (✓ PASS|✗ FAIL)(.*?)(?=\n=|\Z)",
                  r.stdout, re.S)
    if m and m.group(1).startswith("✗"):
        findings.append((z, j, m.group(2).strip()))

print(f"{len(seen)} zul/controller pairs resolved ({unresolved} FQCN references "
      f"had no file in this corpus), {wired} @Wire annotations in those controllers")
print(f"Layer 7 FIRED on {len(findings)} pair(s):")
for z, j, msg in findings:
    print(f"  {z.name}  +  {j.name}\n     {msg}")
