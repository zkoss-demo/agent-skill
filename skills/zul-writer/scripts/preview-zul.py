#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.44"]
# ///
"""
ZUL Preview — render a .zul file to a PNG.

USAGE

  uv run preview-zul.py [options] <file.zul>

  uv run preview-zul.py src/main/webapp/index.zul             # simplest form: detect everything
  uv run preview-zul.py --out shots/page.png page.zul         # somewhere other than ./page-preview.png
  uv run preview-zul.py --debug page.zul                      # diagnostics on stderr; try this on ANY failure
  uv run preview-zul.py --webapp src/main/webapp page.zul     # the docroot was guessed wrong
  uv run preview-zul.py --classpath "$(cat cp.txt)" page.zul  # skip Maven/Gradle resolution entirely
  uv run preview-zul.py --full-page --width 1440 page.zul     # wider / whole-page capture

`uv run` is the recommended form: uv reads the PEP 723 metadata above and provides
`playwright` in an ephemeral environment. uv supplies the Python package only, never a
browser — which is why this drives the system Chrome or Edge rather than a Playwright-managed
one. Plain `python3 preview-zul.py` also works where playwright is already installed.

OPTIONS worth knowing, and when to reach for one

  -o/--out PNG     where to write the image (default: ./<name>-preview.png, in the
                   current directory)
  --debug          dump the resolved classpath entry by entry, every helper command line
                   with its exit code and output, and the renderer's own stdout/stderr —
                   all on stderr. stdout stays exactly the same contract either way, so
                   this is always safe to add. The first thing to try on a failure.
  --webapp DIR     docroot to serve the .zul relative to — reach for it when the DOCROOT:
                   line reports a fallback rule, or the .zul sits outside the project
  --classpath CP   os-path-separated jars/dirs, taken verbatim; no build tool is run
  --project DIR    where to start looking for pom.xml / build.gradle
  --zk-version V   stock-ZK version for a .zul in no project (a -jakarta suffix selects
                   the jakarta servlet variant, e.g. 10.1.0-jakarta)
  --java PATH      the JVM to render with, if the auto-detected one is wrong
  --refresh        ignore the cached classpath and resolve it again
  --run-controllers
                   run the project's real Composers and ViewModels, so bound values,
                   model-bound rows and anything a composer fills are the real thing.
                   This EXECUTES ARBITRARY PROJECT CODE from the resolved classpath, so
                   it is off by default. Pass it for a page whose controller you wrote.
  --controller-timeout N
                   wall-clock budget for a --run-controllers render (default 10s); on
                   expiry the page is rendered again isolated and the run still succeeds
  --probe SELECTOR every element matching this CSS selector, as the browser rendered it:
                   opening tag, measured box, and the computed styles a layout or icon
                   defect turns on. Repeatable. Reach for it when the image shows that
                   something is wrong but not why — it reads the render you already have
                   instead of costing another one.
  --dump-dom       write the whole post-mount DOM beside the PNG (its path with a
                   .dom.html suffix), for when you do not yet know what to --probe
  --report json[:<path>]
                   also write this whole run as one JSON object, for a caller that parses
                   rather than reads (default path: the PNG's, with a .json suffix). The
                   text lines below do not change; stdout gains one line, REPORT: <path>.
  also: --launcher-jar --launcher-version --browser-channel --width --height
        --full-page --timeout --fail-on-layout

READING THE RESULT — stdout is one `KEY: value` per line. Branch on the first line:

  STATUS: ok            → open the path on the SCREENSHOT: line and LOOK at the image
  STATUS: render-error  → a real defect in the .zul; PHASE / MESSAGE / LOCATION say where
  PREVIEW_SKIPPED: …    → no preview was possible, and that is NOT a defect in the .zul.
                          Report it in one line and move on; never describe an image you
                          did not see. The NEXT: line says what would enable it.

WARNINGS: entries are advisory. A 404 on a ZK asset usually means an add-on jar is missing
from the classpath, so the image can look plausible and still be wrong.
`console error:` / `console warning:` entries are what the page's own JavaScript logged.
`ZK client error:` entries are what ZK's client engine put in its on-page error box — it
uses that box rather than the console, so those complaints are only visible there. Both
kinds are deduped and capped; --debug lists every console level, on stderr only.

LAYOUT: entries are what the browser measured, so they are facts rather than opinions —
read them before opening the PNG. The block covers the WHOLE document, not just the
captured region, so a finding may name something the screenshot does not show. It is
omitted when there is nothing to report, and it never changes the exit code unless
--fail-on-layout is passed.

PROBE: and DOM: are the rendered DOM, and they exist because the served response is not
it: ZK sends a `zkmx([...])` bootstrap that restates the .zul, and the client engine builds
the real markup afterwards. So the class names, the fonts and the boxes only exist in the
browser. An empty box where an icon belongs, a component you cannot find, a colour nobody
asked for, a width that is not the one you set — --probe answers all four from the render
already in hand. Neither block appears unless its flag was passed.

The text lines are the contract, with or without --report. `REPORT: <path>` names a
sidecar file carrying this same run as one JSON object — the same facts, no more — for a
caller that parses rather than reads. It is printed only under --report, and it is the
last line printed when it is.

Exit codes:
  0  rendered            STATUS: ok           + SCREENSHOT: <path>
  1  render error        STATUS: render-error — a real defect in the .zul
  2  no preview possible PREVIEW_SKIPPED: <reason> — NOT a defect in the .zul
  3  usage error
  4  layout findings, with --fail-on-layout (never without it)

WHAT THE IMAGE SHOWS

The rendering itself is done by ZK's own DHtmlLayoutServlet inside the launcher, so the
image shows what ZK really produces — but only the FIRST PAINT. What fills that paint
depends on the mode, which the `CONTROLLERS:` line always names:

  CONTROLLERS: skipped (isolated)   the default. No ViewModel, no Composer. Bound values
                                    appear as dimmed placeholder text and model-bound
                                    grids/listboxes show placeholder rows; a bound `src`
                                    is the exception, contributing nothing at all rather
                                    than a placeholder. That is correct behaviour, not a
                                    defect. The project's own classes DO load, so a
                                    <zscript> or use="..." naming one of them runs for real.
  CONTROLLERS: executed             --run-controllers, and the controllers ran. Real bound
                                    values, real model rows, real composer output, no
                                    placeholders anywhere — so a field left blank here is a
                                    real gap in the page or its controller.
  CONTROLLERS: failed → isolated    --run-controllers, but the controllers threw, could not
                                    be loaded, or overran --controller-timeout. The page was
                                    rendered again isolated, so read it under the first set
                                    of rules; WARNINGS names the cause. The exit code stays 0
                                    and the screenshot is still written.

PIPELINE, in execution order. `main()` is this list, one call per step. The order is
load-bearing: no step may do expensive work that a later step can prove unnecessary,
which is why the classpath is resolved before the launcher jar is fetched — an unusable
classpath must exit 2 without touching the network.

  1. Resolve the ZK classpath — explicit / Maven / Gradle / stock-ZK probe POM
  2. Resolve the docroot the .zul is served relative to, and the request path
  3. Find a JDK 17+ (probed, because JAVA_HOME is frequently an older JVM)
  4. Get zk-preview-launcher.jar (cached; else downloaded and SHA-256 verified)
  5. Start the launcher, wait for its PREVIEW_PORT= handshake
  6. Drive headless Chrome (Playwright) at the page, wait for ZK's client engine
     to finish mounting, screenshot
  7. Kill the JVM
"""

import argparse
import atexit
import collections
import contextlib
import glob
import hashlib
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ElementTree
from pathlib import Path


# --- Anonymous, aggregate usage tracking ---------------------------------
# Privacy by design: sends NO identifier of any kind — no visitor ID, no
# cookie, no per-install file. Each run is an independent, unlinkable event
# carrying only the skill name and version.
#
# Fired on a background daemon thread so a slow/unreachable network never
# delays rendering. Opt out entirely by setting DO_NOT_TRACK=1 or
# TRACK_URL="" in the env, or per-run with --dev (see track_usage_async).

TRACK_URL = os.environ.get("TRACK_URL", "https://www.zkoss.org/api/track")
SKILL_VERSION = "2.0.0"


def _tracking_opted_out() -> bool:
    return os.environ.get("DO_NOT_TRACK") == "1" or not TRACK_URL


def _send_usage_event():
    payload = {
        "events": [{
            "name": "zul_writer",  # GA4 event names allow only [a-zA-Z0-9_]
            "params": {
                "skill_version": SKILL_VERSION
            }
        }]
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"zul-writer-skill/{SKILL_VERSION}"
    }

    req = urllib.request.Request(
        TRACK_URL,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=3):
            pass
    except Exception:
        pass


def track_usage_async(dev: bool = False):
    """Fire the anonymous usage ping on a background thread; returns immediately.

    `dev` is set by --dev, for runs made while developing or testing the skill
    itself. Those runs are not usage of the skill, and counting them would
    overstate how many people the aggregate numbers represent. The notice goes
    to stderr: stdout here is a parsed contract (PNG:/REPORT: lines).
    """
    if dev:
        print("[dev] usage tracking disabled for this run", file=sys.stderr)
        return
    if _tracking_opted_out():
        return
    threading.Thread(target=_send_usage_event, daemon=True).start()


# --- The pinned render helper --------------------------------------------
# Built from zkoss/zkidea's `zk-preview-launcher` module and attached to the ZK
# IntelliJ plugin's own `v<version>` GitHub Release -- launcher and plugin share
# one version line, so the tag in the URL below is the plugin's tag. Pinned by
# exact version AND digest: this is a binary downloaded over the network and then
# executed, so an unverified download is not acceptable.
#
# The digest is specific to the JDK the release was built with (the module fixes
# source/target compatibility, not `--release`), so it must be copied from the
# `.sha256` sidecar published beside the asset -- never from a local rebuild,
# which can differ byte-for-byte while being functionally identical.
#
# To move to a new launcher release, edit these three constants together.
LAUNCHER_VERSION = "1.0.3"
LAUNCHER_SHA256 = "c4eb3096a59f0cbe59a71deb2ae8df86aeb82475939eaf7c1bee4e49488d2bee"
LAUNCHER_URL = (
    "https://github.com/zkoss/zkidea/releases/download/"
    f"v{LAUNCHER_VERSION}/zk-preview-launcher-{LAUNCHER_VERSION}.jar"
)

# ZK CE coordinates for the fallback used when the .zul belongs to no project we
# can resolve. Renders against stock ZK, which is right for a standalone page and
# wrong for one relying on project add-ons — so the output always says which
# classpath source was used.
DEFAULT_ZK_VERSION = "10.2.1"
ZK_CE_REPO = "https://mavensync.zkoss.org/maven2"

MIN_JDK = 17
CACHE_SCHEMA = 2              # bump to invalidate every cached classpath; 2 added "output_roots"
CLASSPATH_TTL_SECONDS = 7 * 24 * 3600
STARTUP_TIMEOUT = 60          # seconds to wait for PREVIEW_PORT=
CONTROLLER_TIMEOUT = 10       # --run-controllers: launcher-side budget, whole render
BUILD_TIMEOUT = 240           # seconds for a mvn/gradle classpath resolution

EXIT_OK, EXIT_RENDER_ERROR, EXIT_SKIPPED, EXIT_USAGE = 0, 1, 2, 3
# Additive on purpose. Exit 1 means "a real defect in the .zul" everywhere in this
# script and in SKILL.md, and a clipped label is not that; reusing 1 would make CI
# report a syntax-error-shaped failure for a cosmetic overflow. 4 is unreachable for
# every existing caller, because it needs --fail-on-layout, which nobody passes today.
EXIT_LAYOUT = 4               # only with --fail-on-layout; STATUS: ok still prints

# Where a failure *of this script* is reported. Deliberately not TRACK_URL above:
# that is an anonymous counter, this is the human issue tracker.
ISSUE_URL = "https://github.com/zkoss/zkidea/issues"


# --- Diagnostics ---------------------------------------------------------
# Every diagnostic goes to STDERR. stdout is the machine-readable contract the
# caller branches on, so --debug must not add a single line to it — otherwise
# turning debugging on would change what the agent parses.

DEBUG = False


def debug(label, value=None):
    if DEBUG:
        print(f"debug: {label}" + ("" if value is None else f": {value}"), file=sys.stderr)


def debug_lines(label, values):
    """A labelled, counted list — the shape wanted for a 60-jar classpath."""
    if not DEBUG:
        return
    items = [str(v) for v in values]
    print(f"debug: {label} ({len(items)})", file=sys.stderr)
    for item in items:
        print(f"debug:     {item}", file=sys.stderr)


def enable_debug(args):
    global DEBUG
    DEBUG = bool(args.debug) or os.environ.get("ZUL_WRITER_DEBUG") == "1"
    debug("argv", " ".join(sys.argv[1:]))
    debug("python", f"{sys.version.split()[0]} on {sys.platform}")
    debug("cache dir", cache_dir())


class Skipped(Exception):
    """No preview is possible, for a reason that is not a defect in the .zul."""

    def __init__(self, reason, next_step=None):
        super().__init__(reason)
        self.reason = reason
        self.next_step = next_step


