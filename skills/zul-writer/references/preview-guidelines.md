# Preview Guidelines

Reference for `scripts/preview-zul.py` (Step 5). Read this when a preview fails, is skipped, or
renders something you did not expect — the judging guidance itself lives inline in SKILL.md.

## How the ZK classpath is resolved

The renderer needs the project's real ZK jars. They are resolved in this order, and the `CLASSPATH:`
line in the output always says which source won:

| Order | Source | How |
|---|---|---|
| 1 | `--classpath` | Taken verbatim (os path separator: `:` on Unix, `;` on Windows). No build tool is run. |
| 2 | **The nearest build file** | Walking up from the `.zul` — or from `--project`, if given — the first directory holding a `pom.xml`, `build.gradle` or `build.gradle.kts` wins. **Maven**: `mvn dependency:build-classpath`, preferring `./mvnw`, plus `target/classes` and `src/main/resources`. **Gradle**: a generated Groovy init script (so Kotlin DSL works too), preferring `./gradlew`, which reports the resolved configurations, the `main` source set's output and resource dirs, and the war plugin's real docroot. |
| 3 | **Stock ZK** | No build file anywhere above the `.zul`, **or** the build tool failed: ZK CE resolved from `mavensync.zkoss.org` through a throwaway POM (`zkbind` pulls the whole CE stack). Needs `mvn` on `PATH`. |

**Only one build tool is ever consulted.** In a directory holding both a `pom.xml` and a
`build.gradle`, Maven wins; but a `build.gradle` in a *nearer* directory beats a `pom.xml` further up
— proximity to the `.zul` decides first, and the file name only breaks a tie. If the chosen tool
fails, the fallback is stock ZK, **not** the other tool. Use `--project` to point at the module that
should own the page, or `--classpath` to bypass the choice entirely.

