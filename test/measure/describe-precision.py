#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["lxml"]
# ///
"""
Wide precision sweep for `validate-zul.py --describe`, over an external corpus.

Same question as measure-describe-precision.py, but with a denominator large
enough to mean something, and findings weighted by how many files use the form.
A wrong answer about a form used in 40 files matters more than one about a form
used once.

Corpus: DOC/zkbooks (ZK's own documentation examples).  Caveat recorded in
doc/knowledge-roadmap.md #4: that repo is on branch 11.0.0 while the schema
targets ZK 10, so a genuine ZK 11 addition will show up here as a wrong answer.
That is why findings are printed with their usage counts and triaged by hand
rather than reduced to a single pass/fail.

Usage: measure-describe-wide.py <corpus-root>
"""

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from lxml import etree

REPO = Path(__file__).resolve().parent.parent.parent
VALIDATOR = REPO / "skills" / "zul-writer" / "scripts" / "validate-zul.py"
XSD = REPO / "skills" / "zul-writer" / "assets" / "zul.xsd"
ZUL_NS = "http://www.zkoss.org/2005/zul"

NOT_ACCEPTED = re.compile(r"^\s+(\S+): NOT accepted", re.M)


def collect(root: Path):
    """element -> attr -> number of files using that pair; plus element file counts."""
    pairs: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    el_files: dict[str, int] = defaultdict(int)
    parsed = failed = skipped_attrs = 0
    parser = etree.XMLParser(recover=False, resolve_entities=False)
    files = sorted(root.rglob("*.zul"))
    for path in files:
        try:
            tree = etree.parse(str(path), parser)
        except etree.XMLSyntaxError:
            failed += 1
            continue
        parsed += 1
        seen_pairs, seen_els = set(), set()
        for el in tree.iter():
            if not isinstance(el.tag, str):
                continue
            if "}" in el.tag:
                uri, local = el.tag[1:].split("}", 1)
                if uri != ZUL_NS:
                    continue
            else:
                local = el.tag
            seen_els.add(local)
            for name in el.attrib:
                if "}" in name or ":" in name:
                    skipped_attrs += 1
                    continue
                seen_pairs.add((local, name))
        for e in seen_els:
            el_files[e] += 1
        for e, a in seen_pairs:
            pairs[e][a] += 1
    return pairs, el_files, len(files), parsed, failed, skipped_attrs


def ask(component: str, attrs: list[str]) -> str:
    cmd = [sys.executable, str(VALIDATOR), "--xsd", str(XSD), "--describe", component]
    for a in attrs:
        cmd += ["--attr", a]
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def main() -> int:
    root = Path(sys.argv[1])
    pairs, el_files, total, parsed, failed, skipped = collect(root)
    n_pairs = sum(len(v) for v in pairs.values())
    print(f"corpus {root}")
    print(f"  {parsed}/{total} .zul files parsed ({failed} unparseable), "
          f"{len(pairs)} distinct elements, {n_pairs} distinct (element, attribute) pairs, "
          f"{skipped} namespaced attributes skipped\n")

    missing, rejected = [], []
    for component in sorted(pairs):
        attrs = sorted(pairs[component])
        out = ask(component, attrs)
        if "NOT FOUND in the bundled schema" in out:
            missing.append((el_files[component], component))
            continue
        for m in NOT_ACCEPTED.finditer(out):
            attr = m.group(1)
            rejected.append((pairs[component][attr], component, attr))

    print(f"ELEMENTS REPORTED NOT FOUND: {len(missing)} "
          f"of {len(pairs)} ({len(missing)/max(len(pairs),1)*100:.1f}%)"
          "   [files using it, element]")
    for count, component in sorted(missing, reverse=True):
        print(f"  {count:4d}  <{component}>")

    print(f"\nATTRIBUTES REPORTED NOT ACCEPTED: {len(rejected)} "
          f"of {n_pairs} pairs ({len(rejected)/max(n_pairs,1)*100:.2f}%)"
          "   [files using it, element, attribute]")
    for count, component, attr in sorted(rejected, reverse=True):
        print(f"  {count:4d}  <{component} {attr}=...>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