def cache_dir() -> Path:
    env = os.environ.get("ZUL_WRITER_CACHE_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".cache" / "zul-writer"


def write_json_atomic(path: Path, obj):
    """Two agent runs can race on the same cache entry; never leave a torn file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, indent=1), encoding="utf-8")
    os.replace(tmp, path)


# Both Maven and Gradle bury the actual cause under boilerplate, and Gradle prints
# its most useless lines last -- so a naive "tail of the output" yields
# "BUILD FAILED in 482ms" and nothing a user can act on.
_BUILD_NOISE = (
    "* Try:", "> Run with", "* Get more help", "Get more help", "BUILD FAILED",
    "FAILURE: Build failed", "* Where:", "See https://", "Deprecated Gradle features",
    "You can use '--warning-mode all'", "> Task ", "[ERROR] ->", "[ERROR] For more information",
    "[ERROR] Re-run Maven", "[ERROR] After correcting",
)


def diagnostic_tail(text, limit=3):
    """The most explanatory few lines of a failed build's output."""
    lines = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or any(line.startswith(noise) for noise in _BUILD_NOISE):
            continue
        if line.startswith("* What went wrong:"):
            lines = []              # everything before this was preamble
            continue
        lines.append(line)
    return " / ".join(lines[:limit]) if lines else "no diagnostic output"


def run(cmd, timeout, cwd=None, env=None):
    """Run a helper process, capturing output. Never raises on a non-zero exit.

    Every external command the script issues goes through here, which makes it the
    one place worth instrumenting: under --debug it logs the exact command line, its
    exit code, and — when it failed — the output that `diagnostic_tail` boils down to
    three lines for the normal report."""
    debug("exec", " ".join(str(c) for c in cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                                cwd=cwd, env=env)
    except subprocess.TimeoutExpired:
        result = subprocess.CompletedProcess(cmd, 124, "", f"timed out after {timeout}s")
    except (OSError, ValueError) as e:
        result = subprocess.CompletedProcess(cmd, 127, "", str(e))
    debug("exec rc", result.returncode)
    if DEBUG and result.returncode != 0:
        combined = ((result.stderr or "") + (result.stdout or "")).splitlines()
        debug_lines("exec output (last 40 lines)", combined[-40:])
    return result


# --- Finding a JDK 17+ ---------------------------------------------------
# JAVA_HOME and `which java` are routinely an older JVM even on machines with
# several modern JDKs installed, and the launcher is Java 17 bytecode: an old
# JVM dies with UnsupportedClassVersionError *before* printing a port, which
# looks like a startup timeout. So probe candidates and verify each by running
# it, rather than trusting the environment.

def _java_candidates(explicit):
    if explicit:
        yield Path(explicit)
    env = os.environ.get("ZUL_WRITER_JAVA")
    if env:
        yield Path(env)
    if sys.platform == "darwin":
        r = run(["/usr/libexec/java_home", "-v", f"{MIN_JDK}+"], timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            yield Path(r.stdout.strip()) / "bin" / "java"
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        yield Path(java_home) / "bin" / "java"
    patterns = [
        "/Library/Java/JavaVirtualMachines/*/Contents/Home/bin/java",
        "~/Library/Java/JavaVirtualMachines/*/Contents/Home/bin/java",
        "/usr/lib/jvm/*/bin/java",
        "~/.sdkman/candidates/java/*/bin/java",
        "~/.gradle/jdks/*/bin/java",           # Gradle toolchain auto-downloads
        "C:/Program Files/*/*/bin/java.exe",
    ]
    for pattern in patterns:
        # glob.glob, not Path.glob: it takes absolute patterns (including a Windows
        # drive letter) and simply returns [] when nothing matches.
        for match in sorted(glob.glob(os.path.expanduser(pattern)), reverse=True):
            yield Path(match)
    found = shutil.which("java")
    if found:
        yield Path(found)


def _java_major(exe: Path):
    """(major, banner) for a java executable. `java -version` writes to STDERR."""
    r = run([str(exe), "-version"], timeout=10)
    text = (r.stderr or "") + (r.stdout or "")
    m = re.search(r'version "(\d+)(?:\.(\d+))?', text)
    if not m:
        return None, text.splitlines()[0] if text.strip() else ""
    major = int(m.group(1))
    if major == 1:                       # 1.8.0_x -> 8
        major = int(m.group(2) or 0)
    return major, text.splitlines()[0]


def find_java(explicit):
    cache = cache_dir() / "java.json"
    if not explicit and cache.is_file():
        with contextlib.suppress(Exception):
            entry = json.loads(cache.read_text(encoding="utf-8"))
            exe = Path(entry["exe"])
            if exe.is_file() and entry.get("mtime") == exe.stat().st_mtime:
                debug("java", f"{exe} (cached, Java {entry.get('major')})")
                return exe

    seen, rejected = set(), []
    for candidate in _java_candidates(explicit):
        if not candidate.is_file() or str(candidate) in seen:
            continue
        seen.add(str(candidate))
        major, banner = _java_major(candidate)
        if major is None:
            continue
        debug("java candidate", f"{candidate} -> {banner or f'Java {major}'}")
        if major >= MIN_JDK:
            if not explicit:
                # A one-off --java must not silently become the default for later runs.
                with contextlib.suppress(OSError):
                    write_json_atomic(cache, {"exe": str(candidate), "major": major,
                                              "mtime": candidate.stat().st_mtime})
            debug("java", f"{candidate} (Java {major})")
            return candidate
        rejected.append(f"    Java {major} at {candidate}")
        if explicit:
            break

    detail = "\n".join(rejected[:5]) if rejected else "    (none found)"
    raise Skipped(
        f"no JDK {MIN_JDK}+ found — the ZK renderer needs one.\n  Java installations checked:\n{detail}",
        "install a JDK 17+ (macOS: brew install --cask temurin@21; "
        "Linux: apt install openjdk-21-jdk), or pass --java /path/to/jdk-17/bin/java",
    )


# --- The launcher jar ----------------------------------------------------
# Four sources, first hit wins, and the winner is reported on the LAUNCHER: line.
# Naming it is not cosmetic: "the render looks wrong" and "the render used a jar I
# forgot I had pointed at" are indistinguishable otherwise, and the two hand-pointed
# sources are exactly the ones a caller forgets.

LauncherJar = collections.namedtuple("LauncherJar", "path version source")


def launcher_url(version: str) -> str:
    """The release-asset URL for an arbitrary version. Derived from LAUNCHER_URL by
    substitution rather than re-templated, so repointing LAUNCHER_URL (a mirror, a
    test server) covers every version and not just the pinned one."""
    return LAUNCHER_URL.replace(LAUNCHER_VERSION, version)


def resolve_launcher(explicit, version, warnings) -> LauncherJar:
    """Step 4. --launcher-jar > $ZUL_WRITER_LAUNCHER_JAR > cache > pinned download."""
    if explicit:
        return _pointed_at_launcher(Path(explicit).expanduser(), version,
                                    "--launcher-jar", warnings)
    env = os.environ.get("ZUL_WRITER_LAUNCHER_JAR")
    if env:
        return _pointed_at_launcher(Path(env).expanduser(), version,
                                    "env ZUL_WRITER_LAUNCHER_JAR", warnings)
    return _cached_or_downloaded_launcher(version, warnings)


def _pointed_at_launcher(jar: Path, version, source, warnings) -> LauncherJar:
    """Levels 1-2: a jar the caller named by hand. The digest is still checked, but a
    mismatch only warns — the usual reason to name one is a jar you just built, whose
    bytes cannot match the pin by definition. Failing closed here would make a local
    launcher build unusable, which is the entire point of the override."""
    debug("launcher jar", f"{jar} ({source})")
    if not jar.is_file():
        raise Skipped(f"launcher jar not found at {jar}",
                      "correct --launcher-jar / ZUL_WRITER_LAUNCHER_JAR, or unset it "
                      "to download the pinned release")
    # Only the pinned version has an expected digest; for any other --launcher-version
    # there is nothing here to compare against.
    if version == LAUNCHER_VERSION:
        actual = _sha256(jar)
        if actual != LAUNCHER_SHA256:
            warnings.append(
                f"{jar} is not the pinned launcher {LAUNCHER_VERSION} build — expected "
                f"SHA-256 {LAUNCHER_SHA256}, got {actual}. Used anyway, because it was "
                f"named explicitly; a render difference may be the jar, not the .zul.")
            # And do not go on to call it that version on the LAUNCHER: line. The digest is
            # the only thing that identifies a launcher build -- the jar's manifest carries
            # no version and the cache stores it under a plain name -- so bytes that are not
            # the pinned ones are a build this script cannot name. It used to print the
            # requested version regardless, which meant a run against a locally built 1.0.3
            # announced itself as 1.0.2.
            #
            # Worth more than tidiness now: WARNINGS reads a missing docroot asset as a real
            # defect, and that reading is only true from launcher 1.0.3 onwards. Anyone
            # judging those lines has to know what actually ran, and this line is where they
            # would look.
            return LauncherJar(jar, f"unidentified build sha256:{actual[:12]}", source)
    # A caller-supplied --launcher-version has nothing to check against, so it is reported as
    # given. That is an assertion by the caller rather than a verified fact, and it is the one
    # remaining way this line can name a version nobody proved.
    return LauncherJar(jar, version, source)


def _cached_or_downloaded_launcher(version, warnings) -> LauncherJar:
    """Levels 3-4. Nobody chose these bytes, so nothing unverified is ever executed on
    this path: a digest mismatch is fatal, not advisory."""
    target = cache_dir() / "launcher" / version / "zk-preview-launcher.jar"
    sidecar = target.with_name(f"{target.name}.sha256")
    url = launcher_url(version)
    pinned = version == LAUNCHER_VERSION

    # A --launcher-version this script does not pin has no built-in digest, so the
    # release's own .sha256 is the only reference there is. Same origin as the jar, so
    # it catches a corrupt or truncated download and not a tampered release — hence the
    # warning further down, and hence it is cached beside the jar so that a later run
    # can re-verify offline.
    expected = LAUNCHER_SHA256 if pinned else _read_sidecar_digest(sidecar)

    if target.is_file() and expected and _sha256(target) == expected:
        debug("launcher jar", f"{target} (cached, sha256 verified)")
        if not pinned:
            warnings.append(_release_digest_warning(version))
        return LauncherJar(target, version, "cache")

    if not pinned:
        expected = _fetch_release_digest(url, version)
        warnings.append(_release_digest_warning(version))
    debug("launcher jar", f"downloading {url}")

    target.parent.mkdir(parents=True, exist_ok=True)
    # pid-suffixed so two concurrent runs can't scribble on each other, and never
    # placed at the real path until the digest checks out.
    part = target.with_name(f"{target.name}.part{os.getpid()}")
    digest = hashlib.sha256()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"zul-writer-skill/{SKILL_VERSION}"})
        with urllib.request.urlopen(req, timeout=60) as response, open(part, "wb") as out:
            for chunk in iter(lambda: response.read(65536), b""):
                digest.update(chunk)
                out.write(chunk)
    except urllib.error.HTTPError as e:
        part.unlink(missing_ok=True)
        if e.code == 404:
            raise Skipped(
                f"the pinned launcher release asset does not exist (HTTP 404):\n  {url}",
                "this skill's LAUNCHER_VERSION may be stale — update the zul-writer skill, "
                "or pass --launcher-jar <path to a local jar>",
            )
        raise Skipped(f"could not download the launcher jar (HTTP {e.code})",
                      f"retry later, or download {url} manually to {target}")
    except Exception as e:
        part.unlink(missing_ok=True)
        raise Skipped(
            f"could not download the launcher jar: {e}",
            f"you appear to be offline. Download\n    {url}\n  and save it as\n    {target}\n"
            "  or re-run with --launcher-jar <path>",
        )

    actual = digest.hexdigest()
    if actual != expected:
        part.unlink(missing_ok=True)
        raise Skipped(
            f"the downloaded launcher jar does not match its pinned SHA-256\n"
            f"    expected {expected}\n    got      {actual}\n"
            "  The partial download was deleted and NOT used.",
            "re-run (transient corruption), or pass --launcher-jar <a jar you trust>",
        )
    os.replace(part, target)
    if not pinned:
        # Written only for an unpinned version: the pinned one is re-checked against
        # LAUNCHER_SHA256, which no file on disk can weaken.
        sidecar.write_text(f"{expected}  {target.name}\n", encoding="utf-8")
    debug("launcher jar", f"{target} (downloaded, sha256 {actual})")
    return LauncherJar(target, version, "downloaded")


def _release_digest_warning(version):
    return (f"launcher {version} came from --launcher-version, so it was verified against "
            f"the checksum published beside the release rather than the digest pinned in "
            f"this script — that detects a corrupt download, not a tampered release")


def _read_sidecar_digest(path: Path):
    """The digest cached beside an unpinned download, so a later run re-verifies it
    without the network. None when absent or unreadable — the caller then re-downloads
    rather than trusting an unverifiable file."""
    try:
        fields = path.read_text(encoding="utf-8").split()
    except OSError:
        return None
    return _valid_sha256(fields[0]) if fields else None


def _fetch_release_digest(url, version) -> str:
    """The `.sha256` GitHub publishes beside the asset. Fail closed when it is missing:
    a version whose expected digest cannot be established must not be executed."""
    sidecar_url = f"{url}.sha256"
    fields = []
    try:
        req = urllib.request.Request(sidecar_url,
                                     headers={"User-Agent": f"zul-writer-skill/{SKILL_VERSION}"})
        with urllib.request.urlopen(req, timeout=60) as response:
            fields = response.read(4096).decode("utf-8", "replace").split()
    except Exception as e:
        raise Skipped(
            f"launcher {version} publishes no checksum to verify the download against: {e}\n"
            f"  {sidecar_url}",
            f"drop --launcher-version to use the pinned {LAUNCHER_VERSION}, or pass "
            "--launcher-jar <a jar you trust>",
        )
    digest = _valid_sha256(fields[0]) if fields else None
    if not digest:
        raise Skipped(
            f"the checksum published for launcher {version} is not a SHA-256:\n  {sidecar_url}",
            f"drop --launcher-version to use the pinned {LAUNCHER_VERSION}, or pass "
            "--launcher-jar <a jar you trust>",
        )
    return digest


def _valid_sha256(field: str):
    """A hex digest, lower-cased, or None — never a half-parsed value that would then be
    compared against a real one and silently never match."""
    digest = field.strip().lower()
    if len(digest) != 64 or digest.strip("0123456789abcdef"):
        return None
    return digest


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --- Resolving the ZK classpath ------------------------------------------
# Three entry kinds, in the order the launcher is given them — the same assembly
# the IntelliJ plugin performs in ZulPreviewServerService.launcherClasspath:
#
#  1. EVERY jar, not just the ZK-named ones. Narrowing to zk-* was a shipped
#     crash — ZK's WebManager.<clinit> needs org.slf4j.LoggerFactory. Jars go
#     first so ZK's own bundled web/ resources win any name collision.
#  2. The compiled-output roots, so a page's own <zscript>, use="..." or custom EL
#     function can resolve the project's classes. Passing these does NOT weaken
#     isolation: ViewModels and Composers are blocked by the launcher's UiFactory
#     hook, which never resolves their class name. Test output is excluded.
#  3. Resource roots (src/main/resources), so ZK's `~./` ClassWebResource pages
#     resolve — last, mirroring a real container where WEB-INF/classes is the
#     compiled output with the resources already copied into it.
#
# Excluding the output roots is what the plugin used to do, and it made every page
# whose zscript named a project class fail to render (zkoss/zkidea#67).

BUILD_FILES = ("pom.xml", "build.gradle", "build.gradle.kts")


def _ancestors(start: Path):
    current = start
    while True:
        yield current
        if current.parent == current:      # Path("/").parent == Path("/"): would spin forever
            return
        current = current.parent


def _nearest(start: Path, names):
    for directory in _ancestors(start):
        for name in names:
            if (directory / name).is_file():
                return directory / name
    return None


def _has_zk_core(jars):
    """The launcher needs zk-<version>.jar specifically: VariantDetector byte-scans
    DHtmlLayoutServlet.class out of it. Deliberately not the plugin's broader
    prefix list, which both misses add-ons (calendar-*, ckez-*) and would accept a
    classpath the launcher cannot actually boot."""
    return any(re.match(r"zk-\d", jar.name) for jar in jars)


def _is_test_output(path: Path) -> bool:
    """Test output must never reach the render. The plugin gets this for free from a
    production-only module enumeration; from a CLI we can only match the conventional
    output names: `target/test-classes` (Maven), `build/classes/java/test` (Gradle)."""
    if path.name == "test-classes":
        return True
    return path.name == "test" and "classes" in path.parts


def _partition_classpath(raw_paths, resource_roots):
    """Split a resolved classpath into library jars (the files) and compiled-output
    roots (the directories). Resource roots are passed in separately: a build tool
    reports those from the source tree, not from the classpath."""
    jars, output_roots, seen = [], [], set()
    for entry in raw_paths:
        path = Path(entry)
        if str(path) in seen:
            continue
        if path.is_file():
            seen.add(str(path))
            jars.append(path)
        elif path.is_dir() and not _is_test_output(path):
            seen.add(str(path))
            output_roots.append(path)
    roots = [Path(r) for r in dict.fromkeys(resource_roots) if Path(r).is_dir()]
    return jars, output_roots, roots


def launcher_classpath(resolved):
    """The launcher's --classpath, in contract order: jars, compiled output, resources."""
    return resolved["jars"] + resolved["output_roots"] + resolved["resource_roots"]


def _find_maven(project_dir: Path):
    wrapper = project_dir / ("mvnw.cmd" if os.name == "nt" else "mvnw")
    if wrapper.is_file():
        return str(wrapper)
    return shutil.which("mvn")


def _mvn_build_classpath(mvn, pom: Path, cwd: Path):
    """The recipe proven by the launcher's own test utility (ZkClasspathResolver)."""
    with tempfile.TemporaryDirectory() as tmp:
        out_file = Path(tmp) / "cp.txt"
        # JAVA_HOME is deliberately NOT overridden here: Maven must run on the
        # project's own JDK, not the JDK 17+ we picked for the launcher.
        r = run([mvn, "-f", str(pom), "dependency:build-classpath",
                 f"-Dmdep.outputFile={out_file}", "-q"], timeout=BUILD_TIMEOUT, cwd=str(cwd))
        if r.returncode != 0 or not out_file.is_file():
            return None, f"mvn exited {r.returncode}: {diagnostic_tail(r.stdout or r.stderr)}"
        text = out_file.read_text(encoding="utf-8").strip()
    if not text:
        return None, "mvn produced an empty classpath"
    return [e.strip() for e in text.split(os.pathsep) if e.strip()], None


def resolve_maven(pom: Path):
    project_dir = pom.parent
    mvn = _find_maven(project_dir)
    if not mvn:
        return None, "no mvn (or ./mvnw) available"
    entries, error = _mvn_build_classpath(mvn, pom, project_dir)
    if entries is None:
        return None, error
    # `dependency:build-classpath` lists dependencies only, never the module's own
    # output, so target/classes has to be added by hand. A sibling module in a
    # reactor build arrives as an installed jar among the entries above, so its
    # classes come along that way rather than as another output root.
    entries = list(entries) + [str(project_dir / "target" / "classes")]
    jars, outputs, roots = _partition_classpath(
        entries, [project_dir / "src" / "main" / "resources"])
    return {"kind": "maven", "jars": jars, "output_roots": outputs, "resource_roots": roots,
            "webapp_hint": None, "project_root": project_dir}, None


# A Groovy init script, so it works against Kotlin-DSL builds too: it drives the
# Gradle API rather than the build script's language. Every line we care about is
# ZKCP-prefixed, so daemon and deprecation chatter can be ignored.
GRADLE_INIT = r"""
allprojects { proj ->
    proj.tasks.register('zkPreviewClasspath') { t ->
        t.outputs.upToDateWhen { false }
        t.doLast {
            def dir = proj.projectDir.absolutePath
            def seen = new HashSet<String>()
            def emit = { String kind, File f ->
                if (seen.add(kind + '\u0000' + f.absolutePath))
                    println("ZKCP\t${kind}\t${dir}\t${f.absolutePath}")
            }
            // The war plugin keeps servlet-api and friends OUT of runtimeClasspath
            // (providedCompile/providedRuntime), and compileClasspath carries
            // compileOnly deps. Collect them all: the Python side drops what must
            // not be passed, and wider is the safe direction here.
            ['runtimeClasspath', 'providedRuntime', 'providedCompile', 'compileClasspath'].each { name ->
                def cfg = proj.configurations.findByName(name)
                if (cfg == null || !cfg.canBeResolved) return
                try { cfg.resolve().each { emit('JAR', it) } }
                catch (Throwable e) { println("ZKCP\tWARN\t${dir}\t${name}: ${e.message}") }
            }
            def ss = proj.extensions.findByName('sourceSets')
            def main = (ss == null) ? null : ss.findByName('main')
            if (main != null) main.resources.srcDirs.each { if (it.isDirectory()) emit('RES', it) }
            // Production-only by construction: the `test` source set is a separate
            // object, so build/classes/java/test can never come out of here.
            if (main != null) main.output.classesDirs.each { if (it.isDirectory()) emit('OUT', it) }
            // The war plugin knows the real docroot, so we need not guess it.
            try {
                def war = proj.tasks.findByName('war')
                if (war != null) emit('WEBAPP', proj.file(proj.war.webAppDirName))
            } catch (Throwable ignored) { }
        }
    }
}
"""


def _gradle_executable(project_dir: Path):
    for directory in _ancestors(project_dir):
        wrapper = directory / ("gradlew.bat" if os.name == "nt" else "gradlew")
        if wrapper.is_file():
            return str(wrapper)
    return shutil.which("gradle")


def resolve_gradle(build_file: Path, zul: Path):
    project_dir = build_file.parent
    gradle = _gradle_executable(project_dir)
    if not gradle:
        return None, "no gradlew wrapper or gradle on PATH"

    init_script = cache_dir() / "gradle" / "zk-preview-init.gradle"
    if not init_script.is_file() or init_script.read_text(encoding="utf-8") != GRADLE_INIT:
        init_script.parent.mkdir(parents=True, exist_ok=True)
        init_script.write_text(GRADLE_INIT, encoding="utf-8")

    # No --no-daemon: a warm daemon turns a 60s resolve into ~3s, and a daemon is
    # the user's normal state anyway.
    base = [gradle, "-p", str(project_dir), "-I", str(init_script), "-q",
            "--console=plain", "zkPreviewClasspath"]
    r = run(base, timeout=BUILD_TIMEOUT, cwd=str(project_dir))
    if r.returncode != 0 and "configuration cache" in (r.stderr or "").lower():
        r = run(base + ["--no-configuration-cache"], timeout=BUILD_TIMEOUT, cwd=str(project_dir))
    if r.returncode != 0:
        return None, f"gradle exited {r.returncode}: {diagnostic_tail(r.stderr or r.stdout)}"

    rows = []
    for line in (r.stdout or "").splitlines():
        if line.startswith("ZKCP\t"):
            parts = line.split("\t")
            if len(parts) == 4:
                rows.append((parts[1], Path(parts[2]), parts[3]))
    if not rows:
        return None, "the gradle init script produced no classpath entries"

    # -p runs the task for the project AND its children in a multi-project build.
    # Keep the rows tagged with the project directory that is the *longest*
    # ancestor of the .zul; if none matches, fall back to the union.
    owners = {d for _, d, _ in rows if zul.is_relative_to(d)}
    owner = max(owners, key=lambda d: len(str(d))) if owners else None
    scoped = [row for row in rows if owner is None or row[1] == owner]

    def paths_of(kind):
        return [value for row_kind, _, value in scoped if row_kind == kind]

    webapps = paths_of("WEBAPP")
    jars, outputs, roots = _partition_classpath(
        paths_of("JAR") + paths_of("OUT"), paths_of("RES"))
    webapp_hint = next((Path(w) for w in webapps if Path(w).is_dir()), None)
    return {"kind": "gradle", "jars": jars, "output_roots": outputs, "resource_roots": roots,
            "webapp_hint": webapp_hint, "project_root": owner or project_dir}, None


PROBE_POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.zkoss.zkpreview</groupId>
  <artifactId>zk-preview-probe</artifactId>
  <version>1.0-SNAPSHOT</version>
  <packaging>pom</packaging>
  <dependencies>
    <dependency>
      <groupId>org.zkoss.zk</groupId>
      <artifactId>zkbind</artifactId>
      <version>{zk}</version>
    </dependency>
    <dependency>
      <groupId>{servlet_group}</groupId>
      <artifactId>{servlet_artifact}</artifactId>
      <version>{servlet_version}</version>
      <scope>provided</scope>
    </dependency>
  </dependencies>
  <repositories>
    <repository>
      <id>ZK CE</id>
      <name>ZK CE Repository</name>
      <url>{repo}</url>
    </repository>
  </repositories>
</project>
"""


def resolve_probe(zk_version: str):
    """Stock ZK CE, for a .zul that belongs to no resolvable project. zkbind pulls
    the whole CE stack (zk, zul, zcommon, zweb, zel, zhtml) transitively."""
    mvn = shutil.which("mvn")
    if not mvn:
        return None, "no mvn on PATH to fetch stock ZK"
    jakarta = zk_version.endswith("-jakarta")
    pom_text = PROBE_POM.format(
        zk=zk_version, repo=ZK_CE_REPO,
        servlet_group="jakarta.servlet" if jakarta else "javax.servlet",
        servlet_artifact="jakarta.servlet-api" if jakarta else "javax.servlet-api",
        servlet_version="5.0.0" if jakarta else "4.0.1",
    )
    with tempfile.TemporaryDirectory() as tmp:
        pom = Path(tmp) / "pom.xml"
        pom.write_text(pom_text, encoding="utf-8")
        entries, error = _mvn_build_classpath(mvn, pom, Path(tmp))
    if entries is None:
        return None, error
    jars, outputs, roots = _partition_classpath(entries, [])
    return {"kind": f"probe (stock ZK {zk_version})", "jars": jars, "output_roots": outputs,
            "resource_roots": roots, "webapp_hint": None, "project_root": None}, None


def _cache_key(kind, tracked_files, extra=""):
    parts = [f"schema={CACHE_SCHEMA}", f"kind={kind}", f"extra={extra}"]
    for path in tracked_files:
        with contextlib.suppress(OSError):
            stat = path.stat()
            parts.append(f"{path}|{stat.st_size}|{stat.st_mtime_ns}|{_sha256(path)[:16]}")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:32]


def _tracked_build_files(build_file: Path):
    """Everything whose edit can change the resolved classpath — notably every
    ancestor pom.xml, since a parent POM's dependencyManagement governs versions."""
    tracked = [build_file]
    if build_file.name == "pom.xml":
        for directory in _ancestors(build_file.parent.parent):
            candidate = directory / "pom.xml"
            if candidate.is_file():
                tracked.append(candidate)
    else:
        for name in ("settings.gradle", "settings.gradle.kts", "gradle.properties",
                     "gradle/libs.versions.toml", "gradle/wrapper/gradle-wrapper.properties"):
            for directory in _ancestors(build_file.parent):
                candidate = directory / name
                if candidate.is_file():
                    tracked.append(candidate)
                    break
    return tracked


def _output_marker(build_file: Path) -> str:
    """Which conventional output roots exist, for the cache key. `mvn compile` /
    `gradle classes` creates one without touching any build file, so without this a
    first render in a freshly cloned project caches "no output roots" and every
    <zscript> naming a project class keeps failing until the TTL expires."""
    root = build_file.parent
    conventional = ("target/classes", "build/classes/java/main", "build/classes/kotlin/main")
    return ",".join(d for d in conventional if (root / d).is_dir())


def _load_cached_classpath(key):
    entry_file = cache_dir() / "classpath" / f"{key}.json"
    if not entry_file.is_file():
        return None
    try:
        entry = json.loads(entry_file.read_text(encoding="utf-8"))
    except Exception:
        return None
    if time.time() - entry.get("stamp", 0) > CLASSPATH_TTL_SECONDS:
        return None
    jars = [Path(p) for p in entry["jars"]]
    # A wiped ~/.m2 or a `gradle clean` leaves the key valid but the jars gone.
    if not jars or not all(jar.is_file() for jar in jars):
        return None
    # Output roots are re-checked rather than treated as invalidating: a `clean`
    # removes them without changing any dependency, and a missing directory on
    # --classpath is harmless. Their absence only costs project-class resolution.
    outputs = [Path(p) for p in entry.get("output_roots", []) if Path(p).is_dir()]
    return {"kind": entry["kind"] + " (cached)", "jars": jars, "output_roots": outputs,
            "resource_roots": [Path(p) for p in entry["resource_roots"]],
            "webapp_hint": Path(entry["webapp_hint"]) if entry.get("webapp_hint") else None,
            "project_root": Path(entry["project_root"]) if entry.get("project_root") else None}


def _store_classpath(key, resolved):
    with contextlib.suppress(OSError):
        write_json_atomic(cache_dir() / "classpath" / f"{key}.json", {
            "stamp": time.time(),
            "kind": resolved["kind"],
            "jars": [str(p) for p in resolved["jars"]],
            "output_roots": [str(p) for p in resolved["output_roots"]],
            "resource_roots": [str(p) for p in resolved["resource_roots"]],
            "webapp_hint": str(resolved["webapp_hint"]) if resolved["webapp_hint"] else None,
            "project_root": str(resolved["project_root"]) if resolved["project_root"] else None,
        })


def resolve_classpath(zul: Path, args, warnings):
    """Precedence: explicit → Maven → Gradle → stock-ZK probe POM."""
    if args.classpath:
        jars, outputs, roots = _partition_classpath(args.classpath.split(os.pathsep), [])
        resolved = {"kind": "explicit", "jars": jars, "output_roots": outputs,
                    "resource_roots": roots, "webapp_hint": None, "project_root": None}
        return _require_zk(resolved)

    search_from = Path(args.project).resolve() if args.project else zul.parent
    build_file = _nearest(search_from, BUILD_FILES)
    debug("build file search from", search_from)
    debug("build file", build_file or "none found — falling back to stock ZK")

    if build_file is not None:
        # Only Gradle's result depends on where the .zul sits (which subproject owns it);
        # a Maven classpath is the same for every page, so keying on the directory there
        # would just re-resolve needlessly for each folder.
        scope = "" if build_file.name == "pom.xml" else str(zul.parent)
        key = _cache_key(build_file.name, _tracked_build_files(build_file),
                         f"{scope}|{_output_marker(build_file)}")
        debug("classpath cache", cache_dir() / "classpath" / f"{key}.json")
        if not args.refresh:
            cached = _load_cached_classpath(key)
            debug("classpath cache", "hit" if cached else "miss")
            if cached:
                return _require_zk(cached)

        if build_file.name == "pom.xml":
            resolved, error = resolve_maven(build_file)
        else:
            resolved, error = resolve_gradle(build_file, zul)

        if resolved:
            _store_classpath(key, resolved)
            return _require_zk(resolved)
        warnings.append(f"{build_file.name} classpath resolution failed ({error}) — "
                        "falling back to stock ZK")
        print(f"warning: could not resolve the project classpath from {build_file}: {error}",
              file=sys.stderr)

    resolved, error = resolve_probe(args.zk_version)
    if resolved is None:
        raise Skipped(
            f"no ZK classpath could be resolved for {zul.name} ({error})",
            "run this from inside a Maven or Gradle project that depends on ZK, "
            "install Maven so stock ZK can be fetched, or pass "
            "--classpath <jar1:jar2:...> explicitly",
        )
    return _require_zk(resolved)


def debug_classpath(resolved):
    """The resolved classpath, in the order the launcher receives it. This is the single
    most useful thing to see when a render fails: a missing add-on jar, a stale probe
    fallback and an uncompiled project all look identical from the outside."""
    if not DEBUG:
        return
    debug("classpath source", resolved["kind"])
    debug_lines("classpath jars", resolved["jars"])
    debug_lines("classpath output roots", resolved["output_roots"])
    debug_lines("classpath resource roots", resolved["resource_roots"])
    debug("classpath webapp hint", resolved["webapp_hint"] or "none")
    debug("classpath project root", resolved["project_root"] or "none")


def _require_zk(resolved):
    # Dumped before the gate, not after: the gate's own failure is the case where
    # seeing the entries matters most.
    debug_classpath(resolved)
    if not _has_zk_core(resolved["jars"]):
        raise Skipped(
            f"no ZK core jar (zk-<version>.jar) on the resolved classpath [{resolved['kind']}] — "
            "the renderer has nothing to render with",
            "add a ZK dependency to the project, or pass --classpath with the ZK jars",
        )
    return resolved


# --- Resolving the docroot -----------------------------------------------
# A port of the IntelliJ plugin's DocrootResolver. The docroot matters twice:
# the request path is the .zul relativized against it, AND the launcher refuses
# to serve anything resolving outside it, so a `../` path cannot work.

def resolve_docroot(zul: Path, boundary_roots, resource_roots, webapp_hint):
    if webapp_hint and zul.is_relative_to(webapp_hint):
        return webapp_hint, "WAR webapp (from the gradle war plugin)"

    parent = zul.parent
    for candidate in _ancestors(parent):
        if boundary_roots and not any(candidate.is_relative_to(r) for r in boundary_roots):
            break
        if (candidate / "WEB-INF").is_dir() or candidate.name.lower() == "webapp":
            return candidate, "WAR webapp"
    resource_set = {Path(r) for r in resource_roots}
    for candidate in _ancestors(parent):
        # `web` is a fixed ZK convention (ClassWebResource /web), so match exactly.
        if candidate.name == "web" and candidate.parent in resource_set:
            return candidate, "Spring Boot classpath web"
    for root in boundary_roots:
        if parent.is_relative_to(root):
            return root, "content-root fallback"
    return parent, "file-parent fallback"


def boundary_roots_for(zul: Path, args, resolved):
    if args.project:
        return [Path(args.project).resolve()]
    if resolved["project_root"]:
        return [Path(resolved["project_root"])]
    r = run(["git", "-C", str(zul.parent), "rev-parse", "--show-toplevel"], timeout=10)
    if r.returncode == 0 and r.stdout.strip():
        return [Path(r.stdout.strip())]
    return []


# --- The launcher process ------------------------------------------------

PORT_RE = re.compile(r"PREVIEW_PORT=(\d+)")


class Launcher:
    def __init__(self, java: Path, jar: Path, entries, docroot: Path,
                 run_controllers=False, controller_timeout=CONTROLLER_TIMEOUT):
        self.java, self.jar, self.entries, self.docroot = java, jar, entries, docroot
        self.run_controllers, self.controller_timeout = run_controllers, controller_timeout
        self.proc = None
        self.port = None
        self._stderr_tail = collections.deque(maxlen=200)
        self._stdout_lines = queue.Queue()

    def __enter__(self):
        argv = [str(self.java), "-jar", str(self.jar),
                "--classpath", os.pathsep.join(str(p) for p in self.entries),
                "--webapp", str(self.docroot), "--port", "0"]
        if self.run_controllers:
            # Appended only in this mode, so the default invocation stays byte-identical to
            # what every existing caller (and every captured baseline) already produces.
            argv += ["--isolation", "off", "--controller-timeout", str(self.controller_timeout)]
        debug_lines("renderer argv", argv)
        # Own process group, so the whole tree can be killed rather than just the pid.
        spawn = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
                 else {"start_new_session": True})
        self.proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, bufsize=1, **spawn)
        atexit.register(self.kill)
        # Both pipes MUST be drained: a chatty ZK bootstrap can fill the 64 KB pipe
        # buffer and wedge the JVM before it ever prints a port, which is
        # indistinguishable from a startup timeout.
        self._pump(self.proc.stdout, self._stdout_lines.put, "renderer out")
        self._pump(self.proc.stderr, self._stderr_tail.append, "renderer err")
        self.port = self._await_port()
        debug("renderer port", self.port)
        return self

    @staticmethod
    def _pump(stream, sink, label):
        def drain():
            with contextlib.suppress(Exception):
                for line in stream:
                    text = line.rstrip("\n")
                    # Under --debug the renderer's whole output is echoed, not just the
                    # 6-line tail a failure report can afford.
                    debug(label, text)
                    sink(text)
        threading.Thread(target=drain, daemon=True).start()

    def _await_port(self):
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Skipped(f"the render server did not start within {STARTUP_TIMEOUT}s"
                              + self._stderr_hint(),
                              "re-run; if it persists the ZK jars on the classpath may be incomplete")
            try:
                line = self._stdout_lines.get(timeout=min(remaining, 0.25))
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise Skipped(
                        f"the render server exited (rc={self.proc.returncode}) before serving"
                        + self._stderr_hint(),
                        "check that the classpath carries a complete, consistent set of ZK jars",
                    )
                continue
            match = PORT_RE.search(line)
            if match:
                return int(match.group(1))

    def _stderr_hint(self):
        tail = [line for line in self._stderr_tail if line.strip()][-6:]
        return ("\n  Renderer output:\n" + "\n".join(f"    {line}" for line in tail)) if tail else ""

    def __exit__(self, *exc):
        self.kill()

    def kill(self):
        if self.proc is None or self.proc.poll() is not None:
            return
        try:
            if os.name == "nt":
                self.proc.terminate()
            else:
                # SIGTERM first: the launcher installs a shutdown hook.
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            self.proc.wait(timeout=5)
        except Exception:
            with contextlib.suppress(Exception):
                if os.name == "nt":
                    self.proc.kill()
                else:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)