**With no `pom.xml` and no `build.gradle` anywhere above the `.zul`**, resolution goes straight to
stock ZK: no build tool runs at all, and the page renders against plain ZK CE at `--zk-version`
(default in the script's `DEFAULT_ZK_VERSION`). If Maven is also missing, there is nothing left to
try and the script exits 2 with `no ZK classpath could be resolved`.

Whatever the source, the renderer is handed three kinds of entry in this order — worth knowing if you
ever pass `--classpath` by hand:

1. **Every jar, not just the ZK-named ones.** ZK's `WebManager` needs `org.slf4j.LoggerFactory` at
   bootstrap; a ZK-only classpath dies with `NoClassDefFoundError`.
2. **The compiled-output roots** (`target/classes`, `build/classes/java/main`), so a page's own
   `<zscript>`, `use="..."` or custom EL function can resolve the project's classes. Test output
   (`target/test-classes`, `build/classes/java/test`) is excluded. In the default mode ViewModels and
   Composers still do not run — that is enforced by the renderer, not by withholding the classes — and
   `--run-controllers` is what turns them on (see *Running controllers* below).
3. **Resource roots** such as `src/main/resources`, so ZK's `~./` pages resolve.

Consequence worth remembering: **a `<zscript>` naming a project class needs the project to have been
compiled.** In a freshly cloned project with no `target/classes` yet, that page fails with
`Class ... not found` until you build. That is a missing build, not bad markup.

If resolution falls through to stock ZK, the output says so (`CLASSPATH: probe (stock ZK ...)`) and a
`WARNINGS:` entry gives the reason. Treat that render with care: **project add-ons are absent**, so an
add-on component will show as unknown even though the markup is correct.

Resolved classpaths are cached under `~/.cache/zul-writer/classpath/`, keyed on the content of the
build files (including every ancestor `pom.xml`, since a parent POM governs versions). The cache
self-invalidates when a build file changes, when a cached jar disappears, when the project's
compiled-output directory appears or disappears (so the first build after a clone is picked up), and
after 7 days. Force a re-resolve with `--refresh`.

## How the render helper is resolved

`zk-preview-launcher.jar` is looked up in this order, first hit wins, and the `LAUNCHER:` line in the
output always names the winner (`1.0.2 (cache)`, `1.0.2 (env ZUL_WRITER_LAUNCHER_JAR)`, …):

| Order | Source | How |
|---|---|---|
| 1 | `--launcher-jar` | Taken as given. Nothing is downloaded. |
| 2 | `ZUL_WRITER_LAUNCHER_JAR` | Same, for when the invocation cannot be edited — offline sites, a corporate mirror, a jar you just built. |
| 3 | **The cache** | `~/.cache/zul-writer/launcher/<version>/zk-preview-launcher.jar`, re-verified against its digest on every hit. |
| 4 | **The pinned release** | Downloaded from the URL in the script's `LAUNCHER_URL` and cached at 3. |

A missing file at 1 or 2 is a skip (the path is wrong; nothing silently falls back to a download). A
**digest mismatch** is treated differently by level: at 1 and 2 it only adds a `WARNINGS:` entry and
the jar is used anyway — you named that file deliberately, and a jar you built yourself cannot match
the pin. At 4 it is fatal: nobody chose those bytes, so the partial download is deleted and never
executed.

`--launcher-version <ver>` rolls forward or back without editing the script. A non-default version
has no digest pinned in the script, so it is verified against the `.sha256` published beside the
release instead, with a `WARNINGS:` entry saying so; that checksum is cached beside the jar, so later
runs re-verify offline. If the release publishes no usable checksum, the run skips rather than
executing unverified bytes.

## How the docroot and request path are derived

ZK serves a page at its production URL, not at its filesystem path, so the script picks a docroot and
requests the `.zul` *relative to it*. Rules, in order (the output's `DOCROOT:` line names the one used):

1. **WAR webapp** — nearest ancestor containing `WEB-INF/` or named `webapp`. For a Gradle war
   project, the war plugin's own `webAppDirName` is used directly.
2. **Spring Boot classpath web** — a directory named `web` directly under a resource root
   (`src/main/resources/web`), served as `/index.zul`, not `/src/main/resources/web/index.zul`.
3. **Content-root fallback** — the project root.
4. **File-parent fallback** — the `.zul`'s own directory. This is what a standalone file gets.

**This is what to check when the page renders but its `~./` resources, images or `<include>`s 404.**
A fallback rule in the `DOCROOT:` line is itself a hint that the project layout wasn't recognised;
`--webapp <dir>` overrides it.

The `.zul` **must** live inside the docroot. The render server rejects anything resolving outside it,
so a `../` path cannot work — hence the `outside-docroot` skip below.

## `PREVIEW_SKIPPED:` reasons and their remedies

Exit code 2. None of these is a defect in the ZUL.

| Reason | Remedy |
|---|---|
| `no JDK 17+ found` | Install a JDK 17+, or pass `--java /path/to/jdk-17/bin/java`. The message lists the JVMs it did find. `JAVA_HOME` pointing at an older JDK is the usual cause. |
| `no ZK core jar (zk-<version>.jar) on the resolved classpath` | The project has no ZK dependency, or the resolved set is incomplete. Add ZK, or pass `--classpath`. |
| `no ZK classpath could be resolved` | Not in a Maven/Gradle project and Maven isn't available to fetch stock ZK. Install Maven, or pass `--classpath`. |
| `the .zul is not inside the resolved webapp root` | Pass `--webapp <the .zul's directory>`, or move the file under the docroot. Common when the file was just written to a scratch directory. |
| `no headless browser available` | Install Google Chrome or Microsoft Edge. ZK builds its DOM in client-side JavaScript, so a real browser is mandatory. As a last resort: `uv run --with playwright python -m playwright install chromium`. |
| `could not download the launcher jar` | Offline or proxied. Download the URL in the message to the path it names, or set `ZUL_WRITER_LAUNCHER_JAR`. |
| `does not match its pinned SHA-256` | Re-run (transient corruption). The partial file is deleted, never used. |
| `the pinned launcher release asset does not exist (HTTP 404)` | The skill's pinned launcher version is stale. Three ways out: update the skill, pass `--launcher-version <ver>` for a release that does exist, or point at a local jar with `--launcher-jar` / `ZUL_WRITER_LAUNCHER_JAR`. |
| `the render server did not start / exited before serving` | Almost always an incomplete or mismatched ZK jar set. The message includes the renderer's own output. |

## Debugging a failure

Add **`--debug`** (or set `ZUL_WRITER_DEBUG=1`). It writes to **stderr** only, so stdout stays
byte-for-byte the same contract — it is always safe to add, and it is the first thing to reach for
whenever the result was not what you expected:

- the resolved classpath, **entry by entry**, in the order the renderer receives it (jars → compiled
  output → resource roots), with the source that produced it and whether the cache was hit;
- which build file was found and where the search started;
- every helper command line (`mvn`, `gradlew`, `java -version`, `git`) with its exit code, and the
  full output of any that failed — not the three-line summary the normal report shows;
- the JVM chosen and the version banner of every candidate rejected;
- the launcher jar's path and whether it was cached, downloaded or overridden;
- the renderer's **complete** stdout/stderr, rather than the 6-line tail a failure report carries;
- the docroot rule, the exact URL requested, the HTTP status, whether ZK's client engine reported
  itself mounted, and the PNG's size on disk.

`PREVIEW_SKIPPED: internal error in preview-zul.py` means the script itself crashed, not that the
page is bad — a traceback is printed on stderr. Re-run with `--debug` and report both at
[zkoss/zkidea issues](https://github.com/zkoss/zkidea/issues).

## Reading a render error page

Exit code 1 means ZK itself refused the page — a genuine defect. The output carries:

- **`PHASE`** — `PARSE` (malformed markup, unknown component) or `COMPOSE` (the page parsed but failed
  while building, e.g. a `<zscript>` referencing a class the project has not compiled yet).
- **`MESSAGE`** — ZK's own exception message. Usually names the offending component or class.
- **`LOCATION`** — `in /path.zul:line:column`.
- **`SCREENSHOT`** — the error page is captured too, labelled `[ERROR PAGE — this is not your UI]`.

**An `<include>` with a bound `src` renders nothing, and that is not an error.** A constant literal
in the binding is included for real; anything else leaves `src` unset, so the section is silently
absent from the image rather than dimmed like other bindings. Nothing is logged and no error page is
produced — see *What you cannot judge* in SKILL.md before treating a missing section as a defect.

**A missing line number is not a clue worth chasing.** Component-hierarchy errors (a child not
allowed inside a given parent) are raised without position information, so `LOCATION` may carry only
the file name. Use the `MESSAGE` — it names the components involved.

## Running controllers (`--run-controllers`)

By default the renderer substitutes a no-op composer for every `apply="..."` and every
`viewModel="..."`, so no project controller ever runs. `--run-controllers` turns that off for the
run: the project's real Composers and ViewModels are constructed, the real ZK `Binder` resolves real
values, and the placeholder injector stands down completely.

**It executes arbitrary project code.** Constructors, `doAfterCompose`, `@Init` methods, whatever
they call. It is opt-in per render, never a default, and it is not what the ZK IntelliJ plugin does —
that pane stays isolated. Pass it for a page whose controller you wrote in this session; do not pass
it for code you have not read.

The mode is always reported, on success and on an error page alike:

| Line | Meaning |
|---|---|
| `CONTROLLERS: skipped (isolated)` | default. No Composer, no ViewModel. |
| `CONTROLLERS: executed` | controllers ran; every value in the image is real. |
| `CONTROLLERS: failed → isolated` | controllers were attempted and could not deliver; the isolated render was served instead, and `WARNINGS` names the cause. |

**Fail soft.** A controller that throws, cannot be loaded, or overruns its budget never destroys the
preview: the page is rendered once more with isolation on, the exit code stays **0**, the screenshot
is still written, and a `WARNINGS` entry carries the exception class, the first line of its message
and — when the stack names one — the failing project class. Treat that entry as a defect report
against the controller, not against the ZUL.

**`failed → isolated` really does mean the controller.** The renderer never guesses from the
exception type: it compares the two attempts. Only a failure that disappears when the controllers
stand down is reported as theirs. A page that is broken on its own fails both attempts, so it is
reported exactly as it is without the flag — `CONTROLLERS: skipped (isolated)`, no controller
warning, exit **1** with `PHASE`/`MESSAGE`/`LOCATION` — and the defect is in the ZUL at that
location.

**`--controller-timeout <seconds>`** (default 10) bounds a `--run-controllers` render. The budget
covers the **whole render**, not controller time alone: the renderer cannot separate a composer's
work from ZK's own first-paint work (language and component definitions, page compile), and a cold
JVM's first render is the expensive one. So a legitimately heavy page on a slow machine can time out
and degrade with nothing wrong in it — the warning always says the budget covers the whole render and
names this flag. It is ignored in the default mode, which therefore can never time out.

**Two warnings worth knowing.** If `--run-controllers` is passed and the resolved classpath carries
no compiled output roots, the run says so immediately (`no compiled classes are on the classpath`)
instead of surfacing a `ClassNotFoundException` from inside the render — build first. And if the
render helper is older than this feature, it accepts the flag, ignores it, and renders isolated; the
script detects the silence and warns, naming the launcher version, because a placeholder page judged
under the rules for real data is the worst possible outcome here.

**The placeholder matrix**, which is what the judging rules in SKILL.md turn on:

| | Bound value | `model`-bound grid/listbox | `apply=` label |
|---|---|---|---|
| isolated (default) | dimmed placeholder text (`vm.customer`) | 3 dimmed placeholder rows | empty |
| `--run-controllers` | the real value | the real rows | the real value |
| `--run-controllers`, controller failed | falls back to the isolated row | " | " |

## Layout findings (the `LAYOUT:` block)

After the screenshot is written, the renderer runs a DOM audit in the same browser and reports what
it measured. The block is appended between `CONTROLLERS:` and `WARNINGS:`, and it is **omitted
entirely when there is nothing to report** — so a clean page prints exactly what it printed before
the audit existed.

| Rule | Fires when | Remedy |
|---|---|---|
| `clipped-text` | an element's own text run does not fit inside the nearest ancestor that clips (`overflow: hidden` or `clip`), measured against that ancestor's **padding box** | widen the box, allow wrapping, or shorten the text |
| `zero-size` | a ZK widget root measures 0 in width or height while it has text or children, and nothing inside it has a box either | a missing `height`/`vflex`, or a `width: 0` rule |
| `escapes-parent` | an element's border box exceeds its `offsetParent`'s padding box by more than 2px while that parent clips | give the parent room, or stop the child overflowing |
| `viewport-overflow` | `documentElement.scrollWidth` exceeds the viewport width; one finding for the page, naming the widest element whose right edge passes the viewport | drop the fixed width on the named element |

The padding box is the measurement that matters: `overflow: hidden` clips there, not at the content
box, so text may spill out of the content box into the padding and still be perfectly visible. ZK's
own `div.z-listheader-content` is 60px wide with 16px of padding either side — comparing a 38px
header label against its 28px content box reports a truncation that a reader can plainly see is not
there.

**Locators.** Every finding is resolved back to the ZK widget that *owns* the node, through
`zk.Widget.$()`, because the node carrying the text is often ZK's own chrome. The locator is the ZUL
id when the author wrote one (`label#breadcrumbCurrent`), otherwise the widget plus the first
distinguishing attribute (`a[label="Settings"]`, `label[value="GovPortal"]`,
`textbox[placeholder="Search applications..."]`), otherwise the widget plus a style class,
preferring an author class (`grid.gp-wide`) but falling back to ZK's own theme class when the node
carries nothing else (`div.z-div`). That last form is the weakest one the audit prints — it still
names the widget type, and for `escapes-parent` the line also names the clipping parent. A generated ZK uuid is never printed: a locator reading `label#pQr51` names
nothing anyone can search for, so the id is used only when it differs from the uuid.

**What the audit deliberately does not flag.**

- **`overflow: auto` and `overflow: scroll` regions.** A scrollable region reaches its content, so it
  is not a layout defect — and ZK's Grid, Listbox and Tree bodies are `overflow: auto`, so treating
  them as clippers would report every row of every data table. The cost is that a page which clips
  through `auto` on an axis that cannot actually scroll goes unreported: the audit under-reports
  rather than over-reports, deliberately.
- **Overlapping widgets.** Dropped for v1 — the rule was too noisy to be worth an agent's attention.
- **ZK chrome that legitimately measures nothing.** Only widget *roots* can raise `zero-size`, and
  only when nothing inside them has a box: a ZK borderlayout region root is a class-less wrapper at
  1270x0 whose visible child is 1270x60, and `div.z-hlayout-inner` measures 0x0 around an empty
  label. Both render correctly, so neither is reported.

**Viewport.** Findings are measured against the viewport on the `SIZE:` line — 1280x900 by default —
including under `--full-page`, because a full-page capture stitches the image without ever resizing
the browsing context. What `--full-page` does *not* change is which findings appear: the audit
queries the whole document either way, so it reports things below the captured fold in both modes.
That is the point of it, and it means a finding can name something the PNG does not show.

**Caps.** At most 25 findings are printed, deduped by `(rule, locator)` so one defect is one line;
when there are more, a final `  ... and N more` line accounts for the rest. The count on the
`LAYOUT:` header is always the true total.

**`--fail-on-layout`** makes a run with any finding exit **4** instead of 0, for CI. It changes
nothing else: the same findings are reported without it, and `STATUS: ok` still prints with it — exit
1 stays reserved for a real defect in the .zul.

## Console and client-error warnings

Two browser-side channels feed the existing `WARNINGS:` block. Neither adds a block and neither
changes the exit code — console findings are advisory, exactly like the 404 entries beside them.

| Entry | Source | Captured how |
|---|---|---|
| `console error: <text>` | the page's own JavaScript at `console.error` | `page.on("console")`, level `error` |
| `console warning: <text>` | the same at `console.warn` | `page.on("console")`, level `warning` |
| `ZK client error: <text>` | ZK's client engine — `zk.error()` | a DOM read of the on-page error box, after the screenshot |

**Only `error` and `warning` are collected.** `log`, `info`, `debug` and `trace` never reach stdout.
`--debug` dumps *every* level to stderr, with the originating URL and line, including the levels
this block filters out — stdout's contract is identical with and without it.

**What is dropped, and why.** A console entry whose text starts with `Failed to load resource:` is
discarded. Those come from Chromium's network stack rather than from page JavaScript, and every page
emits at least one: a 404 for `/favicon.ico`, which the launcher does not serve. Their text carries
no URL at all — the URL is only in the message's `location` — so they would read as an unattributable
finding on every clean page. The asset failures that matter, ZK's own `/zkau/web/` resources, are
reported separately by the `page.on("response")` handler with the real URL and the classpath advice.
The cost is deliberate under-reporting in two places: a page whose own JS logs a message beginning
with that exact string is dropped too, and a 404 on an asset *outside* `/zkau/web/` (a project CSS
file, an app image) is now reported by neither channel. Widening the 404 detector is a separate job.

**Why ZK's complaints need a DOM read.** ZK 10.3's client engine does not use the console.
`zk.error()` passes the message to `zk.debugLog` — which only reaches the console when `zk.debugJS`
is on — and then to `zk.errorPush` → `zk._Erbx`, which appends a box to `document.body`
(`zk-10.3.0.1-Eval.jar`, `web/js/zk/index.src.js:35803-35816` and `:36487-36500`). A `page.on(
"console")` subscription therefore sees *nothing* of "Unknown widget: …", "Failed to mount: …" or a
missing mold. So the script reads `div.z-error > .messagecontent > .messages` after the screenshot:
its direct text nodes are the first message and each element child is one more, which is how
`_Erbx.push` builds it. This is a read of ZK-internal markup with no API contract behind it — a
future ZK that renames the box breaks the capture **silently**, because the read is
exception-suppressed so that a bug in it can never fail a good render. Treat it as best-effort.

**Caps and dedupe.** Each channel prints at most 10 entries, deduped — console by `(level, text)`,
client errors by text — and when there are more, a final `  ... and N more …` line accounts for the
rest rather than truncating silently. Every entry is one line: the first line only, snipped at 200
characters with a trailing `…`, because a console message is frequently one enormous serialized
object.

**Limits.** The window closes just after the screenshot: a `zk.error` raised by a later AU response,
or a console message emitted after the last Playwright wait, is never delivered, so an empty block is
not proof of a clean session. A box the page dismissed itself is invisible. `zk.debugJS` stack traces
are not captured. And the error box is a real visible overlay, so on a page that raises a client
error it may show up in the PNG — possibly mid-animation, since `animations="disabled"` applies to
the screenshot and not to a jQuery `slideDown` already in flight.

## Previewing a `.zul` outside any project

Works with no setup: the script falls back to stock ZK CE and uses the file's own directory as the
docroot. Pick a specific version with `--zk-version` (a `-jakarta` suffix selects the jakarta servlet
variant, e.g. `--zk-version 10.1.0-jakarta`). Add-ons are not available on this path.

## Environment overrides

| Variable | Purpose |
|---|---|
| `ZUL_WRITER_LAUNCHER_JAR` | Use a local render helper instead of downloading — offline sites, or a corporate mirror. |
| `ZUL_WRITER_CACHE_DIR` | Relocate the cache (default `~/.cache/zul-writer/`). |
| `ZUL_WRITER_JAVA` | Pin the JVM used for rendering, without passing `--java` every time. |
| `ZUL_WRITER_DEBUG=1` | Same as `--debug`, for when the invocation cannot be edited. |
| `DO_NOT_TRACK=1` | Disable the anonymous usage ping, as with `validate-zul.py`. |

Useful flags: `--debug` (see above), `--width`/`--height` (default 1280x900), `--full-page` for the
whole scrollable page, `--timeout` for slow pages, `--browser-channel chrome|msedge|chromium`,
`--launcher-version` to move off the pinned render helper, `--run-controllers` /
`--no-run-controllers` to run (or force off) the project's real controllers,
`--controller-timeout` for their budget, and `--fail-on-layout` to exit 4 when the `LAYOUT:`
block has any finding.

## Where the renderer comes from

`zk-preview-launcher.jar` is built from the ZK IntelliJ plugin's repository
([zkoss/zkidea](https://github.com/zkoss/zkidea)) and is the same engine that powers that plugin's
Layout Preview pane — so what you see here matches what the IDE shows. Its CLI contract is documented
in that repo's `zk-preview-launcher/README.md`, and the complete list of rendering limitations is
`doc/zul_preview_spec.md` §4 (L-1…L-14), summarised for end users in `doc/zul-preview-feature.md`.
