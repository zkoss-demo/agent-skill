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
  uv run preview-zul.py --out /tmp/page.png page.zul          # choose where the PNG lands
  uv run preview-zul.py --debug page.zul                      # diagnostics on stderr; try this on ANY failure
  uv run preview-zul.py --webapp src/main/webapp page.zul     # the docroot was guessed wrong
  uv run preview-zul.py --classpath "$(cat cp.txt)" page.zul  # skip Maven/Gradle resolution entirely
  uv run preview-zul.py --full-page --width 1440 page.zul     # wider / whole-page capture

`uv run` is the recommended form: uv reads the PEP 723 metadata above and provides
`playwright` in an ephemeral environment. uv supplies the Python package only, never a
browser — which is why this drives the system Chrome or Edge rather than a Playwright-managed
one. Plain `python3 preview-zul.py` also works where playwright is already installed.

OPTIONS worth knowing, and when to reach for one

  -o/--out PNG     where to write the image (default: <tmpdir>/zul-preview/<name>.png)
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
  also: --launcher-jar --launcher-version --browser-channel --width --height
        --full-page --timeout

READING THE RESULT — stdout is one `KEY: value` per line. Branch on the first line:

  STATUS: ok            → open the path on the SCREENSHOT: line and LOOK at the image
  STATUS: render-error  → a real defect in the .zul; PHASE / MESSAGE / LOCATION say where
  PREVIEW_SKIPPED: …    → no preview was possible, and that is NOT a defect in the .zul.
                          Report it in one line and move on; never describe an image you
                          did not see. The NEXT: line says what would enable it.

WARNINGS: entries are advisory. A 404 on a ZK asset usually means an add-on jar is missing
from the classpath, so the image can look plausible and still be wrong.

Exit codes:
  0  rendered            STATUS: ok           + SCREENSHOT: <path>
  1  render error        STATUS: render-error — a real defect in the .zul
  2  no preview possible PREVIEW_SKIPPED: <reason> — NOT a defect in the .zul
  3  usage error

WHAT THE IMAGE SHOWS

The rendering itself is done by ZK's own DHtmlLayoutServlet inside the launcher, so the
image shows what ZK really produces — but only the FIRST PAINT, and with no ViewModel and
no Composer. Bound values appear as dimmed placeholder text; a bound `src` is the
exception, contributing nothing at all rather than a placeholder. That is correct
behaviour, not a defect. The project's own classes DO load, so a <zscript> or use="..."
naming one of them runs for real.

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
from pathlib import Path


# --- Anonymous, aggregate usage tracking ---------------------------------
# Privacy by design: sends NO identifier of any kind — no visitor ID, no
# cookie, no per-install file. Each run is an independent, unlinkable event
# carrying only the skill name and version.
#
# Fired on a background daemon thread so a slow/unreachable network never
# delays rendering. Opt out entirely by setting DO_NOT_TRACK=1 or
# TRACK_URL="" in the env.

TRACK_URL = os.environ.get("TRACK_URL", "https://www.zkoss.org/api/track")
SKILL_VERSION = "1.1.0"


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


def track_usage_async():
    """Fire the anonymous usage ping on a background thread; returns immediately."""
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
LAUNCHER_VERSION = "1.0.2"
LAUNCHER_SHA256 = "bab6493c2168e909e562299e041c9b3d2bb7719b7ad1c145b5db0dd365ea5b82"
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
BUILD_TIMEOUT = 240           # seconds for a mvn/gradle classpath resolution

EXIT_OK, EXIT_RENDER_ERROR, EXIT_SKIPPED, EXIT_USAGE = 0, 1, 2, 3

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
    def __init__(self, java: Path, jar: Path, entries, docroot: Path):
        self.java, self.jar, self.entries, self.docroot = java, jar, entries, docroot
        self.proc = None
        self.port = None
        self._stderr_tail = collections.deque(maxlen=200)
        self._stdout_lines = queue.Queue()

    def __enter__(self):
        argv = [str(self.java), "-jar", str(self.jar),
                "--classpath", os.pathsep.join(str(p) for p in self.entries),
                "--webapp", str(self.docroot), "--port", "0"]
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


# --- Capture -------------------------------------------------------------

# ZK's client engine builds the DOM after load; the served HTML is mostly a
# bootstrap script. These flags are set at the end of ZK's initial mount pipeline
# and have been stable client API since ZK 5, so this covers ZK 9 and 10 alike.
ZK_READY = """() => {
  const z = window.zk;
  return !!z && z.booted === true && z.mounting !== true && !z.loading && z.processing !== true;
}"""