# --- Probing the rendered DOM --------------------------------------------
# The LAYOUT audit answers "is this element the wrong size"; a probe answers "why".
# Both read the same post-mount DOM, and that DOM is the only place a ZK page exists as
# markup: the served response is a `zkmx([...])` bootstrap that merely restates the .zul,
# so the class names, the fonts and the boxes all come into being client-side.
PROBE_MATCH_CAP = 10      # elements reported per selector
PROBE_HTML_CAP = 200      # characters of the opening tag per element

PROBE_JS = """([selector, matchCap, htmlCap]) => {
  let nodes;
  try {
    nodes = Array.from(document.querySelectorAll(selector));
  } catch (e) {
    // A malformed selector is the caller's typo, not a failed render: it comes back as
    // data on this object and is printed as such, never raised.
    return {error: String((e && e.message) || e)};
  }
  const shown = nodes.slice(0, matchCap).map((el) => {
    const cs = getComputedStyle(el);
    const before = getComputedStyle(el, '::before');
    const r = el.getBoundingClientRect();
    // The OPENING TAG only. A probe reports the element, not the subtree under it, and one
    // grid row's full outerHTML would bury the line the reader came for.
    const cut = el.outerHTML.indexOf('>');
    const open = cut === -1 ? el.outerHTML : el.outerHTML.slice(0, cut + 1);
    return {
      html: open.length > htmlCap ? open.slice(0, htmlCap) + '\u2026' : open,
      rect: {x: Math.round(r.x), y: Math.round(r.y),
             w: Math.round(r.width), h: Math.round(r.height)},
      styles: {display: cs.display, position: cs.position, overflow: cs.overflow,
               fontFamily: cs.fontFamily, color: cs.color,
               backgroundColor: cs.backgroundColor,
               width: cs.width, height: cs.height, flex: cs.flex},
      // Reported only when there IS one. `content: none` is every ordinary element, and
      // printing it for all of them would bury the case this line exists for: an icon
      // glyph asked for in a font that cannot draw it.
      before: (before.content && before.content !== 'none')
              ? {content: before.content, fontFamily: before.fontFamily} : null,
    };
  });
  return {total: nodes.length, elements: shown};
}"""


