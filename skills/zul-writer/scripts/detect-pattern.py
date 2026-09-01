#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
ZK Pattern Detector

Answers one question, for Step 1 question 3: does this project already use MVC
or MVVM? A project that is unanimous is evidence; a project that is split has no
answer to give, and saying so is more useful than picking the larger pile.

Reads the ZUL side only. Java is deliberately not consulted: a ViewModel is an
ordinary POJO with no marker a scan can trust -- `@Init` is optional, so counting
it misses every ViewModel written without one, while counting `Composer`
subclasses picks up base classes and helpers that were never applied to a page.
The ZUL side is exact by comparison, because both patterns declare themselves in
an attribute: MVC applies a Composer, MVVM sets a ViewModel.

Output is one `KEY: value` line per fact, then the filenames behind each count:

    SCANNED: 23 .zul files under .
    PATTERN: mixed (MVC 6, MVVM 2)
    USE: mvc -- the project uses both, so it has no single answer to give
    MVC: 6 files
      src/main/webapp/orders.zul
      ...

No usage ping: this runs inside a skill invocation that already reports itself
through validate-zul.py and preview-zul.py, and a third emitter would silently
change what the usage count means.
"""

import argparse
import re
import sys
from pathlib import Path

# Build outputs copy the whole webapp, so scanning them counts every page twice.
SKIP_DIRS = {"target", "build", "out", "node_modules", ".git", ".idea", ".gradle"}

# The MVVM binder. Setting `viewModel` applies it for you on ZK 8+, but plenty of
# pages still name it outright, and reading that as "a Composer, therefore MVC"
# would file a pure MVVM page under its opposite.
BIND_COMPOSER = "org.zkoss.bind.BindComposer"

COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
# `(?<![\w-])` so a hyphenated attribute such as `data-apply` is not a match.
APPLY = re.compile(r"(?<![\w-])apply\s*=\s*([\"'])(.*?)\1", re.DOTALL)
VIEW_MODEL = re.compile(r"(?<![\w-])viewModel\s*=")


def signals(zul: Path):
    """(mvc, mvvm) -- what this one page declares. A page may declare both."""
    text = COMMENT.sub("", zul.read_text(encoding="utf-8", errors="replace"))
    mvc = mvvm = False
    for _, value in APPLY.findall(text):
        for name in value.split(","):          # `apply` takes a comma-separated list
            name = name.strip()
            if name == BIND_COMPOSER:
                mvvm = True
            elif name:
                mvc = True
    if VIEW_MODEL.search(text):
        mvvm = True
    return mvc, mvvm


def collect(root: Path):
    found = []
    for zul in sorted(root.rglob("*.zul")):
        if SKIP_DIRS & set(zul.relative_to(root).parts[:-1]):
            continue
        try:
            found.append((zul, signals(zul)))
        except OSError as failure:
            print(f"SKIPPED: {zul} ({failure})", file=sys.stderr)
    return found


def show(label, files, root, limit):
    """One group, with its filenames. An elided tail is stated, never silent."""
    if not files:
        return
    print(f"{label}: {len(files)} file" + ("" if len(files) == 1 else "s"))
    shown = files if limit == 0 else files[:limit]
    for zul in shown:
        print(f"  {zul.relative_to(root)}")
    if len(files) > len(shown):
        print(f"  ... and {len(files) - len(shown)} more (--list 0 for all)")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Detect whether a project's ZUL pages use MVC or MVVM.")
    parser.add_argument("root", nargs="?", default=".",
                        help="project root to scan (default: the current directory)")
    parser.add_argument("--list", type=int, default=10, metavar="N",
                        help="filenames to print per group (default: 10; 0 prints all)")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 2

    scanned = collect(root)
    mvc_only = [z for z, (mvc, mvvm) in scanned if mvc and not mvvm]
    mvvm_only = [z for z, (mvc, mvvm) in scanned if mvvm and not mvc]
    both = [z for z, (mvc, mvvm) in scanned if mvc and mvvm]

    mvc_total = len(mvc_only) + len(both)
    mvvm_total = len(mvvm_only) + len(both)

    if both or (mvc_total and mvvm_total):
        verdict = "mixed"
        use = "mvc -- the project uses both, so it has no single answer to give"
    elif mvc_total:
        verdict = "mvc"
        use = "mvc -- every page here that names a controller is MVC"
    elif mvvm_total:
        verdict = "mvvm"
        use = "mvvm -- every page here that names a controller is MVVM"
    else:
        verdict = "none"
        use = "mvc -- no page here names a controller, so the default applies"

    print(f"SCANNED: {len(scanned)} .zul file" + ("" if len(scanned) == 1 else "s")
          + f" under {root}")
    print(f"PATTERN: {verdict} (MVC {mvc_total}, MVVM {mvvm_total})")
    print(f"USE: {use}")
    show("MVC", mvc_only, root, args.list)
    show("MVVM", mvvm_only, root, args.list)
    if both:
        show("BOTH", both, root, args.list)
        print("  (these pages mix the two patterns; do not copy their shape)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
