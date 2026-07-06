#!/usr/bin/env python3
"""
ZUL regression net for CI (finding F1).

Runs the skill's own validator (skills/zul-writer/scripts/validate-zul.py)
over four corpora and enforces each corpus's convention:

    test/valid/**                             -> must PASS
    test/wrong/**                             -> must FAIL
    skills/zul-writer/assets/*.zul            -> must PASS
    zulwriter-showcase/src/main/webapp/*.zul  -> must PASS

Files listed in test/known-failures.txt are quarantined: their current
violation is expected (a fix is pending, see finding B1). The net fails on
*drift*, not on the known backlog:

  * REGRESSION      — a non-quarantined file breaks its convention.
  * STALE QUARANTINE — a quarantined file now conforms; remove it from the list.

Exit code 0 = clean, 1 = drift detected. Run locally with:
    python3 test/run-regression.py
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = REPO_ROOT / "skills" / "zul-writer" / "scripts" / "validate-zul.py"
QUARANTINE_FILE = REPO_ROOT / "test" / "known-failures.txt"

# (directory relative to repo root, glob, expected outcome: "pass" | "fail")
CORPUS = [
    ("test/valid", "*.zul", "pass"),
    ("test/wrong", "*.zul", "fail"),
    ("skills/zul-writer/assets", "*.zul", "pass"),
    ("zulwriter-showcase/src/main/webapp", "*.zul", "pass"),
]


def load_quarantine() -> set:
    if not QUARANTINE_FILE.exists():
        return set()
    paths = set()
    for line in QUARANTINE_FILE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            paths.add(line)
    return paths


def validate(file_path: Path) -> bool:
    """Return True if the validator passes (exit 0) for this file."""
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(file_path)],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def main() -> int:
    quarantine = load_quarantine()
    seen_quarantine = set()
    regressions = []
    stale = []
    checked = 0

    for rel_dir, glob, expected in CORPUS:
        directory = REPO_ROOT / rel_dir
        for file_path in sorted(directory.glob(glob)):
            checked += 1
            rel = file_path.relative_to(REPO_ROOT).as_posix()
            passed = validate(file_path)
            conforms = passed if expected == "pass" else not passed

            if rel in quarantine:
                seen_quarantine.add(rel)
                if conforms:
                    stale.append((rel, expected))
                    print(f"STALE  {rel} (now conforms; remove from known-failures.txt)")
                else:
                    print(f"known  {rel} (quarantined; expected {expected} still failing)")
                continue

            if conforms:
                print(f"ok     {rel} ({expected})")
            else:
                got = "pass" if passed else "fail"
                regressions.append((rel, expected, got))
                print(f"FAIL   {rel} (expected {expected}, got {got})")

    # Quarantine entries that no longer match any file — path typo or a
    # deleted file. Flag so the list stays honest.
    orphans = sorted(quarantine - seen_quarantine)
    for rel in orphans:
        print(f"ORPHAN {rel} (in known-failures.txt but no such file)")

    print("-" * 60)
    print(f"Checked {checked} files | "
          f"{len(regressions)} regression(s), {len(stale)} stale, {len(orphans)} orphan(s), "
          f"{len(seen_quarantine)} still quarantined")

    if regressions or stale or orphans:
        print("Result: ✗ drift detected")
        return 1
    print("Result: ✓ corpus matches expectations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