def dom_dump_path(args, out_path: Path):
    """None when --dump-dom was not passed; otherwise beside the PNG, which is the rule
    --report json already follows and the only place a caller can predict without being told.

    The flag deliberately takes NO value. An optional one (`nargs="?"`) reads well in a help
    text and is a trap on the command line: `--dump-dom page.zul` is how anyone would type it,
    and argparse hands `page.zul` to the flag as its path, leaving the .zul positional empty
    and the run dead at exit 3. Layer A caught it. --out places the PNG and this together."""
    if not args.dump_dom:
        return None
    return out_path.with_suffix(".dom.html")


# --- Capture -------------------------------------------------------------

# ZK's client engine builds the DOM after load; the served HTML is mostly a loader
# for it. These flags are set at the end of ZK's initial mount pipeline and have been
# stable client API since ZK 5, so this covers ZK 9 and 10 alike. It reads window.zk
# defensively, so it is also false on a page that has no ZK on it at all.
ZK_READY = """() => {
  const z = window.zk;
  return !!z && z.booted === true && z.mounting !== true && !z.loading && z.processing !== true;
}"""

# Every ZK-served page fetches its client engine from under this path, and nothing else does.
# It is what separates "a ZK page still mounting" from "not a ZK page", and it is read from the
# HTML the server sent rather than from the live page -- see capture() for why that matters.
ZKAU_PATH = "/zkau/"


# --- Settling JS-driven animation ----------------------------------------
# Playwright's screenshot(animations="disabled") covers CSS animations and transitions and
# nothing else. A charting library draws its entry animation from requestAnimationFrame onto SVG
# attributes -- zkcharts/Highcharts widens an SVG clip rect over ~1000ms -- so that flag never
# touches it, and until this existed nothing in the wait sequence asked whether the page had
# stopped moving: ZK_READY watches ZK's mount, networkidle watches the network, fonts.ready
# watches fonts. A capture could therefore be of a half-drawn chart, and the LAYOUT audit would
# measure mid-flight geometry as if it were the final page.
#
# Provenance, because it matters for how much to trust this: the symptom was observed during a
# skill evaluation, where one page cost six diagnostic renders before the truncated chart was
# understood. It does NOT reproduce in the fixture suite on this machine -- chart-animation.zul
# settles before the capture either way -- so what is closed here is a race that is real by
# construction rather than a failure reproduced on demand. The regression sample asserts the
# property that matters (two captures, same bytes) instead of the symptom.
#
# Two defences, because neither alone is enough:
#
#   1. ANIMATION_OFF_JS turns the animation off before it can start. Free, and it is the only
#      one that makes the *first* frame final -- which is what the audit needs.
#   2. _settle() refuses to shoot while the pixels are still moving. Costs a little time and
#      knows nothing about any library, so it also covers whatever animates next.

# Injected with add_init_script, so it runs in a fresh document BEFORE any of the page's own
# scripts. That timing is the whole trick, and specifically because of how zkcharts uses
# Highcharts' globals: Charts.src.js snapshots `Highcharts.getOptions()` into its own
# DefaultOptions at module load, and resetOptions() restores that snapshot before every chart
# is built (zkcharts 12.2.0.0 Charts.src.js:50-58, :146-156). Calling setOptions() after the
# page has loaded is therefore erased by the next chart; setting it before the snapshot is
# taken puts `animation: false` INSIDE the snapshot, so every reset restores it.
#
# Highcharts is not present yet at init time, so the assignment itself is what is intercepted.
# The accessor is configurable and keeps the value, so a later reassignment still works and any
# reader sees the real library -- this cannot break a page that has no charts on it.
ANIMATION_OFF_JS = """(() => {
  const off = (H) => {
    try {
      if (!H || H.__zulWriterAnimationOff || typeof H.setOptions !== 'function') return H;
      H.__zulWriterAnimationOff = true;
      // chart.animation covers redraws, plotOptions.series.animation covers the entry
      // animation of each series -- the second is the one that truncates a line chart, and
      // chart-level setAnimation(false) alone does NOT suppress it.
      H.setOptions({chart: {animation: false},
                    plotOptions: {series: {animation: false}}});
    } catch (e) {}
    return H;
  };
  let value = window.Highcharts;
  try {
    Object.defineProperty(window, 'Highcharts', {
      configurable: true,
      enumerable: true,
      get() { return value; },
      set(v) { value = off(v); },
    });
  } catch (e) { return; }
  if (value) off(value);
})()"""

# The still-frame gate. A screenshot is the signature deliberately: the thing being promised is
# that the delivered PNG is reproducible, so comparing PNGs is the promise itself rather than a
# proxy for it. Any cheaper signature -- an attribute scrape, an rAF counter -- would be a guess
# about which properties an animation touches.
#
# Same flags as the real capture (see capture()), so the frames compared are the frames that
# would be delivered. Never full_page: this is the viewport only, which keeps the probe cheap
# on a long page while still catching anything moving above the fold.
SETTLE_INTERVAL_MS = 120     # long enough that a 1s entry animation moves visibly between frames
SETTLE_BUDGET_MS = 2000      # a perpetual animation is capped here and warned about, not waited on


def _settle(page, warnings):
    """Hold until two consecutive frames are identical, or the budget runs out.

    A still page pays one extra viewport screenshot plus one interval -- measured at 260-350ms
    across the fixtures, against renders that take seconds. A page that never settles is captured
    anyway and the caller is TOLD, because a mid-animation image the author knows about costs one
    glance, and one they do not know about cost six diagnostic renders in the evaluation this
    came from.
    """
    started = time.monotonic()
    deadline = started + SETTLE_BUDGET_MS / 1000
    previous = page.screenshot(animations="disabled", caret="hide")
    frames = 1
    while time.monotonic() < deadline:
        page.wait_for_timeout(SETTLE_INTERVAL_MS)
        current = page.screenshot(animations="disabled", caret="hide")
        frames += 1
        if current == previous:
            debug("settle", f"still after {frames} frames, "
                            f"{(time.monotonic() - started) * 1000:.0f} ms")
            return True
        previous = current
    debug("settle", f"still moving after {frames} frames, "
                    f"{(time.monotonic() - started) * 1000:.0f} ms")
    warnings.append(
        f"the page was still changing after {SETTLE_BUDGET_MS}ms — it was captured anyway, so "
        "the image and the LAYOUT findings may show an animation in progress")
    return False


# --- Layout audit --------------------------------------------------------
# What the browser knows exactly and a reader of the PNG has to guess: whether a
# label is one character short, whether a link collapsed to nothing, whether the
# page needs a horizontal scrollbar. Same shape as ZK_READY above — one script
# handed to page.evaluate — and it runs AFTER the screenshot (see capture()), so
# it can never influence the image it is explaining.

LAYOUT_PRINT_CAP = 25       # spec P1-3: cap the printed list, never truncate silently
LAYOUT_COLLECT_CAP = 200    # bounds the payload crossing the CDP boundary; `total` stays truthful
CONSOLE_WARNING_CAP = 10    # spec P1-4: console findings are "deduped, capped at 10"
ASSET_WARNING_CAP = 10      # one line per missing asset, then a truthful "and N more"
# Deliberately no collect cap beside it. LAYOUT_COLLECT_CAP bounds one payload crossing the
# CDP boundary in a single page.evaluate; console messages arrive one at a time and are
# snipped to one line on arrival, so the dedupe alone bounds memory and the "and N more"
# count stays exactly truthful.

