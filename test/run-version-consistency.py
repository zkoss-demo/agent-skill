#!/usr/bin/env python3
"""
Version consistency check.

The skill's version is declared once, in SKILL.md's frontmatter, and the scripts read
it from there at runtime through skills/zul-writer/scripts/_skill_meta.py.

marketplace.json cannot read it: it sits at the repo root, outside the skill directory,
and no install ships it. This check is the only thing holding it in step -- and the only
thing that would notice a version literal being written back into a script.

Four assertions:

  1. SKILL.md's frontmatter declares a parseable version.
  2. marketplace.json's zul-writer entry carries that same version.
  3. _skill_meta.SKILL_VERSION resolves to it -- i.e. the runtime path really works,
     not just the file contents.
  4. No script has re-introduced a hard-coded SKILL_VERSION literal.

Exit code 0 = consistent, 1 = drift. Run locally with:
    python3 test/run-version-consistency.py
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "zul-writer"
SKILL_MD = SKILL_DIR / "SKILL.md"
SCRIPTS_DIR = SKILL_DIR / "scripts"
MARKETPLACE = REPO_ROOT / "marketplace.json"
SKILL_ID = "zul-writer"

# Parsed independently of _skill_meta on purpose: a check that reuses the code under
# test agrees with it even when both are wrong.
FRONTMATTER = re.compile(r'\A---\s*?\n(.*?)^---\s*?$', re.S | re.M)
VERSION_LINE = re.compile(r'^\s*version:\s*["\']?([0-9][^"\'\s]*)', re.M)
HARDCODED = re.compile(r'^\s*SKILL_VERSION\s*=\s*["\']', re.M)


def skill_md_version() -> str | None:
    frontmatter = FRONTMATTER.search(SKILL_MD.read_text(encoding="utf-8")[:4096])
    if frontmatter is None:
        return None
    match = VERSION_LINE.search(frontmatter.group(1))
    return match.group(1) if match else None


def marketplace_version() -> str | None:
    data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    for skill in data.get("skills", []):
        if skill.get("id") == SKILL_ID:
            return skill.get("version")
    return None


def runtime_version() -> str:
    spec = importlib.util.spec_from_file_location(
        "_skill_meta", SCRIPTS_DIR / "_skill_meta.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SKILL_VERSION


def main() -> int:
    failures = []

    declared = skill_md_version()
    if declared is None:
        print(f"FAIL   {SKILL_MD.relative_to(REPO_ROOT)} declares no parseable "
              f"metadata.version in its frontmatter")
        return 1
    print(f"ok     SKILL.md declares version {declared}")

    listed = marketplace_version()
    if listed != declared:
        failures.append(
            f"marketplace.json lists {listed!r} for '{SKILL_ID}', SKILL.md declares "
            f"{declared!r}. These two are not linked at runtime -- edit both together.")
        print(f"FAIL   marketplace.json: {listed!r} != {declared!r}")
    else:
        print(f"ok     marketplace.json agrees ({listed})")

    resolved = runtime_version()
    if resolved != declared:
        failures.append(
            f"_skill_meta.SKILL_VERSION resolved to {resolved!r}, not {declared!r}. "
            f"The scripts would report that to the usage endpoint.")
        print(f"FAIL   _skill_meta.SKILL_VERSION: {resolved!r} != {declared!r}")
    else:
        print(f"ok     scripts resolve {resolved} at runtime")

    for script in sorted(SCRIPTS_DIR.glob("*.py")):
        if script.name == "_skill_meta.py":
            continue
        if HARDCODED.search(script.read_text(encoding="utf-8")):
            failures.append(
                f"{script.name} assigns SKILL_VERSION a literal. Import it from "
                f"_skill_meta instead, so a release bump stays a one-line edit.")
            print(f"FAIL   {script.name} hard-codes a SKILL_VERSION literal")

    print("-" * 60)
    if failures:
        print("Result: ✗ version drift")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("Result: ✓ every version site agrees")
    return 0


if __name__ == "__main__":
    sys.exit(main())