def capture(url, out_path: Path, args, warnings):
    """Returns (http_status, error_details_or_None)."""
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
            page.on("pageerror", lambda e: warnings.append(f"page error: {str(e).splitlines()[0]}"))
            missing = []
            page.on("response", lambda r: missing.append(r.url) if r.status >= 400
                    and "/zkau/web/" in r.url else None)

            timeout_ms = args.timeout * 1000
            debug("GET", url)
            response = page.goto(url, wait_until="load", timeout=timeout_ms)
            status = response.status if response else 0
            debug("http status", status)

            try:
                page.wait_for_function("() => typeof window.zk !== 'undefined'", timeout=5000)
            except PWTimeout:
                # No ZK client engine: this is the launcher's error page, or a page
                # with no ZK content. Capture it as-is rather than failing.
                debug("zk client engine", "absent (error page, or no ZK content)")
            else:
                try:
                    page.wait_for_function(ZK_READY, timeout=timeout_ms)
                    debug("zk client engine", "mounted")
                except PWTimeout:
                    warnings.append(f"ZK's client engine did not finish mounting within "
                                    f"{args.timeout}s — captured the page as-is")
            with contextlib.suppress(PWTimeout):
                page.wait_for_load_state("networkidle", timeout=5000)
            with contextlib.suppress(Exception):
                page.evaluate("() => (document.fonts ? document.fonts.ready : null)")

            details = _scrape_error(page) if status >= 500 else None

            out_path.parent.mkdir(parents=True, exist_ok=True)
            # animations/caret disabled so repeated captures are comparable if the
            # caller diffs a before/after pair.
            page.screenshot(path=str(out_path), full_page=args.full_page,
                            animations="disabled", caret="hide")
            debug("screenshot", f"{out_path} ({out_path.stat().st_size} bytes)")

            for url_404 in dict.fromkeys(missing):
                warnings.append(f"ZK resource not served: {url_404} — an add-on jar may be "
                                "missing from the classpath, so the image may be misleading")
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


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse exits 2 by default, which is this script's "skipped" code.
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)


def parse_args(argv):
    parser = _Parser(description="Render a ZK .zul file to a PNG screenshot.")
    parser.add_argument("zul", help="the .zul file to render")
    parser.add_argument("-o", "--out", help="output PNG (default: a per-file path under the system temp dir)")
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
    parser.add_argument("--debug", action="store_true",
                        help="print diagnostics to stderr: the resolved classpath, every helper "
                             "command line, and the renderer's own output. stdout is unchanged.")
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
        print(f"No such file: {zul}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)
    zul = zul.resolve()
    if zul.suffix.lower() != ".zul":
        raise Skipped(f"{zul.name} is not a .zul file",
                      "pass a .zul file — this renderer cannot render other file types.")
    return zul


def screenshot_path(args, zul: Path) -> Path:
    if args.out:
        return Path(args.out).expanduser().resolve()
    return Path(tempfile.gettempdir()) / "zul-preview" / f"{zul.stem}.png"


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


def render(target: Target, java: Path, jar: Path, args, warnings):
    """Steps 5-7: the launcher lives exactly as long as the capture needs it."""
    with Launcher(java, jar, launcher_classpath(target.resolved), target.docroot) as launcher:
        url = f"http://127.0.0.1:{launcher.port}{target.request_path}"
        return capture(url, target.out_path, args, warnings)


def report_render_error(target: Target, details, warnings):
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
    emit("SCREENSHOT", f"{target.out_path}   [ERROR PAGE — this is not your UI]")
    emit_warnings(warnings)
    print("NEXT: fix the .zul at the location above, then re-run this script.")
    return EXIT_RENDER_ERROR


def report_success(target: Target, args, launcher: LauncherJar, warnings):
    resolved = target.resolved
    zk_jars = [j.name for j in resolved["jars"] if re.match(r"zk-\d", j.name)]
    emit("STATUS", "ok")
    emit("SCREENSHOT", target.out_path)
    emit("SIZE", f"{args.width}x{args.height}" + (" (full page)" if args.full_page else ""))
    emit("DOCROOT", f"{target.docroot}  (rule: {target.layout})")
    emit("CLASSPATH", f"{resolved['kind']}, {len(resolved['jars'])} jars + "
                      f"{len(resolved['output_roots'])} output roots + "
                      f"{len(resolved['resource_roots'])} resource roots")
    emit("ZK", ", ".join(zk_jars) or "unknown")
    emit("LAUNCHER", f"{launcher.version} ({launcher.source})")
    emit_warnings(warnings)
    return EXIT_OK


def main(argv=None):
    args = parse_args(argv)
    enable_debug(args)
    track_usage_async()
    warnings = []

    zul = locate_zul(args.zul)
    resolved = resolve_classpath(zul, args, warnings)                       # 1
    docroot, layout, request_path = resolve_request(zul, args, resolved)    # 2
    target = Target(zul, screenshot_path(args, zul), resolved, docroot, layout, request_path)

    java = find_java(args.java)                                            # 3
    launcher = resolve_launcher(args.launcher_jar, args.launcher_version,   # 4
                               warnings)
    status, details = render(target, java, launcher.path, args, warnings)   # 5-7

    if details is not None:
        return report_render_error(target, details, warnings)
    if status != 200:
        raise Skipped(f"the render server answered HTTP {status} for {request_path}",
                      "check that the .zul path is correct relative to the docroot")
    return report_success(target, args, launcher, warnings)


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
        sys.exit(EXIT_SKIPPED)