# The rules run in precedence order and a node that produced a finding is `claimed`,
# so one defect yields one line: without that, a width-0 link reports as zero-size AND
# as clipped-text. viewport-overflow is exempt because it is a document-level rule —
# suppressing it because its widest offender was already claimed would throw away the
# one finding that explains a horizontal scrollbar.
LAYOUT_AUDIT_JS = """(collectCap) => {
  const zk = window.zk;
  const findings = [], seen = new Set(), claimed = new Set();
  let total = 0;
  const px = (v) => Math.round(v);
  const all = Array.prototype.slice.call(document.querySelectorAll('body *'));
  // getComputedStyle is the audit's hot call and the ancestor walks re-ask for the same
  // elements over and over; memoizing it is what keeps a 12-finding page inside the budget.
  const styles = new WeakMap();
  const style = (el) => {
    if (styles.has(el)) return styles.get(el);
    let cs = null;
    try { cs = getComputedStyle(el); } catch (e) { cs = null; }
    styles.set(el, cs);
    return cs;
  };

  // display:none gives a subtree no boxes at all, so every descendant would measure
  // 0x0. A deliberately hidden region is not a layout defect.
  const hiddenCache = new WeakMap();
  const hiddenSomewhere = (el) => {
    if (hiddenCache.has(el)) return hiddenCache.get(el);
    let hidden = false;
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      if (n.hasAttribute && n.hasAttribute('hidden')) { hidden = true; break; }
      const cs = style(n);
      if (cs && (cs.display === 'none' || cs.visibility === 'hidden')) { hidden = true; break; }
    }
    hiddenCache.set(el, hidden);
    return hidden;
  };

  const ownTextNodes = (el) => {
    const out = [];
    for (let i = 0; i < el.childNodes.length; i++) {
      const n = el.childNodes[i];
      if (n.nodeType === 3 && n.nodeValue && n.nodeValue.trim()) out.push(n);
    }
    return out;
  };
  const ownText = (el) => ownTextNodes(el).map((n) => n.nodeValue).join(' ')
                                          .replace(/\\s+/g, ' ').trim();

  // --- locator -----------------------------------------------------------
  // `div#zk_comp_37` is useless to whoever has to fix the page, so every finding is
  // resolved back to the ZK widget that OWNS the node. No $n()===el test here on
  // purpose: the text-bearing node is often ZK's inner chrome, and the owning widget
  // is the answer the reader needs (`listheader[label="Done"]`, not `div "Done"`).
  const widgetOf = (el) => {
    try { return (zk && zk.Widget && zk.Widget.$) ? zk.Widget.$(el) : null; } catch (e) { return null; }
  };
  const isWidgetRoot = (el, w) => { try { return !!w && w.$n() === el; } catch (e) { return false; } };
  const zulTag = (w) => {
    const cls = String(w.className || w.widgetName || '');
    const last = cls.substring(cls.lastIndexOf('.') + 1);
    return last ? last.toLowerCase() : 'widget';
  };
  // Client-side widget state lives behind a generated getter with the value in `_name`,
  // so both are tried before giving up on an attribute.
  const prop = (w, name) => {
    const getter = 'get' + name.charAt(0).toUpperCase() + name.slice(1);
    try {
      if (typeof w[getter] === 'function') {
        const v = w[getter]();
        if (v != null && String(v) !== '') return String(v);
      }
      const f = w['_' + name];
      if (f != null && String(f) !== '') return String(f);
    } catch (e) {}
    return '';
  };
  const snip = (s, n) => (s.length > n ? s.slice(0, n - 1) + '\\u2026' : s);
  const cssClass = (el) => {
    const list = (el.className && el.className.split) ? el.className.split(/\\s+/).filter(Boolean) : [];
    for (const c of list) if (c.indexOf('z-') !== 0) return '.' + c;
    return list.length ? '.' + list[0] : '';
  };
  const locator = (el) => {
    const w = widgetOf(el);
    if (w) {
      const tag = zulTag(w);
      // w.id is the ZUL id and stays empty unless the author wrote one; the generated
      // id lives in w.uuid, and ZK copies it into id for a few widgets — hence the
      // inequality test. `label#pQr51` would be worse than no locator at all.
      if (w.id && w.id !== w.uuid) return tag + '#' + w.id;
      const attrs = ['label', 'value', 'title', 'placeholder'];
      for (let i = 0; i < attrs.length; i++) {
        const v = prop(w, attrs[i]);
        if (v) return tag + '[' + attrs[i] + '="' + snip(v, 40) + '"]';
      }
      const t = ownText(el);
      return tag + cssClass(el) + (t ? ' "' + snip(t, 30) + '"' : '');
    }
    const t = ownText(el);
    return el.tagName.toLowerCase() + cssClass(el) + (t ? ' "' + snip(t, 30) + '"' : '');
  };

  const record = (rule, el, detail, measured) => {
    const loc = locator(el);
    // Claim the node BEFORE the dedupe return: a second element sharing a locator is
    // still a node this rule matched, so it must not fall through to a later rule.
    // Two identical collapsed <a label="Settings"/> otherwise print one zero-size line
    // and one clipped-text line for what is one defect repeated.
    claimed.add(el);
    const key = rule + '|' + loc;
    if (seen.has(key)) return;      // dedupe by (rule, locator), insertion order kept
    seen.add(key);
    total += 1;
    if (findings.length < collectCap) {
      findings.push({rule: rule, locator: loc, detail: detail, measured: measured || {}});
    }
  };

  // Only `hidden` and `clip` count as clipping.
  // `auto` and `scroll` are deliberately NOT clippers: a scrollable region reaches
  // its content, so it is not a layout defect — and ZK's Grid/Listbox bodies are
  // overflow:auto, so the spec's literal "overflow is not visible" would fire on
  // every row of every data table in the corpus.
  const HARD = {hidden: 1, clip: 1};
  // EVERY clipping ancestor, intersected, and per axis -- not just the nearest one. What a text
  // run is actually visible inside is the intersection: a roomy overflow:hidden box nested in a
  // narrow one shows only what the narrow one allows, so stopping at the first clipper found
  // reported plainly cut text as fully visible. That was a false negative in the direction this
  // rule can least afford, because the LAYOUT block is documented to the agent as the browser's
  // own measurement -- an author who trusts it stops looking.
  //
  // Per axis because `overflow-x: hidden; overflow-y: auto` is real and common -- ZK's own mesh
  // bodies are built that way -- and folding it into one rectangle would clip vertically where
  // the browser actually scrolls, inventing a finding on every data table in the corpus.
  //
  // The walk narrows once it crosses an out-of-flow box: an absolutely positioned element is
  // clipped only by ancestors in its containing-block chain, and a fixed one by almost nothing,
  // so both are handled by dropping ancestors rather than by keeping them. Reaching further up
  // is only safe while it stays on the under-reporting side of the line.
  const clipRegionOf = (el) => {
    let left = -Infinity, right = Infinity, top = -Infinity, bottom = Infinity;
    let nearest = null, count = 0, needsPositioned = false;
    for (let n = el; n && n.nodeType === 1 && n !== document.documentElement; n = n.parentElement) {
      const cs = style(n);
      if (!cs) continue;
      // Not text-overflow:ellipsis on its own: CSS gives that property no effect at all
      // while overflow is visible, so a box that really elides its text is already a
      // hidden|clip box and is caught here.
      const clips = HARD[cs.overflowX] || HARD[cs.overflowY];
      if (clips && (n === el || !needsPositioned || cs.position !== 'static')) {
        const box = paddingBox(n, cs);
        if (HARD[cs.overflowX]) {
          left = Math.max(left, box.left); right = Math.min(right, box.right);
        }
        if (HARD[cs.overflowY]) {
          top = Math.max(top, box.top); bottom = Math.min(bottom, box.bottom);
        }
        if (!nearest) nearest = {el: n, cs: cs};
        count += 1;
      }
      // Its own overflow has already been applied above; what stops here is the claim that
      // anything ABOVE a fixed box still clips it.
      if (cs.position === 'fixed') break;
      if (cs.position === 'absolute') needsPositioned = true;
    }
    return nearest ? {left: left, right: right, top: top, bottom: bottom,
                      nearest: nearest, count: count} : null;
  };
  const hasBoxInside = (el) => {
    const kids = el.querySelectorAll('*');
    for (let i = 0; i < kids.length; i++) {
      const r = kids[i].getBoundingClientRect();
      if (r.width > 0.5 && r.height > 0.5) return true;
    }
    return false;
  };
  // The PADDING box, and this is the single most important measurement in the audit:
  // `overflow: hidden` clips to the padding box, not to the content box, so text may
  // spill out of the content box into the padding and still be fully visible. Measured:
  // ZK's div.z-listheader-content is 60px wide with 16px padding either side, so a 38px
  // "Done" overflows its 28px content box while the browser clips at 60px and the header
  // renders in full. Comparing against the content box reported it as truncated.
  // It is also what spec P1-3 asks escapes-parent to compare against.
  const paddingBox = (el, cs) => {
    const r = el.getBoundingClientRect();
    const n = (k) => parseFloat(cs.getPropertyValue(k)) || 0;
    return {
      left: r.left + n('border-left-width'),
      right: r.right - n('border-right-width'),
      top: r.top + n('border-top-width'),
      bottom: r.bottom - n('border-bottom-width'),
    };
  };

  // --- ink ---------------------------------------------------------------
  // Does anything RENDERABLE fall inside a rectangle? This is what separates a box whose edge
  // pokes out of its clipping parent from content the reader actually loses, and rule 3 needs
  // the distinction: measured on a status bar built as `hlayout` > inline-block dot + label
  // inside a borderlayout south, the hlayout's box overflows the region by a constant while
  // every pixel it contains stays visible, because the line box is taller than its own content.
  // That finding was reported identically at south heights 34, 52 and 64 -- an agent told to
  // trust the list has no way to act on a number that does not move.
  const TRANSPARENT = /^rgba\\(.*,\\s*0(\\.0+)?\\)$/;
  const paints = (el, cs) => {
    if (!cs) return false;
    const bg = cs.backgroundColor;
    if (bg && bg !== 'transparent' && !TRANSPARENT.test(bg)) return true;
    if (cs.backgroundImage && cs.backgroundImage !== 'none') return true;
    const edges = ['Top', 'Right', 'Bottom', 'Left'];
    for (let i = 0; i < edges.length; i++) {
      if (cs['border' + edges[i] + 'Style'] !== 'none' &&
          parseFloat(cs['border' + edges[i] + 'Width']) > 0) return true;
    }
    return false;
  };
  // More than a hairline of real overlap, so a box that merely touches the strip edge does not
  // count as falling inside it.
  const overlaps = (r, s) => (Math.min(r.right, s.right) - Math.max(r.left, s.left) > 1) &&
                             (Math.min(r.bottom, s.bottom) - Math.max(r.top, s.top) > 1);
  const inkInside = (el, strip) => {
    if (paints(el, style(el))) return true;
    const nodes = ownTextNodes(el);
    if (nodes.length) {
      const range = document.createRange();
      range.setStartBefore(nodes[0]);
      range.setEndAfter(nodes[nodes.length - 1]);
      if (overlaps(range.getBoundingClientRect(), strip)) return true;
    }
    // Only reached for a candidate finding, which is rare, so the subtree walk is affordable.
    const kids = el.querySelectorAll('*');
    for (let i = 0; i < kids.length; i++) {
      const kid = kids[i];
      if (hiddenSomewhere(kid)) continue;
      if (!overlaps(kid.getBoundingClientRect(), strip)) continue;
      if (ownText(kid) || paints(kid, style(kid))) return true;
    }
    return false;
  };

  // --- rule 1: zero-size -------------------------------------------------
  // ZK WIDGET ROOTS ONLY. ZK's own chrome legitimately measures 0x0 — div.z-hlayout-inner
  // around an empty label does — and without this restriction a correct page reports
  // that chrome as a defect.
  // Rect-based, not clientWidth-based: clientWidth is 0 by CSS definition on
  // display:inline boxes, which is exactly what ZK renders <label> and <a> as, so the
  // spec's literal `clientWidth === 0` reported a plainly visible 14.9x20 icon link.
  for (let i = 0; i < all.length; i++) {
    const el = all[i];
    // Cheapest test first: zk.Widget.$() walks the DOM upwards, so it is only worth
    // asking about the handful of elements that actually measure zero.
    const r = el.getBoundingClientRect();
    if (r.width > 0.5 && r.height > 0.5) continue;
    if (hiddenSomewhere(el)) continue;
    if (!isWidgetRoot(el, widgetOf(el))) continue;
    const text = ownText(el);
    // Renderable content is text OR children, not the spec's `childElementCount > 0`:
    // a collapsed <a label="Settings"/> has zero element children, and it is the very
    // defect this rule is cited for.
    if (!text && el.childElementCount === 0) continue;
    // A widget root that does not clip and whose subtree still has a real box has not
    // vanished — the box simply lives one level down. Measured: every ZK borderlayout
    // region root (zul.layout.North and friends) is a class-less wrapper at 1270x0 whose
    // child div.z-north is 1270x60 and plainly visible. Without this test a correct
    // borderlayout page reports four findings. The clipping case is kept, because a
    // 0x0 overflow:hidden box really does erase whatever measures inside it.
    const cs = style(el);
    if (!(cs && (HARD[cs.overflowX] || HARD[cs.overflowY])) && hasBoxInside(el)) continue;
    record('zero-size', el,
           px(r.width) + 'x' + px(r.height) +
             (text ? ' with text but no box' : ' with ' + el.childElementCount + ' children'),
           {width: r.width, height: r.height, textLength: text.length,
            children: el.childElementCount});
  }

  // --- rule 2: clipped-text ----------------------------------------------
  // Measured on the nearest CLIPPING box, not on the text element itself: ZK renders
  // <label> and <a> as display:inline, where clientWidth and scrollWidth are both 0,
  // so the spec's `scrollWidth > clientWidth + 1` can never fire on a clipped brand
  // name (measured: label[value="GovPortal"] at clientWidth 0, rect 90x23). CSS
  // overflow does not apply to inline non-replaced boxes either, so the clipping box
  // always has real scrollWidth/clientWidth numbers — both are carried in `measured`.
  for (let i = 0; i < all.length; i++) {
    const el = all[i];
    if (claimed.has(el)) continue;
    const nodes = ownTextNodes(el);
    if (!nodes.length || hiddenSomewhere(el)) continue;
    const clip = clipRegionOf(el);
    if (!clip) continue;
    // A Range measures the text run exactly where it already is — no node inserted,
    // no style written. That is what keeps the audit non-mutating.
    const range = document.createRange();
    range.setStartBefore(nodes[0]);
    range.setEndAfter(nodes[nodes.length - 1]);
    const t = range.getBoundingClientRect();
    if (t.width <= 0.5 && t.height <= 0.5) continue;
    const boxW = clip.right - clip.left, boxH = clip.bottom - clip.top;
    // Edge by edge against the clip rectangle, with a 1px tolerance for sub-pixel text
    // metrics. Position matters as much as size: a run narrower than the box is still cut
    // when it starts inside the padding and ends past the far edge, which is exactly how
    // a listcell truncates its own label. An axis nobody clips stays infinite here, so its
    // two edges evaluate to -Infinity and can never win the `cut` comparison below.
    const past = {left: clip.left - t.left, right: t.right - clip.right,
                  top: clip.top - t.top, bottom: t.bottom - clip.bottom};
    let side = '', cut = 0;
    for (const edge in past) if (past[edge] > cut) { side = edge; cut = past[edge]; }
    if (cut <= 1) continue;
    const vertical = (side === 'top' || side === 'bottom');
    const need = vertical ? t.height : t.width;
    const boxSize = vertical ? boxH : boxW;
    record('clipped-text', el,
           need > boxSize + 1
             ? 'text needs ' + px(need) + 'px, box is ' + px(boxSize) + 'px'
             : 'text is ' + px(cut) + 'px past the ' + side + ' edge of the ' +
               px(boxSize) + 'px box',
           {axis: vertical ? 'y' : 'x', side: side, cut: cut,
            textWidth: t.width, textHeight: t.height,
            // null, not Infinity, on an axis nobody clips: `measured` is serialised into the
            // --report JSON, and Infinity has no representation there.
            boxWidth: isFinite(boxW) ? boxW : null, boxHeight: isFinite(boxH) ? boxH : null,
            clippers: clip.count,
            clipperScrollWidth: clip.nearest.el.scrollWidth,
            clipperClientWidth: clip.nearest.el.clientWidth});
  }

  // --- rule 3: escapes-parent --------------------------------------------
  // offsetParent skips statically-positioned ancestors, so this rule systematically
  // under-reports rather than over-reports. Under-reporting is the safe direction for
  // a list an agent is told to trust.
  for (let i = 0; i < all.length; i++) {
    const el = all[i];
    if (claimed.has(el) || hiddenSomewhere(el)) continue;
    let op = null;
    try { op = el.offsetParent; } catch (e) { op = null; }
    if (!op || op === document.body || op === document.documentElement) continue;
    const cs = style(op);
    if (!cs || !(HARD[cs.overflowX] || HARD[cs.overflowY])) continue;
    const r = el.getBoundingClientRect();
    if (r.width <= 0.5 && r.height <= 0.5) continue;
    const box = paddingBox(op, cs);
    const sides = [['left', box.left - r.left], ['right', r.right - box.right],
                   ['top', box.top - r.top], ['bottom', r.bottom - box.bottom]];
    let side = '', over = 0;
    for (let k = 0; k < sides.length; k++) if (sides[k][1] > over) { side = sides[k][0]; over = sides[k][1]; }
    if (over <= 2) continue;
    // The strip that the parent cuts away, and the judgement call this rule turns on: report it
    // only when something is rendered in there. A bare box edge crossing the boundary costs the
    // reader nothing and cannot be fixed by the one move the message invites -- give the parent
    // more room -- because the child's box grows with it and the number never changes. Silence
    // here is the same under-reporting bias the offsetParent walk already accepts.
    const strip = {left: r.left, right: r.right, top: r.top, bottom: r.bottom};
    if (side === 'bottom') strip.top = box.bottom;
    else if (side === 'top') strip.bottom = box.top;
    else if (side === 'right') strip.left = box.right;
    else strip.right = box.left;
    if (!inkInside(el, strip)) continue;
    record('escapes-parent', el,
           'escapes clipping parent ' + locator(op) + ' by ' + px(over) + 'px on the ' + side,
           {side: side, overflow: over, parent: locator(op)});
  }

  // --- rule 5: icon-not-rendered -----------------------------------------
  // A font icon that renders as an empty box, decided by measurement rather than by markup.
  // The mechanism: an icon is a Private Use Area codepoint in ::before, and it only draws if
  // the font stack the browser resolved for that pseudo-element actually reaches the icon
  // webfont. Measured on ZK's four carriers of the SAME class, all four ask for U+F0F3 and
  // only one misses the font:
  //   <span>, <div>, button iconSclass  ->  ::before font-family "ZK85Icons, FontAwesome"
  //   <label>                           ->  ::before font-family "Helvetica Neue", ...
  // The empty box that follows was misdiagnosed three separate ways in the zul-writer
  // evaluation -- built-in font lacks the glyph, webfont 404, and once not noticed at all --
  // and one of those pages shipped with every icon on it blank. None of the three readings is
  // available to a screenshot, which is why this has to be a measurement and not advice.
  //
  // Deliberately framework-agnostic: nothing here knows the name ZK85Icons, or that <label> is
  // the carrier that fails. It asks whether the resolved stack reaches ANY @font-face family,
  // so it holds for Font Awesome, Material Icons or a house icon font equally.
  const webfonts = new Set();
  try {
    // Declared, NOT `status === 'loaded'`. A face is 'unloaded' until something on the page
    // uses it, so a page whose every icon is broken -- exactly the page that shipped -- would
    // present an empty set and silence the rule on the one case it exists for. A declared face
    // whose file 404s is a different defect, and the WARNINGS block reports that one by URL.
    document.fonts.forEach((ff) => {
      const fam = String(ff.family || '').trim().replace(/^['"]|['"]$/g, '').toLowerCase();
      if (fam) webfonts.add(fam);
    });
  } catch (e) { /* no FontFaceSet: leave the set empty and skip below, never guess */ }
  // No webfonts at all means no icon font could be reaching anything, so every PUA glyph
  // would report. Under-reporting is the only safe direction for a rule the agent is told
  // to trust as the browser's own measurement.
  if (webfonts.size) {
    // A single Private Use Area codepoint. Three ranges, because Material Symbols and some
    // house fonts sit in the supplementary planes rather than in U+E000-F8FF.
    const puaGlyph = (raw) => {
      if (!raw) return null;
      const s = String(raw).trim();
      if (s === 'none' || s === 'normal' || s === '""' || s === "''") return null;
      // Only a quoted string is a glyph: counter(), attr() and url() forms are not.
      const m = s.match(/^(?:"([^"]*)"|'([^']*)')$/);
      if (!m) return null;
      const text = m[1] !== undefined ? m[1] : m[2];
      const chars = Array.from(text);
      if (chars.length !== 1) return null;      // an icon is exactly one glyph
      const cp = chars[0].codePointAt(0);
      const pua = (cp >= 0xE000 && cp <= 0xF8FF) ||
                  (cp >= 0xF0000 && cp <= 0xFFFFD) ||
                  (cp >= 0x100000 && cp <= 0x10FFFD);
      return pua ? cp : null;
    };
    const reachesWebfont = (fontFamily) => {
      const list = String(fontFamily || '').split(',');
      for (let i = 0; i < list.length; i++) {
        const fam = list[i].trim().replace(/^['"]|['"]$/g, '').toLowerCase();
        if (webfonts.has(fam)) return true;
      }
      return false;
    };
    for (let i = 0; i < all.length; i++) {
      const el = all[i];
      if (claimed.has(el) || hiddenSomewhere(el)) continue;
      for (const pseudo of ['::before', '::after']) {
        let cs = null;
        try { cs = getComputedStyle(el, pseudo); } catch (e) { cs = null; }
        if (!cs) continue;
        const cp = puaGlyph(cs.content);
        if (cp === null) continue;
        if (reachesWebfont(cs.fontFamily)) continue;
        const hex = 'U+' + cp.toString(16).toUpperCase();
        record('icon-not-rendered', el,
               pseudo + ' glyph ' + hex + ' needs an icon font, but the resolved stack is ' +
                 snip(String(cs.fontFamily || '(none)'), 60),
               {pseudo: pseudo, codepoint: hex, fontFamily: cs.fontFamily || null});
        break;      // one finding per element: both pseudos share the one broken stack
      }
    }
  }

  // --- rule 4: viewport-overflow -----------------------------------------
  // One finding for the whole document, naming the widest element whose right edge
  // passes the viewport — that is the element to fix, and it is what turns "there is a
  // horizontal scrollbar" into an address.
  const de = document.documentElement;
  if (de.scrollWidth > window.innerWidth + 1) {
    let widest = null, widestW = 0;
    for (let i = 0; i < all.length; i++) {
      const el = all[i];
      if (hiddenSomewhere(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.right <= window.innerWidth + 1) continue;
      if (r.width > widestW) { widestW = r.width; widest = el; }
    }
    if (widest) {
      record('viewport-overflow', widest,
             'page scrollWidth ' + de.scrollWidth + ' > viewport ' + window.innerWidth +
               '; widest offender ' + px(widestW) + 'px',
             {scrollWidth: de.scrollWidth, viewportWidth: window.innerWidth, widest: widestW});
    }
  }

  return {total: total, findings: findings,
          viewport: {w: window.innerWidth, h: window.innerHeight}};
}"""


