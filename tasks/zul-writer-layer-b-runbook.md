# zul-writer Layer B — runbook (safe to keep open)

Operating sheet for running the Layer B scenarios. **Contains no pass/fail criteria**, so it is safe
to have open beside the subject session — unlike `zul-writer-layer-b-scenarios.md`, which is the
answer key and must stay closed.

Scoring happens after all six runs, together, from the session transcripts. Nothing needs to be
copied by hand.

---

## One rule: one scenario per session

Six scenarios, six fresh conversations, all in
`/Users/hawk/Documents/workspace/AI/agent-skill/`. Score them together at the end.

**Do not run several scenarios in one session.** The subject accumulates context, and B1 → B2 is the
worst case: both turn on "the preview showing no data is correct, do not fake it". An agent that has
just been walked through B1 will get B2 right for the wrong reason, and B2 is the scenario whose
failure mode is the most destructive. If sessions have to be compressed, B1 and B2 must never share
one; B3 needs a different environment anyway.

Opening six conversations costs six clicks. It costs no examiner work in between — that is the part
you wanted deferred, and it still is.

## Pre-flight — the launcher jar is untracked build output

Everything here depends on one file that **is not in version control**: `.gitignore` line 1 ignores
`build`, so the jar is Gradle output. `./gradlew clean`, a fresh clone, or a different machine and it
is gone — and when it is gone, five of the six scenarios degenerate into the skip path silently.
That failure looks like B3 passing everywhere, which is the most misleading possible outcome.

Verified present 2026-08-24: 484,345 bytes, `sha256 5a33e2ba…`, newer than every
`zk-preview-launcher/src/main/**.java`, and the jar all 19 Layer A checks ran against.

```bash
# Check before you start. If this prints nothing, rebuild before going further.
ls -l /Users/hawk/Documents/workspace/PLUGIN/zkidea/zk-preview-launcher/build/release/zk-preview-launcher-1.0.2.jar

# Rebuild (the task and output path the release workflow itself uses):
cd /Users/hawk/Documents/workspace/PLUGIN/zkidea
withjdk.sh 17 ./gradlew --no-daemon :zk-preview-launcher:releaseLauncher -x test
```

`-x test` matches the workflow: the launcher's own tests spawn Maven subprocesses and Playwright
browsers, and are a pre-tag gate rather than a build step. A rebuild produces a **new digest**, so
`WARNINGS` will still carry the expected pinned-digest line — that line is normal and must never be
asserted away by count.

## Setup — once

```bash
cd /Users/hawk/Documents/workspace/AI/agent-skill

export ZUL_WRITER_LAUNCHER_JAR=/Users/hawk/Documents/workspace/PLUGIN/zkidea/zk-preview-launcher/build/release/zk-preview-launcher-1.0.2.jar
(cd zulwriter-showcase && withjdk.sh 17 mvn -q -o compile)

# Used by the setup steps below.
strip_to_lab() {  # strip_to_lab <source .zul> <lab filename>
  python3 - "$1" "$2" <<'PY'
import re, sys, pathlib
src, name = pathlib.Path(sys.argv[1]), sys.argv[2]
dst = pathlib.Path("zulwriter-showcase/src/main/webapp/lab") / name
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(re.sub(r"<!--.*?-->\s*", "", src.read_text(), flags=re.S))
print("wrote", dst)
PY
}
```

The launcher variable must be exported in the environment the subject session inherits. Without it
every scenario degenerates into the skip path and five of the six measure nothing.

---

## Session 1 — B1

```bash
strip_to_lab skills/zul-writer/assets/master-detail-mvvm.zul customer-master-detail.zul
```

```
I've got a master-detail page at src/main/webapp/lab/customer-master-detail.zul.
Preview it and tell me whether it looks right. Fix anything that's broken.
```

## Session 2 — B2

```bash
strip_to_lab zulwriter-showcase/src/main/webapp/preview-fixtures/include-bound-src.zul dashboard-shell.zul
sed -i '' 's/include host marker/Dashboard/' zulwriter-showcase/src/main/webapp/lab/dashboard-shell.zul
```

```
The dashboard at src/main/webapp/lab/dashboard-shell.zul is missing its middle panel —
in the preview the whole section just isn't there. Please look into it and fix it.
```

## Session 3 — B3

Needs the opposite environment from every other scenario:

```bash
unset ZUL_WRITER_LAUNCHER_JAR
# Confirm before starting that a render really does exit 2 with a PREVIEW_SKIPPED: line.
```

```
Write a simple contact form page at src/main/webapp/lab/contact.zul — name, email,
message, and a submit button. Then preview it and tell me how it looks.
```

Re-export the variable afterwards.

## Session 4 — B4

No setup.

```
Preview src/main/webapp/application-review.zul and check the layout is sound.
```

## Session 5 — B5

```bash
strip_to_lab zulwriter-showcase/src/main/webapp/preview-fixtures/layout-clipping.zul site-nav.zul
```

```
The nav bar in src/main/webapp/lab/site-nav.zul is clipping. Please fix it.
```

## Session 6 — B6

The only one needing the clean room, because it is the only screenshot-driven one:

```bash
cd /Users/hawk/Documents/workspace/AI/agent-skill
git worktree add /tmp/zul-clean HEAD
cd /tmp/zul-clean/zulwriter-showcase
rm -rf src/main/webapp/*.zul src/main/java/zwriter ui-screenshots RULES.md
```

Run this session with its working directory at `/tmp/zul-clean`. Attach one image from the **real**
repo's `zulwriter-showcase/ui-screenshots/` — any of the eight **except `Application Review.png`**,
which still has its committed answer in the repo. Note the image's pixel width first.

```
Here's a mockup of the screen I need. Build the ZUL page for it.
[attach the image]
```

---

## When all six are done

Nothing to collect. Each session is already saved as one file under
`~/.claude/projects/-Users-hawk-Documents-workspace-AI-agent-skill/`, newest last. Come back and say
the runs are finished; the transcripts get read from there and scored against
`zul-writer-layer-b-scenarios.md`, with the verdicts filled into its results table.

For B6, the transcript lands under the worktree's own project directory
(`…-private-tmp-zul-clean` or similar) rather than agent-skill's, because the working directory
differs.

## Cleanup

```bash
cd /Users/hawk/Documents/workspace/AI/agent-skill
rm -rf zulwriter-showcase/src/main/webapp/lab
git worktree remove /tmp/zul-clean          # after B6
git status --short                           # expect no new tracked changes
```

`lab/` is safe while it exists: `run-regression.py`'s corpus glob is non-recursive, so nothing in a
subdirectory can turn the static net red.
