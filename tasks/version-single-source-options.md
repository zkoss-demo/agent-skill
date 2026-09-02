# Single source for the skill version — options

## Where "2.0.0" is written today

Four literal sites, not three (the docs count the two scripts as one item):

| # | File | Line | Shipped inside an installed skill? |
|---|---|---|---|
| 1 | `skills/zul-writer/SKILL.md` (`metadata.version`) | 14 | yes |
| 2 | `marketplace.json` | 15 | **no** — repo-level storefront index |
| 3 | `skills/zul-writer/scripts/validate-zul.py` (`SKILL_VERSION`) | 64 | yes |
| 4 | `skills/zul-writer/scripts/preview-zul.py` (`SKILL_VERSION`) | 181 | yes |

`SKILL_VERSION` is consumed in the tracking payload and the `User-Agent` of every outbound
request (`preview-zul.py` also uses it on the download paths at lines 568 and 633).

`detect-pattern.py` holds no version and sends no ping — deliberate, see decisions.md §D19.

## Mechanics verified before writing this

- `uv run <script>.py` puts the script's own directory at `sys.path[0]`, so a sibling-module
  import resolves. Same for the plain `python3 <script>.py` form CI uses.
- Both scripts already resolve siblings through `__file__` (`DEFAULT_XSD_PATH` =
  `../assets/zul.xsd`), so reading `../SKILL.md` is not a new kind of coupling.
- The frontmatter version extracts cleanly with a small regex: `SKILL.md` has exactly one
  line matching `^\s*version:`, and it is inside the `---` block.
- The CI workflow's path filter covers `skills/zul-writer/scripts/**` but **not** `SKILL.md`
  or `marketplace.json` — relevant to option D.

---

## Option A — a shared constant module

`skills/zul-writer/scripts/_skill_meta.py`:

```python
SKILL_VERSION = "2.0.0"
```

Each script replaces its constant with `from _skill_meta import SKILL_VERSION`.

- **Sites: 4 → 3** (SKILL.md, marketplace.json, `_skill_meta.py`)
- **Size:** a 1-line file, a 1-line change in each script.
- **Cost:** the version is still duplicated against SKILL.md, which is the file that actually
  declares what the skill is. Adds a fourth file to `scripts/`, and its `__pycache__` entry
  (already gitignored).
- **Risk:** a script copied out on its own stops importing. Nothing in this repo's install
  paths does that — they move the whole skill directory — but it is the one new failure mode.

## Option B — read the version from `SKILL.md` (recommended)

Put the reader in the shared module from option A, so the parsing exists once:

```python
# _skill_meta.py
import re
from pathlib import Path

def _read_version() -> str:
    try:
        head = (Path(__file__).parent.parent / "SKILL.md").read_text(
            encoding="utf-8", errors="replace")[:4096]
        fm = re.search(r'\A---\s*?\n(.*?)^---\s*?$', head, re.S | re.M)
        return re.search(r'^\s*version:\s*["\']?([0-9][^"\'\s]*)', fm.group(1), re.M).group(1)
    except Exception:
        return "unknown"

SKILL_VERSION = _read_version()
```

- **Sites: 4 → 2** (SKILL.md, marketplace.json). `SKILL.md` becomes the single source of
  truth for the skill itself; `marketplace.json` cannot participate because it is not present
  in an installed skill.
- **Size:** ~15 lines, in one place.
- **Cost:** the tracking payload's correctness now depends on a documentation file being
  present and parseable next to the scripts.
- **Sub-decision it forces:** what the ping carries when `SKILL.md` cannot be read.
  `"unknown"` gives broken installs their own bucket in the analytics; skipping the ping
  entirely loses the run silently. Recommend `"unknown"`.

## Option C — read from `marketplace.json`

**Rule out.** `marketplace.json` sits at the repo root, outside `skills/zul-writer/`. Every
real install (`npx skills add`, a symlink of the skill directory, `.github/skills/`) ships the
skill directory without it, so the scripts would lose their version on every install that is
not a git clone.

## Option D — keep the four literals, make drift fail the build

Add a check to `test/run-regression.py` (or a small standalone test) asserting all four sites
agree, and extend the CI path filter to include `skills/zul-writer/SKILL.md` and
`marketplace.json` — without that, a bump touching only those two never triggers the job.

- **Sites: still 4.** Does not remove the duplication; converts silent drift into a red build.
- **Size:** ~15 lines plus two path-filter entries.
- **Value independent of A/B:** `marketplace.json` is the one site no runtime option can reach,
  so something of this shape is the only thing that ever guards it.

## Option E — a bump script

`tool/bump-version.sh 2.1.0` rewrites all four sites (`tool/` exists and is empty).

- **Sites: still 4**, but one command edits them.
- **Cost:** nothing forces anyone to use it, so it does not remove the failure mode the way
  D does. Best read as a convenience on top of D, not a substitute.

---

## Recommendation

**B for the scripts, D for `marketplace.json`.** B is the only option that makes the file
declaring the skill also the file stating its version, and it costs one small module. D covers
the one site B structurally cannot.

If the goal is strictly the smallest change that answers "the two scripts duplicate a
constant", A alone does that in two lines and stops there.

## Work that comes with any of these

`doc/decisions.md` §D20 and `doc/README.md` both state the rule as *"three places move
together"*. Whichever option lands changes how many places there are, so both passages need
rewriting in the same commit — otherwise the recorded rule describes a layout that no longer
exists.

The version itself stays **2.0.0**. D20's live constraint is that the number moves only when a
release is cut; this refactor changes where the number is written, not what it is.