# --- Literal rows a model discarded --------------------------------------
# The one LAYOUT rule that cannot be answered from the DOM alone, because the defect is
# something the page does NOT contain. Setting a model on a mesh component discards the
# rows spelled out in the markup -- measured on ZK 10.3: a listbox and a grid, under a
# bound model and under a Composer's setModel(), with a full model and with an empty one.
# Four configurations, four times the literal rows were gone, STATUS: ok and not one
# warning. So the page renders correctly while its source keeps rows that claim to show
# data they never show, and whoever edits those rows next will change nothing and not
# know why. Step 5 is a look at the render, and a render is structurally incapable of
# showing this.
#
# Two detectors, because the two halves leave different evidence:
#
#   A  the ZUL carries both `model=` and literal rows. Self-contained, exact, and it
#      fires under isolation too -- the defect is in the source either way.
#   B  the ZUL has literal rows, no `model=`, and not one of those strings reached the
#      page. That is a Composer's setModel(), which lives in a .java file this script
#      never opens. Needs the render, and needs the guards below.
#
# The guards come from measuring what else can legitimately keep a literal row off the
# page (see tasks/zul-writer-data-flow-review.md for the run):
#
#   mold="paging"          only the first pageSize rows render     -> caught by ANY_PRESENT
#   a collapsed tree node  its children do not render               -> caught by ANY_PRESENT
#   an unselected tabpanel its whole subtree is absent from the DOM -> caught by IN_DOM
#   a long scrolling list  renders in full; ZK has no render-on-demand without a model
#
# Detector B additionally requires an `id`, which is not a hedge: setModel() reaches the
# component through @Wire, and @Wire matches the ZUL id. Without one there is nothing to
# look up and nothing to say, so the rule stays quiet rather than guessing.

MESH_ITEMS = {"listbox": {"listitem"}, "grid": {"row"}, "tree": {"treeitem"}}
LITERAL_TEXT_CAP = 20       # per component, in document order -- see below
# Document order matters more than the number: paging shows the FIRST pageSize rows, so
# taking the first N is exactly the slice that proves the literals survived.

_BINDING = re.compile(r"^\s*@\w+\s*\(")     # @load(...), @bind(...), @init(...)
_EL_EXPR = re.compile(r"\$\{")


def _tag(el) -> str:
    """ZUL's default namespace makes every tag `{http://...}listbox` once parsed."""
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) and "}" in el.tag else str(el.tag)


def _literal_strings(item, out):
    """Every fixed string this row would display, skipping any nested mesh component
    (its rows are its own component's business) and any binding or EL expression."""
    for attr in ("label", "value"):
        text = item.get(attr)
        if text and not _BINDING.match(text) and not _EL_EXPR.search(text):
            if text.strip():
                out.append(text.strip())
    if item.text and item.text.strip():
        out.append(item.text.strip())
    for child in item:
        if _tag(child) in MESH_ITEMS:
            continue
        _literal_strings(child, out)


def _literal_rows(component, item_tags):
    """The component's own literal rows, in document order. `<template>` is skipped: the
    rows inside it are the model's renderer, not data."""
    found = []

    def walk(node):
        for child in node:
            tag = _tag(child)
            if tag == "template" or tag in MESH_ITEMS:
                continue
            if tag in item_tags:
                found.append(child)      # not descended into: _literal_strings covers the
                continue                 # nested treeitems of a tree under their ancestor
            walk(child)

    walk(component)
    return found


def literal_row_groups(zul: Path):
    """One entry per mesh component that spells its rows out in the markup.

    Parsing is best-effort by design: a .zul this cannot parse is one validate-zul.py
    would have failed at Layer 1, and a render must never be lost to a rule that only
    adds a finding."""
    try:
        root = ElementTree.parse(str(zul)).getroot()
    except Exception as failure:
        debug("literal rows", f"not parsed: {failure}")
        return []
    groups = []
    for component in root.iter():
        item_tags = MESH_ITEMS.get(_tag(component))
        if not item_tags:
            continue
        strings = []
        for row in _literal_rows(component, item_tags):
            _literal_strings(row, strings)
            if len(strings) >= LITERAL_TEXT_CAP:
                break
        if not strings:
            continue
        groups.append({
            "tag": _tag(component),
            "id": component.get("id") or "",
            "sclass": component.get("sclass") or "",
            "rows": len(_literal_rows(component, item_tags)),
            "item": sorted(item_tags)[0],
            "model": component.get("model") or "",
            "texts": strings[:LITERAL_TEXT_CAP],
        })
    debug_lines("literal rows", [f"{g['tag']}#{g['id'] or '-'}: {g['rows']} row(s), "
                                 f"model={g['model'] or '-'}" for g in groups])
    return groups


# Answers exactly two questions per group, both about presence rather than geometry:
# is the component in the document at all, and did any of its literal strings reach it.
# textContent, not innerText, on purpose -- a component hidden by `visible="false"` still
# holds its text, and "hidden" is not "discarded".
LITERAL_ROWS_JS = """(groups) => {
  const zk = window.zk;
  const text = document.body ? (document.body.textContent || '') : '';
  const byId = {};
  const els = document.querySelectorAll('body *');
  for (let i = 0; i < els.length; i++) {
    const el = els[i];
    let w = null;
    try { w = (zk && zk.Widget && zk.Widget.$) ? zk.Widget.$(el) : null; } catch (e) { w = null; }
    if (!w || !w.id) continue;
    try { if (w.$n() !== el) continue; } catch (e) { continue; }
    if (!(w.id in byId)) byId[w.id] = true;
  }
  return groups.map((g) => ({
    anyPresent: g.texts.some((t) => text.indexOf(t) !== -1),
    inDom: g.id ? (g.id in byId) : false,
  }));
}"""


def literal_row_findings(groups, verdicts):
    """The two detectors, applied to what the page reported back."""
    findings = []
    for group, verdict in zip(groups, verdicts):
        locator = group["tag"]
        if group["id"]:
            locator += "#" + group["id"]
        elif group["sclass"]:
            locator += "." + group["sclass"].split()[0]
        rows = f"{group['rows']} literal <{group['item']}>" + ("" if group["rows"] == 1 else "s")
        if group["model"]:
            findings.append({
                "rule": "literal-rows-discarded", "locator": locator,
                "detail": f'{rows} under model="{group["model"]}" — the model replaces them, '
                          f"so they never render. Delete them.",
                "measured": {"rows": group["rows"], "detector": "model-attribute"},
            })
        elif verdict.get("inDom") and not verdict.get("anyPresent"):
            findings.append({
                "rule": "literal-rows-discarded", "locator": locator,
                "detail": f"{rows} are written here but none of them reached the page — a "
                          f"controller set a model, which discards them. Delete them.",
                "measured": {"rows": group["rows"], "detector": "absent-from-dom"},
            })
    return findings


# --- ZK client error box -------------------------------------------------
# ZK's client engine does NOT log to the console: zk.error() hands the message to
# zk.debugLog (which reaches the console only under zk.debugJS) and then to
# zk.errorPush -> zk._Erbx, which appends a box to document.body
# (zk-10.3.0.1-Eval.jar web/js/zk/index.src.js:35803-35816, :36487-36500). So every
# ZK client complaint — "Unknown widget: ...", "Failed to mount: ...", a missing mold —
# is reachable from the DOM and from nowhere else. This is a read of ZK-internal markup
# with no API contract behind it; treat it as best-effort.
ZK_ERROR_BOX_JS = """() => {
  const out = [];
  document.querySelectorAll('div.z-error > .messagecontent > .messages').forEach((box) => {
    // _Erbx builds the FIRST message as the direct text of .messages and appends each
    // further one as an element child - div.message, or div.newmessage while the
    // slideDown is still in flight (index.src.js:36532-36537). Hence the two reads:
    // box.textContent alone would glue every message into one string.
    const first = Array.prototype.filter.call(box.childNodes, (n) => n.nodeType === 3)
                       .map((n) => n.textContent).join('').trim();
    if (first) out.push(first);
    Array.prototype.forEach.call(box.children, (child) => {
      const text = (child.textContent || '').trim();
      if (text) out.push(text);
    });
  });
  return out;
}"""


def _one_line(text, limit=200):
    """One line, bounded width — the shape every console / client-error entry prints in.
    `str(e).splitlines()[0]` (the pageerror handler in capture()) is the established idiom
    here, but a console message is frequently one enormous serialized object on a single
    line, so the width bound has to come with it."""
    lines = (text or "").splitlines()
    first = lines[0].strip() if lines else ""
    return first if len(first) <= limit else first[:limit] + "\u2026"


