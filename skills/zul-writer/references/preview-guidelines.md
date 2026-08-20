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
   (`target/test-classes`, `build/classes/java/test`) is excluded. ViewModels and Composers still do
   not run — that is enforced by the renderer, not by withholding the classes.
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
`--launcher-version` to move off the pinned render helper.

## Where the renderer comes from

`zk-preview-launcher.jar` is built from the ZK IntelliJ plugin's repository
([zkoss/zkidea](https://github.com/zkoss/zkidea)) and is the same engine that powers that plugin's
Layout Preview pane — so what you see here matches what the IDE shows. Its CLI contract is documented
in that repo's `zk-preview-launcher/README.md`, and the complete list of rendering limitations is
`doc/zul_preview_spec.md` §4 (L-1…L-14), summarised for end users in `doc/zul-preview-feature.md`.
