# Working on the skill itself

Environment facts and test-rig reasoning that are not visible in the code: how to iterate on the skill in
its plugin form, and why testing the skill *inside this repository* measures something other than the
skill.

---

## 1. Two prerequisites that silently degrade everything

**Java on `PATH` is 11; Step 5 needs 17+.** Without intervention the preview exits 2 with
`PREVIEW_SKIPPED` and the self-review step never runs — **this applies to the showcase project too, not
just scratch projects.** Confirm it before blaming a skipped preview on the ZUL. JDK 17 and 21 are
installed; invoke through the JDK wrapper:

```bash
withjdk.sh 17 uv run skills/zul-writer/scripts/preview-zul.py …
```

**The launcher jar used to be untracked build output.** When it was a local Gradle artifact, a
`./gradlew clean`, a fresh clone or a different machine removed it — and with it gone, most scenarios
degenerated into the skip path *silently*, which looks like everything passing. The jar is now a pinned,
SHA-256-verified GitHub release asset, so this is historical; the failure mode is worth remembering
because **a preview that skips looks like a preview that succeeded** unless the output is read.

A rebuilt local jar produces a **new digest**, so the pinned-digest warning line is expected and must
never be asserted away by counting warnings.

---

## 2. An unconfirmed risk worth one cheap experiment

`zulwriter-showcase/src/main/webapp/WEB-INF/zk.xml` forwards every `Throwable` to `/error.zul`:

```xml
<error-page>
    <exception-type>java.lang.Throwable</exception-type>
    <location>/error.zul</location>
</error-page>
```

**There is no `error.zul` in the webapp.** On a ZUL error the server forwards to a missing page, so Step
5's error path (`PHASE` / `MESSAGE` / `LOCATION`) may be reading a 404 instead of ZK's real error page.

**This was never confirmed.** It is a risk, not a finding. The experiment: write one deliberately broken
`.zul`, render it in both a project with that block and one without, and compare stderr.

---

## 3. Iterating on the skill in its plugin form

### A live symlink into the working tree is not possible

Two independent reasons, both from the marketplace's own design:

1. The marketplace build has an explicit **symlink guard** that fails the build if any symlink survives
   inside `plugins/`, because plugin content is copied into `~/.claude/plugins/cache/` on install.
   `plugins/` is generated and wiped on every build.
2. More fundamentally, the plugin form **requires** the portability patch. `SKILL.md` invokes its own
   scripts by literal path (`uv run ~/.claude/skills/zul-writer/scripts/…`), and the build rewrites those
   to `${CLAUDE_PLUGIN_ROOT}/skills/zul-writer/…`. A raw symlink to the repo would ship the unpatched
   paths, and `~/.claude/skills/zul-writer` no longer exists — so **Step 3 (validate) and Step 5
   (preview) would both break**, which is exactly the code being iterated on.

**The build step is not incidental overhead; it is what makes the plugin form work at all.**

### `claude plugin update` is a no-op on content changes

The install cache is keyed on **version, not content**. Both of these report success while the cache
stays stale:

```
claude plugin marketplace update <marketplace>   # refreshes the catalogue only
claude plugin update <plugin>@<marketplace>      # "already at the latest version"
```

To actually refresh without bumping the version, uninstall and reinstall.

### The loop that works

Edit the repo — `skills/zul-writer` here is the canonical source — then:

```bash
cd <marketplace-repo>
./build.sh && claude --plugin-dir "$PWD/plugins/zk-framework"
```

`--plugin-dir` loads the plugin for that session only and **skips the version-keyed cache entirely**, so
every launch picks up the current build. Verified: the session shows the skill exactly once, with no
clash against a user-scope install.

To ship a change permanently: build, commit the generated `plugins/` tree, then uninstall/reinstall — or
bump the plugin version so `claude plugin update` starts working.

**A mirror will drift, and only a build reveals it.** One rebuild surfaced three committed
`preview-zul.py` fixes that had never reached the mirror: `glob.glob` for JDK discovery, the
`if not explicit:` guard so a one-off `--java` is not cached as the default, and a Maven classpath cache
key no longer keyed on the `.zul` directory. After the rebuild the only intended repo-vs-mirror
difference is the portability patch.

---

## 4. Why testing the skill in this repository measures the wrong thing

`SKILL.md` never tells the agent to read project `.zul` files — Step 2 points only at `assets/*.zul`.
**The interference comes from the surrounding environment instead**, ranked by how much it distorts a
test.

### This repository contains the answer key — fatal

`ui-screenshots/` holds nine PNGs and **each one already has its committed output** (`Task Master.png` →
`task-master.zul` + `TaskMasterComposer.java`, and so on). Testing with one of these means the agent does
not have to *generate* the page — it can find it. And it surfaces incidentally even with no intent to
cheat: detecting the ZK version, resolving the docroot for Step 5, or any glob over `src/main/webapp/`
puts sibling filenames in context. **What gets measured is recall, not generation.**