def capture(url, out_path: Path, args, warnings, controllers, layout, probes, dom,
            literal_groups=()):
    """Returns (http_status, error_details_or_None).

    `controllers` is mutated in place (same idiom as `warnings`) with what the launcher
    reported for this render, because it is a property of the response rather than of the
    process: one launcher can serve several pages. `layout` is mutated the same way with
    the DOM audit's result, `probes` with one entry per --probe selector, and `dom` with
    the path --dump-dom was written to (absent when it was not passed, or could not be)."""
    from playwright.sync_api import sync_playwright, Error as PWError, TimeoutError as PWTimeout

    with sync_playwright() as pw:
        browser = None
        tried = []
        for channel in ([args.browser_channel] if args.browser_channel else ["chrome", "msedge"]):
            try:
                browser = pw.chromium.launch(channel=channel, headless=True)
                debug("browser", f"channel {channel}")
                break
            except PWError as e:
                tried.append(f"{channel}: {str(e).splitlines()[0]}")
                debug("browser unavailable", tried[-1])
        if browser is None:
            try:
                browser = pw.chromium.launch(headless=True)   # a Playwright-managed one, if present
                debug("browser", "playwright-managed chromium")
            except PWError:
                raise Skipped(
                    "no headless browser available — ZK renders through client-side JavaScript, "
                    "so a real browser is required.\n  Tried: " + "; ".join(tried),
                    "install Google Chrome or Microsoft Edge, or run:\n"
                    "    uv run --with playwright python -m playwright install chromium",
                )

        try:
            page = browser.new_page(viewport={"width": args.width, "height": args.height})
            # Before page.goto, because add_init_script only reaches documents opened after it
            # is registered. Suppressed on its own: a browser that rejects the script must not
            # cost the caller the render, it just costs them the animation guarantee.
            with contextlib.suppress(Exception):
                page.add_init_script(ANIMATION_OFF_JS)
            page.on("pageerror", lambda e: warnings.append(f"page error: {str(e).splitlines()[0]}"))

            # The console carries what the page's own JavaScript logged — ZK's client engine
            # is not on it (see ZK_ERROR_BOX_JS), which is why there are two collectors.
            # An insertion-ordered dict keyed (level, one-lined text) is both the dedupe and
            # the print order.
            console_seen = {}
            client_errors = []

            def _on_console(msg):
                # Suppressed whole: a malformed console message must never fail a good render.
                with contextlib.suppress(Exception):
                    text = _one_line(msg.text)
                    location = msg.location or {}
                    origin = location.get("url") or ""
                    # The --debug dump is unconditional and covers EVERY level, including the
                    # ones filtered out below — stderr only, so stdout's contract is untouched.
                    debug("console", f"[{msg.type}] {text}"
                          + (f"  ({origin}:{location.get('lineNumber')})" if origin else ""))
                    if msg.type not in ("error", "warning"):
                        return
                    # Chromium reports its own network failures on the console, and they are
                    # not the page complaining: measured, EVERY page emits exactly one of
                    # these — a 404 for /favicon.ico — whose text carries no URL at all, so
                    # keeping them would put a false finding on every clean page. The ones
                    # that matter, ZK's own /zkau/web/ assets, are already reported by the
                    # page.on("response") handler below, with the real URL and advice.
                    if text.startswith("Failed to load resource:"):
                        return
                    console_seen[(msg.type, text)] = None

            page.on("console", _on_console)
            missing = []
            # EVERY 4xx/5xx, not only ZK's own /zkau/web/ assets. The narrower filter that used
            # to be here left the tool silent on the case it is most often asked about: an
            # <image src="/img/logo.png"> that does not resolve produced no WARNINGS entry and
            # no console line either -- Chromium reports those as "Failed to load resource:",
            # which the console handler above drops because every page emits one for its
            # favicon. Measured on a three-case fixture: the ~./ asset reported, while a
            # docroot-relative <image> and a native <n:img> both vanished from the output
            # entirely. A blank box in the image with nothing in the text is the worst
            # combination available, because the reader has to guess which of the two it is.
            # The page's own document is excluded: a render error serves the launcher's error
            # page with a 4xx, and reporting that as a missing asset told the reader to go
            # hunting for a path when STATUS/PHASE/MESSAGE and the exit code had already named
            # the real problem. Only subresources belong in this list.
            page.on("response", lambda r: missing.append(r.url) if r.status >= 400
                    and not r.url.endswith("/favicon.ico")
                    and r.url.split("?")[0] != url.split("?")[0] else None)

            timeout_ms = args.timeout * 1000
            debug("GET", url)
            response = page.goto(url, wait_until="load", timeout=timeout_ms)
            status = response.status if response else 0
            debug("http status", status)

            # The launcher states the controller mode per response (see its README). Absent
            # on a pre-P0-2 jar, which is exactly the case controllers_line has to warn about.
            if response is not None:
                controllers["mode"] = response.header_value("x-zk-preview-controllers")
                failure = response.header_value("x-zk-preview-controller-failure")
                debug("controllers", f"{controllers['mode']} ({failure or 'no failure'})")
                if failure:
                    controllers["failure"] = failure
                    warnings.append(f"controller failure: {failure}")

            # Whether this page has a ZK client engine at all is answered from the HTML the
            # server sent, and deliberately not by asking the live page. The question used to be
            # "is window.zk defined within 5s?", and wait_for_function evaluates its predicate on
            # the page's own main thread -- which on a page heavy enough to be worth previewing is
            # saturated at exactly the moment it gets asked. Measured on a page holding one div
            # and one chart: zk.wpd finished downloading at 499ms, window.zk existed at 2.5s, ZK
            # finished mounting 34ms after that, and the main thread was then blocked for 4.6s
            # straight by mounting plus chart construction. The 5s check expired inside that
            # block and reported "no ZK content" about a page that had been fully mounted for
            # seconds -- and then skipped the mount wait below and captured whatever was up.
            #
            # Reading the response body needs no main thread, so a busy page cannot make it lie.
            served = ""
            if response is not None:
                with contextlib.suppress(Exception):
                    served = response.text()
            if ZKAU_PATH in served:
                try:
                    # The caller's whole budget, because "how long does this page take to mount"
                    # has no answer shorter than "as long as it takes". ZK_READY is false while
                    # window.zk is undefined, so the not-loaded-yet case needs no separate gate.
                    page.wait_for_function(ZK_READY, timeout=timeout_ms)
                    debug("zk client engine", "mounted")
                except PWTimeout:
                    warnings.append(f"ZK's client engine did not finish mounting within "
                                    f"{args.timeout}s — captured the page as-is")
            else:
                # The launcher's error page lands here, and so does any plain HTML: measured 200
                # with /zkau/ for both ZK fixtures, 500 without it for the error page. Capture it
                # as-is rather than failing, and say what was actually observed rather than
                # guessing at which of the two it was.
                debug("zk client engine",
                      "none on this page (the served HTML loads nothing from /zkau/)")
            with contextlib.suppress(PWTimeout):
                page.wait_for_load_state("networkidle", timeout=5000)
            with contextlib.suppress(Exception):
                page.evaluate("() => (document.fonts ? document.fonts.ready : null)")

            details = _scrape_error(page) if status >= 500 else None

            # Last of the waits and deliberately so: it is the only one that asks about the
            # pixels rather than about a subsystem. Skipped on the launcher's error page, which
            # is static markup of our own and has nothing to settle.
            if details is None:
                with contextlib.suppress(Exception):
                    _settle(page, warnings)

            out_path.parent.mkdir(parents=True, exist_ok=True)
            # animations/caret disabled so repeated captures are comparable if the
            # caller diffs a before/after pair.
            page.screenshot(path=str(out_path), full_page=args.full_page,
                            animations="disabled", caret="hide")
            debug("screenshot", f"{out_path} ({out_path.stat().st_size} bytes)")

            # After the screenshot for the same reason as the audit below: the PNG is
            # already on disk, so nothing read here can alter the image it explains. Written
            # even on the error page -- that markup is what a reader chasing an error page
            # would want -- and the DOM: line labels it there, exactly as SCREENSHOT: does.
            dom_target = dom_dump_path(args, out_path)
            if dom_target is not None:
                # A dump that cannot be written must not cost the caller a render that
                # worked, so no DOM: line means no dump and the reason goes to stderr,
                # where every diagnostic goes.
                try:
                    dom_target.parent.mkdir(parents=True, exist_ok=True)
                    dom_target.write_text(page.content(), encoding="utf-8")
                    dom["path"] = str(dom_target)
                    debug("dom dump", f"{dom_target} ({dom_target.stat().st_size} bytes)")
                except Exception as failure:
                    print(f"warning: could not write the DOM dump to {dom_target}: {failure}",
                          file=sys.stderr)

            # Deliberately AFTER the screenshot: the PNG is already on disk before
            # anything evaluates in the page, so the audit cannot alter the image it
            # describes. Skipped on the launcher's error page — that is not the user's
            # UI, and measuring it would report defects in our own diagnostic markup.
            # Suppressed wholesale: a bug in the audit must never fail a good render.
            if details is None:
                with contextlib.suppress(Exception):
                    started = time.monotonic()
                    audited = page.evaluate(LAYOUT_AUDIT_JS, LAYOUT_COLLECT_CAP)
                    layout["total"] = audited["total"]
                    layout["findings"] = audited["findings"]
                    debug("layout", f"{audited['total']} findings in "
                                    f"{(time.monotonic() - started) * 1000:.0f} ms")
                    # page.screenshot(full_page=True) stitches; it does not resize the
                    # browsing context. So this always equals --width x --height, which
                    # is what the SIZE: line reports and what the findings are read against.
                    debug("layout viewport",
                          f"{audited['viewport']['w']}x{audited['viewport']['h']}")

                # Same block, same suppression, but a separate evaluate: this one is the
                # only rule that needs a question from the .zul, so it has nothing to ask
                # when the file declared no literal rows -- the common case, and it costs
                # nothing there. Appended to the audit's findings rather than given a block
                # of its own, because a reader told to "read the LAYOUT block first" should
                # not have to learn a second place to look.
                if literal_groups:
                    with contextlib.suppress(Exception):
                        verdicts = page.evaluate(LITERAL_ROWS_JS, literal_groups)
                        extra = literal_row_findings(literal_groups, verdicts)
                        layout.setdefault("findings", []).extend(extra)
                        layout["total"] = layout.get("total", 0) + len(extra)
                        debug("literal rows", f"{len(extra)} finding(s) from "
                                              f"{len(literal_groups)} component(s)")

                # After the screenshot for the same reason as the audit above — the PNG is
                # already on disk, so nothing evaluated here can alter the image it explains.
                # Skipped on the launcher's error page: that box would be our own diagnostic
                # UI, not the user's. Suppressed wholesale, because a bug in the read must
                # never fail a good render.
                with contextlib.suppress(Exception):
                    client_errors.extend(_one_line(m) for m in page.evaluate(ZK_ERROR_BOX_JS))
                    debug("client error box", f"{len(client_errors)} message(s)")

                # Last of the three DOM reads, and gated on `details` with the other two: the
                # launcher's error page is not the user's UI, so measuring it would answer a
                # question about our own diagnostic markup. Each selector is suppressed on its
                # own -- one bad selector must not cost the caller the others, nor the render.
                for selector in args.probe:
                    found = {"selector": selector, "total": 0, "elements": []}
                    with contextlib.suppress(Exception):
                        found.update(page.evaluate(
                            PROBE_JS, [selector, PROBE_MATCH_CAP, PROBE_HTML_CAP]))
                    probes.append(found)
                    debug("probe", f"{selector}: {found.get('error') or found['total']}")

            # Two causes, two remedies, so two shapes. A /zkau/web/ miss is a classpath
            # problem: the jar that would have defined the resource is absent, and the answer
            # is a dependency, not an edit. A docroot miss is a real missing file.
            #
            # Launcher 1.0.3 is what makes the second sentence true. Before it, the render
            # server served .zul pages and /zkau/web/ resources and nothing else -- a png, a
            # css and a js sitting inside the correctly resolved docroot all returned 404 --
            # so every docroot asset was blank by construction and these had to be grouped
            # into one line that told the reader to discount them. They are now genuine
            # findings, reported one per URL because each one names a different file to go
            # and look at. Keep this paired with the pinned LAUNCHER_VERSION: on an older
            # jar passed through --launcher-jar these lines would overstate the case, which
            # is what the digest-mismatch warning above exists to flag.
            zk_misses = [u for u in dict.fromkeys(missing) if "/zkau/web/" in u]
            page_misses = [u for u in dict.fromkeys(missing) if "/zkau/web/" not in u]
            for url_404 in zk_misses:
                warnings.append(f"ZK resource not served: {url_404} — an add-on jar may be "
                                "missing from the classpath, so the image may be misleading")
            for url_404 in page_misses[:ASSET_WARNING_CAP]:
                warnings.append(f"page asset not found: {url_404} — the docroot has no file at "
                                "that path, so it is blank in the image. Check the path first, "
                                "then the DOCROOT: line, since a guessed docroot makes a correct "
                                "path look wrong")
            if len(page_misses) > ASSET_WARNING_CAP:
                warnings.append(f"…and {len(page_misses) - ASSET_WARNING_CAP} more missing page "
                                "assets not listed")

            # P1-4 feeds the EXISTING WARNINGS block: the block order is a contract, so no
            # new block and no new exit code. Ungated on `details`, because on the launcher's
            # error page both collectors are empty by construction — no ZK client engine
            # boots there and the page runs no script of the user's.
            def _append_capped(entry_fn, items, tail_noun):
                for item in items[:CONSOLE_WARNING_CAP]:
                    warnings.append(entry_fn(item))
                # Never a silent truncation (same rule as the LAYOUT: block): whatever the
                # cap dropped is counted on a line of its own.
                dropped = len(items) - CONSOLE_WARNING_CAP
                if dropped > 0:
                    warnings.append(f"... and {dropped} more {tail_noun}")

            # ZK client errors first: a complaint from the client engine outranks a page log
            # line, because it names something that did not render at all.
            _append_capped(lambda msg: f"ZK client error: {msg}",
                           list(dict.fromkeys(client_errors)),
                           "in ZK's on-page error box")
            _append_capped(lambda entry: f"console {entry[0]}: {entry[1]}",
                           list(console_seen),
                           "console message(s) (re-run with --debug to see every level)")
            return status, details
        finally:
            browser.close()


def _scrape_error(page):
    """Pull the structured failure out of the launcher's error page. Its CSS class
    names are not locked by a test, so fall back to the visible body text — free
    robustness, since a real browser is already driving the page."""
    def text(selector):
        with contextlib.suppress(Exception):
            locator = page.locator(selector)
            if locator.count():
                return locator.first.inner_text().strip()
        return ""

    details = {"phase": text(".phase") or "UNKNOWN", "message": text("pre.msg"),
               "location": text(".loc"), "trace": text("details.trace pre")}
    if not details["message"]:
        with contextlib.suppress(Exception):
            details["message"] = page.inner_text("body")[:1500].strip()
    return details


# --- Output --------------------------------------------------------------

def emit(key, value):
    print(f"{key}: {value}")


def emit_warnings(warnings):
    if warnings:
        emit("WARNINGS", len(warnings))
        for warning in warnings:
            print(f"  - {warning}")


def _visible(text):
    """An icon's ::before content is a private-use codepoint: printed raw it is an empty box
    in the terminal, or nothing at all, so the one line that proves the glyph WAS requested
    would read as proof that it was not. Escaped, it reads \uf0f3 and says what it is."""
    return "".join(c if 32 <= ord(c) <= 126 else f"\\u{ord(c):04x}" for c in text)


def emit_probe(probes):
    """Omitted entirely when --probe was not passed, so a run without it prints exactly what
    it printed before this block existed. A selector that matched nothing still gets its line:
    "0 matches" is an answer -- the component is not in the DOM at all -- and silence is not."""
    if not probes:
        return
    emit("PROBE", f"{len(probes)} selector{'' if len(probes) == 1 else 's'}, "
                  f"{sum(p.get('total', 0) for p in probes)} matches")
    for probe in probes:
        if probe.get("error"):
            print(f"  {probe['selector']}  —  not a usable selector: {probe['error']}")
            continue
        total = probe.get("total", 0)
        shown = probe.get("elements") or []
        print(f"  {probe['selector']}  —  {total} match{'' if total == 1 else 'es'}")
        for element in shown:
            rect, styles = element["rect"], element["styles"]
            print(f"    - {element['html']}")
            print(f"      box {rect['w']}x{rect['h']} @ ({rect['x']},{rect['y']})"
                  f" | display {styles['display']} | position {styles['position']}"
                  f" | overflow {styles['overflow']}")
            print(f"      font-family {styles['fontFamily']} | color {styles['color']}"
                  f" | background-color {styles['backgroundColor']}")
            print(f"      width {styles['width']} | height {styles['height']}"
                  f" | flex {styles['flex']}")
            if element.get("before"):
                print(f"      ::before content {_visible(element['before']['content'])}"
                      f" | ::before font-family {element['before']['fontFamily']}")
        # Never a silent truncation, for the same reason the LAYOUT block says so.
        if total > len(shown):
            print(f"    ... and {total - len(shown)} more")


def emit_layout(layout):
    """Omitted entirely when there is nothing to report, so a clean page prints exactly
    what it printed before this block existed."""
    findings = layout.get("findings") or []
    if not findings:
        return
    total = layout.get("total", len(findings))
    emit("LAYOUT", f"{total} findings")
    shown = findings[:LAYOUT_PRINT_CAP]
    rule_width = max(len(f["rule"]) for f in shown)
    for finding in shown:
        print(f"  - {finding['rule'].ljust(rule_width)} | {finding['locator']} | "
              f"{finding['detail']}")
    # Never a silent truncation: the header counts every finding, so the difference
    # has to be accounted for on its own line.
    if total > len(shown):
        print(f"  ... and {total - len(shown)} more")


# --- The JSON report -----------------------------------------------------
# Everything below serializes state the pipeline already holds; it measures nothing of its
# own, so the text block and the JSON cannot disagree about a run.

REPORT_TARGET = None   # set once in main(); exits 2 and 3 happen outside it (see report_for_skip)
REPORT_ZUL = None      # the RAW zul argument, for the same two paths: nothing is resolved there


def report_target(args, zul_like: Path):
    """None when --report was not passed. `json` alone lands the file beside the PNG, which
    is the only place a caller can predict without being told. Takes the caller's own argument
    rather than the pipeline-resolved .zul: on the exit-2 and exit-3 paths nothing has been
    resolved yet, and only the stem is used, so a path that does not exist still yields a
    usable destination."""
    if not args.report:
        return None
    _, _, explicit = args.report.partition(":")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return screenshot_path(args, zul_like).with_suffix(".json")


def report_skeleton():
    """Every key on every path, in the order of the text block it mirrors. A consumer must be
    able to read report["controllers"] without first branching on the exit code — that
    branching is exactly what this flag exists to remove. A key is non-null only when the work
    it describes actually happened; `zul` is the exception, because it is the request rather
    than the work, and `warnings` is always an array."""
    return {"status": None, "exitCode": None, "zul": None, "screenshot": None, "size": None,
            "docroot": None, "classpath": None, "zk": None, "launcher": None,
            "controllers": None, "layout": None, "probe": None, "domDump": None,
            "warnings": [], "error": None}


def write_report(obj):
    """The one new stdout line, and it is always the last one printed. Suppressed wholesale,
    like the layout audit and the error-box read: a report that cannot be written must not
    change the exit code (0/1/2/3/4 are frozen) nor fail a render that succeeded. No REPORT:
    line therefore means no report — the diagnostic goes to stderr, where every diagnostic goes."""
    if REPORT_TARGET is None:
        return
    try:
        write_json_atomic(REPORT_TARGET, obj)     # mkdir + tmp file + os.replace, already here
    except Exception as failure:
        print(f"warning: could not write the JSON report to {REPORT_TARGET}: {failure}",
              file=sys.stderr)
        return
    emit("REPORT", REPORT_TARGET)


def report_for_run(exit_code, args, target: "Target", launcher, warnings, controllers,
                   layout, details, probes, dom):
    """Exits 0, 1 and 4 — every one of them a render that reached the browser. Built from the
    same objects report_success/report_render_error print from, so text and JSON cannot drift.
    Called from main() and not from those two, because exit 4 is only known after the LAYOUT
    findings are counted, i.e. at report_success's last line."""
    resolved = target.resolved
    kind = resolved["kind"]
    # `cached` is not a dict key: _load_cached_classpath appends " (cached)" to `kind` and the
    # CLASSPATH: line prints it verbatim. Derived here rather than threaded through the six
    # {"kind": ...} literals, which is the smaller change and keeps one source of truth.
    suffix = " (cached)"
    cached = kind.endswith(suffix)
    report = report_skeleton()
    report.update(
        status="render-error" if details else "ok",
        exitCode=exit_code,
        zul=str(target.zul),
        # The bare path. The text line's "   [ERROR PAGE - this is not your UI]" suffix is a
        # warning to a human reader, not part of the filename.
        screenshot=str(target.out_path),
        size={"width": args.width, "height": args.height, "fullPage": bool(args.full_page)},
        docroot={"path": str(target.docroot), "rule": target.layout},
        classpath={"source": kind[:-len(suffix)] if cached else kind, "cached": cached,
                   "jars": len(resolved["jars"]),
                   "outputRoots": len(resolved["output_roots"]),
                   "resourceRoots": len(resolved["resource_roots"])},
        zk=", ".join(j.name for j in resolved["jars"] if re.match(r"zk-\d", j.name)) or None,
        launcher={"version": launcher.version, "source": launcher.source},
        # The RAW launcher token, not the CONTROLLER_LINES presentation string. "skipped" when
        # the launcher reported no mode at all, because that is the claim the CONTROLLERS: line
        # then makes, and the warning controllers_line raised is already in `warnings`.
        # `failures` is the spec's plural key over a singular header, so 0 or 1 element: the
        # launcher reports one x-zk-preview-controller-failure and no more.
        controllers={"mode": controllers.get("mode") or "skipped",
                     "failures": [controllers["failure"]] if controllers.get("failure") else []},
        # The COLLECT cap (200), not the print cap (25): a JSON consumer that got the printed
        # 25 with no way to tell would be reading a silent truncation, which nothing here does.
        layout={"total": layout.get("total", 0), "findings": layout.get("findings") or []},
        # Null when the flag was not passed, which is not the same claim as "asked and found
        # nothing" -- an empty array. The text block draws the same distinction by omitting
        # the PROBE: block entirely in the first case and printing "0 matches" in the second.
        probe=list(probes) if args.probe else None,
        domDump=dom.get("path"),
        warnings=list(warnings),
    )
    if details:
        report["error"] = {"phase": details["phase"] or None,
                           "message": details["message"] or None,
                           "location": details["location"] or None,
                           "trace": details["trace"] or None}
    return report


def report_for_skip(exit_code, status, raw_zul, reason, next_step=None):
    """Exits 2 and 3, which are raised where none of the above exists: `Skipped` is caught in
    the __main__ block and locate_zul exits 3 before step 1 has run. A skipped run resolved
    nothing it can promise, so every key stays null rather than being sometimes-present -- a
    consumer that has to test for a key is back to scraping. The reason text is the payload,
    and it is the same string the PREVIEW_SKIPPED:/NEXT: lines carry, internal-error wording
    included, so grepping `error.reason` tells a crash from a clean skip exactly as grepping
    stdout does today."""
    report = report_skeleton()
    report.update(status=status, exitCode=exit_code, zul=str(raw_zul),
                  error={"reason": reason, "next": next_step})
    return report


