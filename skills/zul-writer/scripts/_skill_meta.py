"""The skill's version, read from the one file that declares what the skill is.

`SKILL.md`'s `metadata.version` is the source of truth. Every script that reports a
version imports it from here, so cutting a release edits the frontmatter and nothing
else inside the skill directory. Before this, each script carried its own literal and
a bump had to touch all of them; changing one alone reported a version that was never
released.

`marketplace.json` deliberately cannot participate. It lives at the repo root, outside
`skills/zul-writer/`, and no install ships it -- `npx skills add`, a symlink of the
skill directory, and `.github/skills/` all move the skill directory alone. A script
reading it would find nothing on every real install. It is held in step by
`test/run-version-consistency.py` instead.
"""

import re
from pathlib import Path

# Same relative idiom the scripts already use for ../assets/zul.xsd. resolve() first,
# so this still finds SKILL.md when a single script is reached through a symlink and
# not only when the whole directory is.
SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"

# Frontmatter only. The body is 60 KB of prose and code samples, and a `version:` in
# one of those must never be mistaken for the skill's own.
_FRONTMATTER = re.compile(r'\A---\s*?\n(.*?)^---\s*?$', re.S | re.M)
_VERSION = re.compile(r'^\s*version:\s*["\']?([0-9][^"\'\s]*)', re.M)

UNKNOWN_VERSION = "unknown"


def read_skill_version() -> str:
    """The version in SKILL.md's frontmatter, or UNKNOWN_VERSION if it cannot be read.

    Returning a sentinel rather than raising is deliberate: reporting a version is
    never the job the user asked for, so a missing or malformed SKILL.md must not stop
    a validation or a render. "unknown" also gives broken installs their own bucket in
    the aggregate counts, where silence would just look like less usage.
    """
    try:
        head = SKILL_MD.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError:
        return UNKNOWN_VERSION

    frontmatter = _FRONTMATTER.search(head)
    if frontmatter is None:
        return UNKNOWN_VERSION
    version = _VERSION.search(frontmatter.group(1))
    return version.group(1) if version else UNKNOWN_VERSION


SKILL_VERSION = read_skill_version()