### "Match the surrounding code" is a standing baseline instruction — significant

Independently of the skill, the harness tells the agent to write code that reads like its neighbours.
Dropping a new page beside fifteen existing ZK pages primes file naming, `sclass` naming, whether CSS
goes in a `<style>` block, and borderlayout habits. A page generated here is therefore
**skill + repo-prior**, not the skill alone. Fine for "does my dev loop work", misleading for "is
SKILL.md good".

### `RULES.md` confounds exactly one guideline — narrow but real

`RULES.md` says *"Always create css classes, don't specify inline style"*; `SKILL.md` says *"Prefer
`sclass` over inline styles."* They say the same thing, so obeying it cannot be attributed to the skill.
Every other guideline is unaffected. Move `RULES.md` aside when grading that one rule.

### What does *not* interfere

- **The Step 5 preview.** It appends `target/classes` to the classpath by hand and never runs a compile,
  so a pre-existing composer that fails to build cannot break the preview of a new page.
- **`pom.xml` version detection.** Step 1 is *supposed* to read it; that is the feature working. Note the
  commented-out ZK 9 version and the `webapp/zk9/` folder — **exercising the ZK 9 path means flipping the
  pom, not relying on the folder name.**
- **Runtime collisions.** Distinct filenames, no shared IDs across pages.

---

## 5. "What if I just delete all the ZUL files?" — don't

Three answers: it helps a little, it does not equal a fresh project, and **the git risk is not the
obvious one.**

Deleting the fifteen `.zul` files buys exactly one thing — the exact answer markup can no longer be
read — and that is the **smallest** of the leaks. What survives:

| Carrier | What it still leaks | Severity |
|---|---|---|
| **`README.md`** | A **prompt→output table**: the verbatim prompt for 8 pages, each linked to its `.zul` | **Worse than the files** |
| `src/main/java/zwriter/*.java` | 18 controllers — the Step 4 priors, paired 1:1 with the deleted pages | High |
| `ui-screenshots/*.png` | The nine input images, i.e. the test inputs themselves | High |
| `target/classes/zwriter/*.class` | Compiled composers — and the preview puts this directory on the Step 5 classpath | Medium |
| `RULES.md` | The CSS-class rule above | Low but confounding |

`README.md` is what breaks the plan: it is not a file listing, it is **the assignment sheet**, describing
in detail what each page contains and naming its file. It even documents the cross-reference convention
(a generated ZUL carries a comment naming its source screenshot).

**Git history is the low risk; `git status` is the high one.** Nothing tells the agent to consult
`git log` during generation — recovering deleted pages from history is something an agent *could* do, not
something that happens by default. But `git status` runs routinely, and deleting fifteen tracked files
makes every run print all fifteen filenames as deletions. **Deleting to hide them is the one action
guaranteed to surface them.**

And the part no file operation fixes: **contamination is about what is in the context window, not what is
on disk.** A conversation that has already read the filenames, controller names and README table cannot
un-read them by deleting files afterwards.

### The right shapes instead

- **A separate scratch project** achieves strictly more for zero risk: `pom.xml` + `WEB-INF/web.xml` +
  `WEB-INF/zk.xml` copied verbatim, an empty `src/main/webapp/`, the live skill symlinked in, and
  **nothing else** — no `RULES.md`, no `.zul`, no controller, no `ui-screenshots/`, no `target/`. Keep
  dependencies pinned to the same ZK version so version detection and the Step 5 classpath behave
  identically. Put it **outside** this repository, or it inherits this repo's `CLAUDE.md` and `README.md`
  as project instructions and shows up in `git status`.
- **A throwaway git worktree**, if the deletion route is wanted anyway: `git worktree add /tmp/… HEAD`,
  then delete all five carriers there. The showcase stays untouched, `git status` stays quiet in the real
  repository, and only git history is shared — which is the part that does not matter much.

### Who runs the clean pass matters more than where it runs

An agent that has already read this repository's file list in the current conversation cannot then run
the "clean" test — the prior is in its context and the isolation is theatre. **A fresh session in the
scratch directory is genuinely clean;** a subagent with a narrow prompt has fresh context but the prompt
is written by someone who can leak, so it is weaker.

### What the comparison tells you

Run the same new screenshot through both environments and diff the two `.zul` + controller pairs:

- **Near-identical** → the repo prior is weak; `SKILL.md` is carrying the output.
- **Diverges on naming, CSS placement or layout idiom** → that is the "match surrounding code" prior.
- **The showcase output is markedly better** → `SKILL.md` is under-specified and the showcase examples
  were quietly doing the work. The most actionable outcome: those implicit conventions belong in
  `assets/` or `references/`.