def _report_spec(value):
    """`json` or `json:<path>`. Routed through argparse's own `type=` so a malformed value
    exits 3 with the usage block, exactly like any other bad flag (see _Parser.error) --
    which also means no report can exist for it: argparse fails before --report is a value."""
    fmt, sep, path = value.partition(":")
    if fmt != "json" or (sep and not path):
        raise argparse.ArgumentTypeError(f"expected json or json:<path>, not {value!r}")
    return value


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse exits 2 by default, which is this script's "skipped" code.
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)


def parse_args(argv):
    parser = _Parser(description="Render a ZK .zul file to a PNG screenshot.")
    parser.add_argument("zul", help="the .zul file to render")
    parser.add_argument("-o", "--out", help="output PNG (default: ./<name>-preview.png)")
    parser.add_argument("--width", type=int, default=1280, help="viewport width (default: 1280)")
    parser.add_argument("--height", type=int, default=900, help="viewport height (default: 900)")
    parser.add_argument("--full-page", action="store_true", help="capture the whole scrollable page")
    parser.add_argument("--classpath", help="os-path-separated ZK jars; skips all build-tool resolution")
    parser.add_argument("--webapp", help="docroot to serve the .zul relative to; skips docroot detection")
    parser.add_argument("--project", help="project root: where to look for pom.xml/build.gradle")
    parser.add_argument("--zk-version", default=DEFAULT_ZK_VERSION,
                        help=f"stock ZK version for the no-project fallback (default: {DEFAULT_ZK_VERSION}; "
                             "a -jakarta suffix selects the jakarta servlet variant)")
    parser.add_argument("--java", help="java executable to run the renderer (default: auto-detected JDK 17+)")
    parser.add_argument("--launcher-jar", help="local zk-preview-launcher.jar instead of the pinned download")
    parser.add_argument("--launcher-version", default=LAUNCHER_VERSION,
                        help=f"launcher release to download (default: {LAUNCHER_VERSION}, the one "
                             "this skill pins); any other version is verified against the checksum "
                             "published beside that release, not the digest pinned here")
    parser.add_argument("--browser-channel", help="chrome | msedge | chromium (default: chrome, then msedge)")
    parser.add_argument("--timeout", type=int, default=120, help="browser phase budget in seconds (default: 120)")
    parser.add_argument("--refresh", action="store_true", help="ignore the cached classpath and re-resolve")
    parser.add_argument("--run-controllers", dest="run_controllers", action="store_true", default=False,
                        help="run the project's real Composers/ViewModels, so bound values and "
                             "model rows are the real thing. EXECUTES ARBITRARY PROJECT CODE from "
                             "the resolved classpath; off by default. A controller that fails or "
                             "hangs degrades the render to the isolated one instead of failing it.")
    parser.add_argument("--no-run-controllers", dest="run_controllers", action="store_false",
                        help="force the default isolated render (no Composer, no ViewModel)")
    parser.add_argument("--controller-timeout", type=int, default=CONTROLLER_TIMEOUT,
                        help=f"wall-clock budget for a --run-controllers render, in seconds "
                             f"(default: {CONTROLLER_TIMEOUT}); on expiry the page is rendered "
                             f"again isolated")
    parser.add_argument("--fail-on-layout", dest="fail_on_layout", action="store_true",
                        help="exit 4 when the LAYOUT block has any finding, for CI use. It's "
                             "the exit code and nothing else that changes: the findings are "
                             "reported either way, and STATUS: ok still prints.")
    parser.add_argument("--probe", action="append", default=[], metavar="<css-selector>",
                        help="report the rendered DOM for every element matching this "
                             "selector: its opening tag, its measured box and the computed "
                             "styles a layout or icon defect turns on. Repeatable. Reach for "
                             "it when the image shows something is wrong but not why; it "
                             "reads the render you already have rather than costing another. "
                             "Adds a PROBE: block and nothing else.")
    parser.add_argument("--dump-dom", action="store_true",
                        help="write the post-mount DOM beside the PNG (its path with a "
                             ".dom.html suffix) and name it on a DOM: line. The whole page, "
                             "for when you do not yet know what to --probe; a data-heavy page "
                             "can run to hundreds of KB, which is why it is a file. Takes no "
                             "value -- use --out to place it.")
    parser.add_argument("--report", type=_report_spec, metavar="json[:<path>]",
                        help="also write the whole result as one JSON object, for a caller "
                             "that parses rather than reads (default path: the PNG's, with a "
                             ".json suffix). stdout gains exactly one line, REPORT: <path>, "
                             "and nothing else changes.")
    parser.add_argument("--debug", action="store_true",
                        help="print diagnostics to stderr: the resolved classpath, every helper "
                             "command line, and the renderer's own output. stdout is unchanged.")
    parser.add_argument("--dev", action="store_true",
                        help="development mode: suppress the anonymous usage ping for this run, "
                             "so developing or testing the skill does not inflate its usage "
                             "counts. Same effect as DO_NOT_TRACK=1, but per-invocation.")
    return parser.parse_args(argv)


# --- The pipeline --------------------------------------------------------
# One function per step of the pipeline in the module docstring, in that order.

Target = collections.namedtuple(
    "Target", "zul out_path resolved docroot layout request_path")


def locate_zul(raw_path):
    """The argument itself, before any step runs. A non-.zul file is a clean skip
    rather than a usage error: the command is well-formed, but the render server
    answers a bare 404 for anything that is not *.zul, so there is nothing to see."""
    zul = Path(raw_path).expanduser()
    if not zul.is_file():
        # Same exit and shape as an argparse failure (see _Parser.error).
        emit("STATUS", "usage-error")
        # REPORT_ZUL, not `zul`: the field is the absolute path, while the message keeps the
        # path as typed -- it is echoing the caller's own argument back at them.
        write_report(report_for_skip(EXIT_USAGE, "usage-error", REPORT_ZUL,
                                     f"No such file: {zul}"))
        print(f"No such file: {zul}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)
    zul = zul.resolve()
    if zul.suffix.lower() != ".zul":
        raise Skipped(f"{zul.name} is not a .zul file",
                      "pass a .zul file — this renderer cannot render other file types.")
    return zul


def screenshot_path(args, zul: Path) -> Path:
    """The default lands in the *current directory*, not a temp dir: the caller is normally
    about to open this image, and a path they can see beside their work is one they can
    open, keep and delete. `-preview` in the name says it is generated, and the name is
    stable across re-renders so successive rounds overwrite one file instead of littering."""
    if args.out:
        return Path(args.out).expanduser().resolve()
    return Path.cwd() / f"{zul.stem}-preview.png"


def resolve_request(zul: Path, args, resolved):
    """Step 2. The docroot and the request path are one step because the docroot is
    only meaningful as the thing the .zul is relativized against — and the launcher
    refuses to serve anything resolving outside it, so this is also where a .zul in
    an unrelated scratch directory is turned away."""
    if args.webapp:
        docroot, layout = Path(args.webapp).expanduser().resolve(), "explicit --webapp"
    else:
        docroot, layout = resolve_docroot(
            zul, boundary_roots_for(zul, args, resolved),
            resolved["resource_roots"], resolved["webapp_hint"])
    debug("docroot", f"{docroot}  (rule: {layout})")

    if not zul.is_relative_to(docroot):
        raise Skipped(
            f"the .zul is not inside the resolved webapp root, so the render server cannot serve it\n"
            f"    file:    {zul}\n    docroot: {docroot}  (rule: {layout})",
            f"pass --webapp {zul.parent}, or move the file under the docroot",
        )
    return docroot, layout, "/" + urllib.parse.quote(zul.relative_to(docroot).as_posix())


def render(target: Target, java: Path, jar: Path, args, warnings, controllers, layout,
           probes, dom):
    """Steps 5-7: the launcher lives exactly as long as the capture needs it."""
    with Launcher(java, jar, launcher_classpath(target.resolved), target.docroot,
                  args.run_controllers, args.controller_timeout) as launcher:
        url = f"http://127.0.0.1:{launcher.port}{target.request_path}"
        return capture(url, target.out_path, args, warnings, controllers, layout, probes, dom,
                       literal_row_groups(target.zul))


# The three strings of the text contract (spec P0-2 item 4), keyed by the launcher's token.
CONTROLLER_LINES = {"executed": "executed",
                    "skipped": "skipped (isolated)",
                    "failed": "failed \u2192 isolated"}


def controllers_line(args, controllers, launcher: LauncherJar, warnings):
    """The `CONTROLLERS:` value, and the one warning only this function can raise.

    A launcher built before this feature accepts `--isolation off` and ignores it (its
    argument parser stores unknown keys and never reads them), so it renders isolated and
    says nothing. Silence therefore has to be reported: without this warning the reader
    would judge a dimmed placeholder page under the rules for real data, and those rules
    invert on exactly this line."""
    token = controllers.get("mode")
    if token is None:
        if args.run_controllers:
            warnings.append(
                f"--run-controllers was requested but the renderer did not report a controller "
                f"mode, so the page was rendered isolated (placeholders, no Composer): launcher "
                f"{launcher.version} ({launcher.source}) predates this feature — use a newer one")
        return CONTROLLER_LINES["skipped"]
    return CONTROLLER_LINES.get(token, token)


def report_render_error(target: Target, args, details, warnings, controllers_value, dom):
    """A real defect in the .zul — the one non-zero exit the agent should act on."""
    emit("STATUS", "render-error")
    emit("PHASE", details["phase"])
    emit("MESSAGE", details["message"] or "(no message on the error page)")
    if details["location"]:
        emit("LOCATION", details["location"])
    if details["trace"]:
        first = details["trace"].splitlines()
        emit("TRACE", first[0] + (f"  (+{len(first) - 1} more lines)" if len(first) > 1 else ""))
        debug_lines("error page trace", first)
    emit("CONTROLLERS", controllers_value)
    emit("SCREENSHOT", f"{target.out_path}   [ERROR PAGE — this is not your UI]")
    if dom.get("path"):
        emit("DOM", f"{dom['path']}   [ERROR PAGE — this is not your UI]")
    # Said rather than left silent: a caller who asked for a probe and got no block would
    # read it as "nothing matched", which is a claim about their page. This is a claim
    # about ours.
    if args.probe:
        emit("PROBE", "skipped — the error page is not your UI")
    emit_warnings(warnings)
    print("NEXT: fix the .zul at the location above, then re-run this script.")
    return EXIT_RENDER_ERROR


def report_success(target: Target, args, launcher: LauncherJar, warnings, controllers_value,
                   layout, probes, dom):
    resolved = target.resolved
    zk_jars = [j.name for j in resolved["jars"] if re.match(r"zk-\d", j.name)]
    emit("STATUS", "ok")
    emit("SCREENSHOT", target.out_path)
    # Beside SCREENSHOT: because it is the same kind of thing -- an artifact this run wrote,
    # named by its path. Both are absent from a run that did not ask for them.
    if dom.get("path"):
        emit("DOM", dom["path"])
    emit("SIZE", f"{args.width}x{args.height}" + (" (full page)" if args.full_page else ""))
    emit("DOCROOT", f"{target.docroot}  (rule: {target.layout})")
    emit("CLASSPATH", f"{resolved['kind']}, {len(resolved['jars'])} jars + "
                      f"{len(resolved['output_roots'])} output roots + "
                      f"{len(resolved['resource_roots'])} resource roots")
    emit("ZK", ", ".join(zk_jars) or "unknown")
    emit("LAUNCHER", f"{launcher.version} ({launcher.source})")
    emit("CONTROLLERS", controllers_value)
    emit_layout(layout)
    emit_probe(probes)
    emit_warnings(warnings)
    if args.fail_on_layout and (layout.get("findings") or []):
        return EXIT_LAYOUT
    return EXIT_OK


def main(argv=None):
    args = parse_args(argv)
    enable_debug(args)
    global REPORT_TARGET, REPORT_ZUL
    # Before locate_zul, so its exit-3 branch and every later failure can still write one.
    # Resolved even though nothing has validated it yet: a skip report whose `zul` is whatever
    # the caller happened to type is not comparable across working directories, and comparing
    # runs is what the report is for. resolve() is happy with a path that does not exist.
    REPORT_ZUL = Path(args.zul).expanduser().resolve()
    REPORT_TARGET = report_target(args, REPORT_ZUL)
    track_usage_async(dev=args.dev)
    warnings = []
    controllers = {}
    # Not `layout`: Target.layout is the docroot RULE STRING printed on the DOCROOT:
    # line, and a second meaning for that name would read as correct and be wrong.
    layout_findings = {"total": 0, "findings": []}
    # Mutated in place by capture(), the same idiom as `warnings` and `layout_findings`:
    # both are properties of the render rather than of the process.
    probes, dom = [], {}

    zul = locate_zul(args.zul)
    resolved = resolve_classpath(zul, args, warnings)                       # 1
    if args.run_controllers and not resolved["output_roots"]:
        # Said now rather than surfaced later as a ClassNotFoundException from inside the
        # render: the run still proceeds, because a page whose controller lives in a jar on
        # the classpath is legitimate.
        warnings.append("--run-controllers was requested but no compiled classes are on the "
                        "classpath — run your build first (mvn compile / gradle classes)")
    docroot, layout, request_path = resolve_request(zul, args, resolved)    # 2
    target = Target(zul, screenshot_path(args, zul), resolved, docroot, layout, request_path)

    java = find_java(args.java)                                            # 3
    launcher = resolve_launcher(args.launcher_jar, args.launcher_version,   # 4
                               warnings)
    status, details = render(target, java, launcher.path, args, warnings,  # 5-7
                             controllers, layout_findings, probes, dom)

    # Computed once, before either report: it can append a warning of its own.
    controllers_value = controllers_line(args, controllers, launcher, warnings)
    if details is not None:
        code = report_render_error(target, args, details, warnings, controllers_value, dom)
    else:
        if status != 200:
            raise Skipped(f"the render server answered HTTP {status} for {request_path}",
                          "check that the .zul path is correct relative to the docroot")
        code = report_success(target, args, launcher, warnings, controllers_value,
                             layout_findings, probes, dom)
    # Last, and after the exit code exists: --fail-on-layout's 4 is decided on
    # report_success's final line, and REPORT: is the only line allowed after WARNINGS.
    write_report(report_for_run(code, args, target, launcher, warnings, controllers,
                                layout_findings, details, probes, dom))
    return code


if __name__ == "__main__":
    # Unwind through Launcher.__exit__ on Ctrl-C rather than orphaning the JVM.
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(ValueError, OSError):
            signal.signal(sig, lambda *_: sys.exit(130))
    try:
        sys.exit(main())
    except Skipped as skipped:
        print(f"PREVIEW_SKIPPED: {skipped.reason}")
        if skipped.next_step:
            print(f"NEXT: {skipped.next_step}")
        write_report(report_for_skip(EXIT_SKIPPED, "skipped", REPORT_ZUL, skipped.reason,
                                     skipped.next_step))
        if not DEBUG:
            print("hint: re-run with --debug to see the resolved classpath, every helper "
                  "command line and the renderer's own output.", file=sys.stderr)
        sys.exit(EXIT_SKIPPED)
    except Exception as unexpected:
        # A bug in this script is NOT a defect in the .zul, so it must not exit 1 —
        # the caller would go and "fix" working markup. Report it as a skip, and always
        # print the traceback: a crash with no traceback is the one failure nobody can
        # act on. The distinctive "internal error" wording is what the CI smoke test
        # greps for, so a crash can still be told apart from a clean skip.
        traceback.print_exc()
        print(f"PREVIEW_SKIPPED: internal error in preview-zul.py — "
              f"{type(unexpected).__name__}: {unexpected}")
        print(f"NEXT: re-run with --debug and report the output (plus the traceback above) "
              f"at {ISSUE_URL}")
        # Suppressed on top of write_report's own guard: this path exists to print a
        # traceback, and a fault in the report must not become the crash it reports.
        with contextlib.suppress(Exception):
            write_report(report_for_skip(
                EXIT_SKIPPED, "skipped", REPORT_ZUL,
                f"internal error in preview-zul.py — {type(unexpected).__name__}: {unexpected}",
                f"re-run with --debug and report the output (plus the traceback above) "
                f"at {ISSUE_URL}"))
        sys.exit(EXIT_SKIPPED)
