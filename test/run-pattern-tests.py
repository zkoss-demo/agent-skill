#!/usr/bin/env python3
"""
Contract checks for skills/zul-writer/scripts/detect-pattern.py.

The detector answers Step 1's question 3 when nobody is there to answer it, and
it only gets to override the MVC default when a project is unanimous. So the
checks that matter are the ones that decide unanimity: what counts as an MVC
signal, what counts as an MVVM one, and what is not a signal at all. A regex
tweak that quietly reclassifies `org.zkoss.bind.BindComposer` would point every
MVVM project at MVC without saying a word, which is exactly what this catches.

No browser, no network, no build. Run with:
    python3 test/run-pattern-tests.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DETECTOR = REPO_ROOT / "skills" / "zul-writer" / "scripts" / "detect-pattern.py"

MVC_PAGE = '<zk>\n  <window apply="com.foo.OrderComposer"/>\n</zk>\n'
MVVM_PAGE = ("<zk>\n  <window viewModel=\"@id('vm') @init('com.foo.OrderVM')\"/>\n</zk>\n")
BIND_COMPOSER_PAGE = '<zk>\n  <div apply="org.zkoss.bind.BindComposer"/>\n</zk>\n'
BOTH_PAGE = ("<zk>\n  <window apply=\"com.foo.OrderComposer\""
             " viewModel=\"@id('vm') @init('com.foo.OrderVM')\"/>\n</zk>\n")
NO_SIGNAL_PAGE = ('<zk>\n  <!-- an old version applied com.foo.Legacy here -->\n'
                  '  <div data-apply="not-an-attribute"/>\n</zk>\n')


def run(files):
    """Write `files` (relative path -> text) into a temp project and detect."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, text in files.items():
            page = root / name
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(text, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(DETECTOR), str(root)],
            capture_output=True, text=True, timeout=60)
    return result.stdout


def check_unanimous_mvc_overrides_nothing():
    out = run({"a.zul": MVC_PAGE, "sub/b.zul": MVC_PAGE})
    assert "PATTERN: mvc (MVC 2, MVVM 0)" in out, out
    assert "USE: mvc" in out, out


def check_unanimous_mvvm_wins_over_the_default():
    """The whole reason the detector exists: an all-MVVM project must not be
    handed an MVC page just because MVC is the fallback."""
    out = run({"a.zul": MVVM_PAGE, "sub/b.zul": MVVM_PAGE})
    assert "PATTERN: mvvm (MVC 0, MVVM 2)" in out, out
    assert "USE: mvvm" in out, out


def check_a_split_project_falls_back_to_mvc():
    out = run({"a.zul": MVC_PAGE, "b.zul": MVVM_PAGE})
    assert "PATTERN: mixed (MVC 1, MVVM 1)" in out, out
    assert "USE: mvc" in out, out


def check_a_page_using_both_is_named_as_such():
    out = run({"a.zul": BOTH_PAGE})
    assert "PATTERN: mixed (MVC 1, MVVM 1)" in out, out
    assert "BOTH: 1 file" in out, out


def check_bind_composer_reads_as_mvvm():
    """`apply="org.zkoss.bind.BindComposer"` is MVVM's own binder, not a
    user-written Composer. Counting it as MVC inverts the verdict."""
    out = run({"a.zul": BIND_COMPOSER_PAGE})
    assert "PATTERN: mvvm (MVC 0, MVVM 1)" in out, out


def check_comments_and_lookalike_attributes_are_not_signals():
    out = run({"a.zul": NO_SIGNAL_PAGE})
    assert "PATTERN: none (MVC 0, MVVM 0)" in out, out
    assert "USE: mvc" in out, out


def check_build_output_is_not_counted_twice():
    """A build copies the whole webapp into target/, so scanning it would double
    every page and could invent a majority that does not exist."""
    out = run({"web/a.zul": MVC_PAGE, "target/web/a.zul": MVC_PAGE})
    assert "SCANNED: 1 .zul file under" in out, out
    assert "PATTERN: mvc (MVC 1, MVVM 0)" in out, out


CHECKS = [
    ("unanimous MVC     ", check_unanimous_mvc_overrides_nothing),
    ("unanimous MVVM    ", check_unanimous_mvvm_wins_over_the_default),
    ("split project     ", check_a_split_project_falls_back_to_mvc),
    ("one page, both    ", check_a_page_using_both_is_named_as_such),
    ("BindComposer      ", check_bind_composer_reads_as_mvvm),
    ("comments/lookalike", check_comments_and_lookalike_attributes_are_not_signals),
    ("build output      ", check_build_output_is_not_counted_twice),
]


def main():
    failed = 0
    for label, check in CHECKS:
        try:
            check()
            print(f"  ✓ {label}")
        except AssertionError as failure:
            failed += 1
            print(f"  ✗ {label} — {failure}")
    print(f"\n{len(CHECKS)} checks | {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
