#!/usr/bin/env python3
"""Layer A of the zul-writer test plan: the preview-zul.py CLI contract.

Drives the purpose-built fixtures under `zulwriter-showcase/src/main/webapp/preview-fixtures/`
through the real CLI and asserts on what it prints and what it exits with. Those fixtures were
each verified by hand during the preview-launcher engagement; this script is that verification
made repeatable.

Scope is the **CLI contract** -- exit codes, the stdout blocks, the flags. The rendering engine
underneath has its own JUnit suite in the zkidea repo; this does not duplicate it.

Local only, never on the push path: needs a JDK, the project's ZK jars, a launcher jar and a
headless browser. See tasks/zul-writer-skill-test-plan.md in the zkidea repo.

    ZUL_WRITER_LAUNCHER_JAR=/path/to/zk-preview-launcher-1.0.2.jar python3 test/run-preview-tests.py

Exit 0 = contract holds, 1 = a check failed.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "skills" / "zul-writer" / "scripts" / "preview-zul.py"
WEBAPP = REPO_ROOT / "zulwriter-showcase" / "src" / "main" / "webapp"
FIXTURES = WEBAPP / "preview-fixtures"
# The success-path control. Deliberately a purpose-built fixture and never a showcase page:
# showcase pages get regenerated, and one regenerated clipped label would fail the
# "zero findings" checks for a reason that has nothing to do with the CLI contract.
# Measured clean at viewport 1280 and 1600, and 625px tall.
GOLDEN = FIXTURES / "healthy-page.zul"

# The pinned-digest warning emitted when a run is handed a jar whose bytes are not the pinned
# release -- a local rebuild, say, which differs byte-for-byte from CI's while being functionally
# identical. A run against the published jar does not emit it at all, so this is noise to filter
# rather than a fixture. Filtered by CONTENT and never by count: a check that asserted
# "WARNINGS: 1" would silently swallow a second, real warning.
PIN_NOISE = "is not the pinned launcher"

# Documented order of the stdout blocks a successful render always prints, in this order.
# Three more are conditional and none of them belong in this spine: LAYOUT is inserted between
# CONTROLLERS and WARNINGS when the audit found something, REPORT is appended by --report, and
# WARNINGS prints only when a warning was actually raised -- which a clean run against the
# published jar no longer does.
BLOCK_ORDER = ["STATUS", "SCREENSHOT", "SIZE", "DOCROOT", "CLASSPATH", "ZK", "LAUNCHER",
               "CONTROLLERS"]

RENDER_TIMEOUT = 300
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


# --------------------------------------------------------------------------- helpers

def cli(*args, timeout=RENDER_TIMEOUT, env=None, cwd=None):
    """Run preview-zul.py with exactly these arguments and nothing implicit."""
    child_env = None
    if env is not None:
        child_env = {**os.environ, **env}
    proc = subprocess.run([sys.executable, str(SCRIPT), *args], env=child_env,
                          capture_output=True, text=True, timeout=timeout,
                          cwd=str(cwd or REPO_ROOT))
    return proc.returncode, proc.stdout, proc.stderr


def render(zul, *extra, out_name="out.png", jar=None, timeout=RENDER_TIMEOUT, env=None,
           explicit_jar=True):
    """One render into a fresh temp path. Returns (code, stdout, stderr, png_bytes)."""
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / out_name
        pre = ("--launcher-jar", jar or JAR) if explicit_jar else ()
        code, out, err = cli(*pre, "--out", str(png), *extra, str(zul), timeout=timeout, env=env)
        # Read the bytes before the temp dir goes away; the caller only needs size + magic.
        blob = png.read_bytes() if png.is_file() else None
    return code, out, err, blob


def png_size(blob):
    """(width, height) from the IHDR chunk, which always starts at byte 16."""
    if not blob or not blob.startswith(PNG_MAGIC):
        return None
    return (int.from_bytes(blob[16:20], "big"), int.from_bytes(blob[20:24], "big"))


def size_line(stdout):
    """(width, height) as the SIZE: line reports the viewport actually used."""
    # A --full-page run appends " (full page)" to the line, so match the pair rather than split.
    match = re.match(r"(\d+)x(\d+)", value(stdout, "SIZE") or "")
    return (int(match.group(1)), int(match.group(2))) if match else None


def layout_entries(stdout):
    """The LAYOUT findings, as raw `rule | locator | detail` strings."""
    return [l.strip()[2:] for l in stdout.splitlines()
            if l.startswith("  - ") and l.count("|") >= 2]


def value(stdout, key):
    """The text after `KEY: `, or None when the block is absent."""
    match = re.search(rf"^{key}: (.*)$", stdout, re.MULTILINE)
    return match.group(1).strip() if match else None


def blocks(stdout):
    """The top-level block keys in the order they were printed."""
    return re.findall(r"^([A-Z][A-Z_]*): ", stdout, re.MULTILINE)


def real_warnings(stdout):
    """The indented WARNINGS entries, minus the expected pinned-digest noise."""
    return [line.strip()[2:] for line in stdout.splitlines()
            if line.startswith("  - ") and PIN_NOISE not in line]


# --------------------------------------------------------------------------- checks
# Each check returns a list of failure strings; empty means it passed.

def check_usage_no_args():
    """Exit 3 is EXIT_USAGE and must not be confused with 2 (a legitimate skip)."""
    code, out, _ = cli()
    if code != 3:
        return [f"no arguments: expected exit 3 (EXIT_USAGE), got {code}"]
    return []


def check_skip_missing_jar():
    """A launcher jar that does not exist is a skip, not a ZUL defect."""
    code, out, _ = cli("--launcher-jar", "/nonexistent/none.jar", str(GOLDEN))
    fails = []
    if code != 2:
        fails.append(f"missing jar: expected exit 2, got {code}")
    if not re.search(r"^PREVIEW_SKIPPED:", out, re.MULTILINE):
        fails.append("missing jar: no PREVIEW_SKIPPED: line")
    if "internal error" in out:
        fails.append("missing jar: crashed instead of skipping cleanly")
    return fails


def check_a1_good_page():
    """A1: the golden page renders, in the documented block order, and writes a real PNG."""
    code, out, _, blob = render(GOLDEN)
    fails = []
    if code != 0:
        fails.append(f"golden page: expected exit 0, got {code}\n{out}")
    if value(out, "STATUS") != "ok":
        fails.append(f"golden page: STATUS is {value(out, 'STATUS')!r}, expected 'ok'")
    order = blocks(out)
    # WARNINGS is the one optional block a clean golden run can still produce: it appears when the
    # jar under test is not the pinned release, and vanishes when it is. Accept the spine either
    # way, and nothing else -- an unexpected LAYOUT or REPORT here is still a failure.
    if order not in (BLOCK_ORDER, BLOCK_ORDER + ["WARNINGS"]):
        fails.append(f"golden page: block order {order} != {BLOCK_ORDER} (+ optional WARNINGS)")
    if size_line(out) != (1280, 900):
        fails.append(f"golden page: default viewport is {size_line(out)}, expected (1280, 900)")
    if blob is None:
        fails.append("golden page: no PNG written")
    elif not blob.startswith(PNG_MAGIC):
        fails.append("golden page: the output file is not a PNG")
    if real_warnings(out):
        fails.append(f"golden page: unexpected warning(s): {real_warnings(out)}")
    return fails


def check_a2_render_error():
    """A2: a page that cannot parse is exit 1 with a located message.

    The PNG *is* written here, on purpose: the error page is captured too and the SCREENSHOT line
    is labelled `[ERROR PAGE ...]` so a reader cannot mistake ZK's error page for the UI
    (references/preview-guidelines.md:142). The label is the contract -- assert it, not its absence.
    """
    code, out, _, blob = render(FIXTURES / "render-error.zul")
    fails = []
    if code != 1:
        fails.append(f"render-error: expected exit 1, got {code}\n{out}")
    if value(out, "STATUS") != "render-error":
        fails.append(f"render-error: STATUS is {value(out, 'STATUS')!r}, expected 'render-error'")
    for key in ("PHASE", "MESSAGE", "LOCATION", "NEXT"):
        if value(out, key) is None:
            fails.append(f"render-error: no {key}: line")
    shot = value(out, "SCREENSHOT")
    if shot is None:
        fails.append("render-error: the error page is captured too, so SCREENSHOT: must print")
    elif "[ERROR PAGE" not in shot:
        fails.append(f"render-error: SCREENSHOT: is not labelled [ERROR PAGE ...]: {shot!r}")
    if blob is None:
        fails.append("render-error: no PNG written, but the error-page capture is deliberate")
    return fails


def check_a3_layout_findings():
    """A3: the LAYOUT block reports findings as `rule | locator | detail`."""
    code, out, _, _ = render(FIXTURES / "layout-clipping.zul")
    fails = []
    if code != 0:
        fails.append(f"layout-clipping: expected exit 0, got {code}\n{out}")
    header = value(out, "LAYOUT")
    if header is None:
        return fails + ["layout-clipping: no LAYOUT block -- the fixture stopped producing findings"]
    if not re.fullmatch(r"\d+ findings?", header):
        fails.append(f"layout-clipping: LAYOUT header is {header!r}, expected '<n> findings'")
    entries = [l for l in out.splitlines() if l.startswith("  - ") and PIN_NOISE not in l]
    if not entries:
        fails.append("layout-clipping: LAYOUT header with no entries under it")
    for entry in entries:
        if entry.count("|") < 2:
            fails.append(f"layout-clipping: entry is not `rule | locator | detail`: {entry!r}")
    # LAYOUT is documented as sitting between CONTROLLERS and WARNINGS.
    order = blocks(out)
    if "LAYOUT" in order and order.index("LAYOUT") != order.index("CONTROLLERS") + 1:
        fails.append(f"layout-clipping: LAYOUT is not directly after CONTROLLERS: {order}")
    return fails


def check_a3_fail_on_layout():
    """A3: --fail-on-layout turns findings into exit 4, and STATUS: ok still prints."""
    code, out, _, blob = render(FIXTURES / "layout-clipping.zul", "--fail-on-layout")
    fails = []
    if code != 4:
        fails.append(f"--fail-on-layout: expected exit 4, got {code}\n{out}")
    if value(out, "STATUS") != "ok":
        fails.append("--fail-on-layout: STATUS: ok must still print on exit 4")
    if blob is None:
        fails.append("--fail-on-layout: the screenshot must still be written on exit 4")
    return fails


def check_a3b_clean_page_has_no_layout_block():
    """A3b: no findings means no LAYOUT line at all, and --fail-on-layout stays at 0."""
    code, out, _, _ = render(GOLDEN, "--fail-on-layout")
    fails = []
    if code != 0:
        fails.append(f"clean page + --fail-on-layout: expected exit 0, got {code}\n{out}")
    if value(out, "LAYOUT") is not None:
        fails.append("clean page: printed a LAYOUT block; absence is how zero findings is reported")
    return fails


def check_a4_isolated_is_the_default():
    """A4: controllers are opt-in, so an apply= page renders isolated unless asked."""
    code, out, _, _ = render(FIXTURES / "header-composer.zul")
    fails = []
    if code != 0:
        fails.append(f"header-composer (default): expected exit 0, got {code}\n{out}")
    if value(out, "CONTROLLERS") != "skipped (isolated)":
        fails.append(f"header-composer (default): CONTROLLERS is "
                     f"{value(out, 'CONTROLLERS')!r}, expected 'skipped (isolated)'")
    return fails


def check_a4_run_controllers_executes():
    """A4: --run-controllers on a compiled composer really runs it."""
    code, out, _, blob = render(FIXTURES / "header-composer.zul", "--run-controllers")
    fails = []
    if code != 0:
        fails.append(f"header-composer --run-controllers: expected exit 0, got {code}\n{out}")
    if value(out, "CONTROLLERS") != "executed":
        fails.append(f"header-composer --run-controllers: CONTROLLERS is "
                     f"{value(out, 'CONTROLLERS')!r}, expected 'executed'")
    if blob is None:
        fails.append("header-composer --run-controllers: no PNG written")
    return fails


def check_a5_failing_controller_is_not_a_zul_defect():
    """A5: a throwing composer degrades to isolated, names itself, and still exits 0."""
    code, out, _, blob = render(FIXTURES / "throwing-composer.zul", "--run-controllers")
    fails = []
    if code != 0:
        fails.append(f"throwing-composer: expected exit 0 (a controller fault is not a ZUL "
                     f"defect), got {code}\n{out}")
    controllers = value(out, "CONTROLLERS")
    if controllers is None or "failed" not in controllers or "isolated" not in controllers:
        fails.append(f"throwing-composer: CONTROLLERS is {controllers!r}, "
                     f"expected 'failed -> isolated'")
    if blob is None:
        fails.append("throwing-composer: the isolated screenshot must still be written")
    named = [w for w in real_warnings(out) if "ThrowingComposer" in w]
    if not named:
        fails.append(f"throwing-composer: no WARNINGS entry names the failing class; "
                     f"got {real_warnings(out)}")
    return fails


def check_a6_controller_budget():
    """A6: a controller that outlasts its budget is re-rendered isolated, not left hanging."""
    code, out, _, blob = render(FIXTURES / "sleeping-composer.zul", "--run-controllers",
                                "--controller-timeout", "1")
    fails = []
    if code != 0:
        fails.append(f"sleeping-composer: expected exit 0, got {code}\n{out}")
    controllers = value(out, "CONTROLLERS")
    if controllers is None or "isolated" not in controllers:
        fails.append(f"sleeping-composer: CONTROLLERS is {controllers!r}, expected a fall back "
                     f"to isolated after the budget expired")
    if controllers == "executed":
        fails.append("sleeping-composer: reported 'executed' despite a 1s budget")
    if blob is None:
        fails.append("sleeping-composer: no PNG written after the fall back")
    return fails


def check_a7_missing_controller_class():
    """A7: a controller class absent from the classpath is a controller fault, not a ZUL defect."""
    code, out, _, blob = render(FIXTURES / "uncompiled-composer.zul", "--run-controllers")
    fails = []
    if code != 0:
        fails.append(f"uncompiled-composer: expected exit 0, got {code}\n{out}")
    controllers = value(out, "CONTROLLERS")
    if controllers is None or "isolated" not in controllers:
        fails.append(f"uncompiled-composer: CONTROLLERS is {controllers!r}, expected isolated")
    if blob is None:
        fails.append("uncompiled-composer: no PNG written")
    if not [w for w in real_warnings(out) if "NeverCompiledComposer" in w]:
        fails.append(f"uncompiled-composer: no WARNINGS entry names the missing class; "
                     f"got {real_warnings(out)}")
    return fails


def check_a8_width_is_honoured_verbatim():
    """A8: --width is honoured as given, and SIZE: reports the viewport actually used.

    Deliberately NOT a clamp test: nothing clamps, and nothing ever promised to. SKILL.md advises
    the agent on which width to *choose* and now gives the reason -- a very narrow render
    manufactures clipped-text findings the same markup does not produce at desktop width -- but the
    script honours whatever it is handed. Measured on the golden page: 800 renders clean, 400
    produces 10 clipped-text findings, and both report their own width on the SIZE: line. 1600 is
    the realistic case here, a 1600px mockup.
    """
    code, out, _, _ = render(GOLDEN, "--width", "1600")
    fails = []
    if code != 0:
        fails.append(f"--width 1600: expected exit 0, got {code}\n{out}")
    size = size_line(out)
    if size is None:
        fails.append("--width 1600: no parsable SIZE: line")
    elif size[0] != 1600:
        fails.append(f"--width 1600: SIZE: reports width {size[0]}, expected 1600")
    return fails


def check_a9_full_page_never_resizes_the_viewport():
    """A9: --full-page stitches a taller PNG but leaves the viewport alone.

    Both halves are asserted against the run's own SIZE: line rather than against a hard-coded
    height, so neither depends on how tall the golden page happens to be today. A short page
    coming back exactly viewport-tall is the documented "flex-sized, not truncated" signal.
    """
    fails = []

    # A page far shorter than the viewport: the capture cannot exceed it.
    code, out, _, blob = render(FIXTURES / "include-bound-src.zul", "--full-page")
    size, png = size_line(out), png_size(blob)
    if code != 0 or size is None or png is None:
        fails.append(f"short page --full-page: exit {code}, SIZE {size}, PNG {png}")
    elif png[1] != size[1]:
        fails.append(f"short page --full-page: PNG is {png[1]}px tall but the viewport is "
                     f"{size[1]}px; a page with nothing below the fold must match it")

    # A real page against a deliberately short viewport: the capture must grow past it.
    code, out, _, blob = render(GOLDEN, "--full-page", "--height", "300")
    size, png = size_line(out), png_size(blob)
    if code != 0 or size is None or png is None:
        fails.append(f"long page --full-page: exit {code}, SIZE {size}, PNG {png}")
    else:
        if png[1] <= size[1]:
            fails.append(f"long page --full-page: PNG is {png[1]}px tall, viewport {size[1]}px; "
                         f"--full-page did not stitch past the fold")
        if size[1] != 300:
            fails.append(f"long page: SIZE: reports height {size[1]}, expected the requested 300 "
                         f"-- --full-page must not resize the browsing context")
    return fails


def check_a10_literal_include_is_resolved():
    """A10: a constant-literal bound src is included for real (issue #69, commit 9b81416).

    The fragment carries `label#includeProbe`, which clips on purpose, so the layout audit names
    it in a locator whenever the fragment is really in the DOM. That is the only DOM evidence the
    CLI can give; it does mean this check leans on the layout audit, which A3 covers separately.
    """
    code, out, _, _ = render(FIXTURES / "include-literal-src.zul")
    fails = []
    if code != 0:
        fails.append(f"include-literal-src: expected exit 0, got {code}\n{out}")
    if not [e for e in layout_entries(out) if "label#includeProbe" in e]:
        fails.append(f"include-literal-src: the fragment was not included -- no finding located "
                     f"at label#includeProbe. Entries: {layout_entries(out)}")
    return fails


def check_a10_bound_include_is_a_silent_gap():
    """A10: isolated, a ViewModel-supplied src leaves a silent gap -- and that is not a defect.

    Nothing may be invented here: no error, no warning, and no layout finding. An agent that sees
    a failure signal on this page is being told to "fix" a page that is already correct.
    """
    code, out, _, blob = render(FIXTURES / "include-bound-src.zul")
    fails = []
    if code != 0:
        fails.append(f"include-bound-src: expected exit 0, got {code}\n{out}")
    if value(out, "CONTROLLERS") != "skipped (isolated)":
        fails.append(f"include-bound-src: CONTROLLERS is {value(out, 'CONTROLLERS')!r}")
    if [e for e in layout_entries(out) if "label#includeProbe" in e]:
        fails.append("include-bound-src: the fragment rendered without the ViewModel running")
    if value(out, "LAYOUT") is not None:
        fails.append(f"include-bound-src: a gap must not produce a LAYOUT finding; "
                     f"got {layout_entries(out)}")
    if real_warnings(out):
        fails.append(f"include-bound-src: a gap must not warn; got {real_warnings(out)}")
    if blob is None:
        fails.append("include-bound-src: no PNG written")
    return fails


def check_a10_mode_inversion():
    """A10: the same page, with controllers on, includes the fragment for real."""
    code, out, _, _ = render(FIXTURES / "include-bound-src.zul", "--run-controllers")
    fails = []
    if code != 0:
        fails.append(f"include-bound-src --run-controllers: expected exit 0, got {code}\n{out}")
    if value(out, "CONTROLLERS") != "executed":
        fails.append(f"include-bound-src --run-controllers: CONTROLLERS is "
                     f"{value(out, 'CONTROLLERS')!r}, expected 'executed'")
    if not [e for e in layout_entries(out) if "label#includeProbe" in e]:
        fails.append(f"include-bound-src --run-controllers: the ViewModel ran but the fragment "
                     f"is absent. Entries: {layout_entries(out)}")
    return fails


def check_a11_json_report_agrees_with_stdout():
    """A11: --report adds exactly one line to stdout, and the JSON cannot disagree with it.

    Both runs must share one --out path. Give them separate temp dirs and the SCREENSHOT: lines
    differ on their own, which looks exactly like the contract being broken -- the implementation
    log's "byte-identical, modulo the --out path" caveat is load-bearing here.
    """
    import json
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "out.png"
        report = Path(tmp) / "r.json"
        fixture = str(FIXTURES / "layout-clipping.zul")

        plain_code, plain_out, _ = cli("--launcher-jar", JAR, "--out", str(png), fixture)
        code, out, _ = cli("--launcher-jar", JAR, "--out", str(png),
                           "--report", f"json:{report}", fixture)

        if code != plain_code:
            fails.append(f"--report changed the exit code: {plain_code} -> {code}")
        if value(out, "REPORT") is None:
            fails.append("--report: no REPORT: line on stdout")
        stripped = "\n".join(l for l in out.splitlines() if not l.startswith("REPORT: "))
        if stripped.strip() != plain_out.strip():
            fails.append("--report changed stdout beyond adding the REPORT: line")
        if not report.is_file():
            return fails + ["--report: the JSON file was not written"]
        try:
            data = json.loads(report.read_text())
        except Exception as exc:
            return fails + [f"--report: the JSON does not parse: {exc}"]
        header = value(out, "LAYOUT") or ""
        printed = int(header.split()[0]) if header[:1].isdigit() else None
        total = (data.get("layout") or {}).get("total")
        if printed is None:
            fails.append("--report: the fixture printed no LAYOUT header to cross-check against")
        elif total != printed:
            fails.append(f"--report: layout.total is {total} but the LAYOUT: header says {printed}")
    return fails


def check_a14_default_out_is_the_cwd():
    """With no --out the PNG lands in the *current directory* as <name>-preview.png. Run from a
    disposable cwd, not the repo: that both proves the path follows the caller and keeps the
    suite from leaving images behind."""
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        # resolve(): on macOS the temp dir is a symlink, and the script reports Path.cwd(),
        # which is the real path.
        expected = Path(tmp).resolve() / f"{GOLDEN.stem}-preview.png"
        code, out, _ = cli("--launcher-jar", JAR, str(GOLDEN), cwd=tmp)
        if code != 0:
            fails.append(f"default out: expected exit 0, got {code}\n{out}")
        if value(out, "SCREENSHOT") != str(expected):
            fails.append(f"default out: SCREENSHOT is {value(out, 'SCREENSHOT')!r}, "
                         f"expected {str(expected)!r}")
        if not expected.is_file():
            fails.append(f"default out: no PNG at {expected}; cwd held {[p.name for p in Path(tmp).iterdir()]}")
        elif expected.read_bytes()[:8] != PNG_MAGIC:
            fails.append(f"default out: {expected.name} is not a PNG")
    return fails


def check_a13_launcher_precedence():
    """A13: --launcher-jar wins over the environment, and the LAUNCHER: line says which won."""
    fails = []

    # Environment pointing somewhere useless must not beat an explicit flag.
    code, out, _, _ = render(GOLDEN, env={"ZUL_WRITER_LAUNCHER_JAR": "/nonexistent/none.jar"})
    if code != 0:
        fails.append(f"--launcher-jar over a bad env var: expected exit 0, got {code}\n{out}")
    launcher = value(out, "LAUNCHER") or ""
    if "--launcher-jar" not in launcher:
        fails.append(f"LAUNCHER: does not name the flag as the source: {launcher!r}")

    # With no flag, the environment is what gets used -- and is named as such.
    code, out, _, _ = render(GOLDEN, explicit_jar=False,
                             env={"ZUL_WRITER_LAUNCHER_JAR": JAR})
    if code != 0:
        fails.append(f"env-var launcher: expected exit 0, got {code}\n{out}")
    launcher = value(out, "LAUNCHER") or ""
    if "ZUL_WRITER_LAUNCHER_JAR" not in launcher:
        fails.append(f"LAUNCHER: does not name the env var as the source: {launcher!r}")
    return fails


def check_a15_every_clipping_ancestor_is_measured():
    """A15: text is measured against every clipping ancestor, not only the nearest one.

    The regression sample for a false negative that mattered. A roomy `overflow:hidden` box
    nested inside a narrow one made plainly cut text measure as fitting, so the LAYOUT block --
    which the skill tells the agent to trust as the browser's own measurement rather than an
    opinion -- stayed silent about a label with a letter missing. What a text run is visible
    inside is the intersection of its clipping ancestors, not the first one found walking up.
    """
    code, out, _, _ = render(FIXTURES / "layout-nested-clip.zul")
    fails = []
    if code != 0:
        fails.append(f"layout-nested-clip: expected exit 0, got {code}\n{out}")
    entries = layout_entries(out)
    nested = [e for e in entries if "Clipped by the outer box" in e]
    if not nested:
        fails.append("layout-nested-clip: the outer-clipper case produced no finding -- only the "
                     f"nearest clipping ancestor is being measured again:\n{entries}")
    elif not nested[0].startswith("clipped-text"):
        fails.append(f"layout-nested-clip: expected clipped-text, got {nested[0]!r}")
    # The negative control shares the page, so a rule that fires on everything fails here too.
    if any("This one fits" in e for e in entries):
        fails.append(f"layout-nested-clip: reported a text run that fits its box:\n{entries}")
    return fails


def check_a16_escapes_parent_needs_something_to_lose():
    """A16: escapes-parent reports content the reader loses, not a bare box edge.

    Three status bars differing only in the height of the box that clips them. Each is sized
    `height:100%` with vertical padding under `content-box`, so its box is always the parent plus
    the padding: the overflow figure is the same number at every parent height, and growing the
    parent -- the one move the message invites -- can never change it. Nothing renders in the
    strip that gets cut. The fourth block spills a painted box for real and must keep reporting,
    which is what separates fixing the rule from switching it off.
    """
    code, out, _, _ = render(FIXTURES / "layout-escapes-parent.zul")
    fails = []
    if code != 0:
        fails.append(f"layout-escapes-parent: expected exit 0, got {code}\n{out}")
    entries = layout_entries(out)
    for bar in ("sb34", "sb52", "sb64"):
        if any(bar in e for e in entries):
            fails.append(f"layout-escapes-parent: {bar} reported an overflow with nothing rendered "
                         f"in the strip that gets clipped:\n{entries}")
    spill = [e for e in entries if "div.spill" in e]
    if not spill:
        fails.append("layout-escapes-parent: the genuine overflow stopped being reported -- the "
                     f"rule was turned off rather than corrected:\n{entries}")
    elif not spill[0].startswith("escapes-parent"):
        fails.append(f"layout-escapes-parent: expected escapes-parent, got {spill[0]!r}")
    return fails


def check_a17_capture_of_an_animated_page_is_reproducible():
    """A17: two captures of a page with a JS-driven animation are byte-identical.

    A chart left on its default entry animation. Playwright's `animations="disabled"` covers CSS
    animations and transitions and nothing else, and a charting library draws its entry animation
    from requestAnimationFrame onto SVG attributes -- so none of the waits before the capture
    used to promise the page had stopped moving. Two renders, same bytes, is that promise.
    """
    fails = []
    first_code, first_out, _, first = render(FIXTURES / "chart-animation.zul", "--run-controllers")
    second_code, second_out, _, second = render(FIXTURES / "chart-animation.zul", "--run-controllers")
    for tag, code, out in (("first", first_code, first_out), ("second", second_code, second_out)):
        if code != 0:
            fails.append(f"chart-animation ({tag}): expected exit 0, got {code}\n{out}")
    if first is None or second is None:
        return fails + ["chart-animation: a capture produced no PNG"]
    if first != second:
        fails.append(f"chart-animation: two captures differ ({len(first)} vs {len(second)} bytes) "
                     "-- the page was still moving when at least one of them was taken")
    return fails


def check_a18_zk_engine_is_recognised_on_a_busy_page():
    """A18: a page whose main thread is saturated is still recognised as a ZK page.

    The regression sample for a check that asked the wrong thing. "Is window.zk defined within
    5s?" was evaluated on the page's own main thread, and on a page holding one div and one chart
    that thread is blocked for 4.6s straight by mounting plus chart construction -- so the check
    expired and declared "no ZK content" about a page that had been fully mounted for seconds,
    then skipped the mount wait and captured whatever was on screen. Measured on this fixture:
    zk.wpd finished downloading at 499ms and window.zk existed at 2.5s, so nothing about it was
    ever slow to load.

    Whether a page has a ZK client engine is now read from the HTML the server sent, which needs
    no main thread and cannot be starved. Both halves are asserted, because a check that answered
    "yes, ZK" for everything would pass the first half alone.
    """
    fails = []
    _, _, busy_err, _ = render(FIXTURES / "chart-animation.zul", "--run-controllers", "--debug")
    if "zk client engine: mounted" not in busy_err:
        fails.append("chart-animation: the ZK client engine was not recognised on a page whose "
                     "main thread is busy -- the detection is back on a clock")
    _, _, plain_err, _ = render(FIXTURES / "render-error.zul", "--debug")
    if "loads nothing from /zkau/" not in plain_err:
        fails.append("render-error: a page with no ZK client engine was not identified as one, "
                     "so every non-ZK page now waits out the full mount budget")
    return fails


CHECKS = [
    ("usage/no-args        ", check_usage_no_args),
    ("skip/missing-jar     ", check_skip_missing_jar),
    ("A1  golden page      ", check_a1_good_page),
    ("A2  render error     ", check_a2_render_error),
    ("A3  layout findings  ", check_a3_layout_findings),
    ("A3  --fail-on-layout ", check_a3_fail_on_layout),
    ("A3b clean page       ", check_a3b_clean_page_has_no_layout_block),
    ("A4  isolated default ", check_a4_isolated_is_the_default),
    ("A4  --run-controllers", check_a4_run_controllers_executes),
    ("A5  failing composer ", check_a5_failing_controller_is_not_a_zul_defect),
    ("A6  controller budget", check_a6_controller_budget),
    ("A7  missing class    ", check_a7_missing_controller_class),
    ("A8  --width honoured ", check_a8_width_is_honoured_verbatim),
    ("A9  --full-page      ", check_a9_full_page_never_resizes_the_viewport),
    ("A10 literal include  ", check_a10_literal_include_is_resolved),
    ("A10 bound = gap      ", check_a10_bound_include_is_a_silent_gap),
    ("A10 mode inversion   ", check_a10_mode_inversion),
    ("A11 --report json    ", check_a11_json_report_agrees_with_stdout),
    ("A13 jar precedence   ", check_a13_launcher_precedence),
    ("A14 default out = cwd", check_a14_default_out_is_the_cwd),
    ("A15 nested clippers ", check_a15_every_clipping_ancestor_is_measured),
    ("A16 escapes w/ content", check_a16_escapes_parent_needs_something_to_lose),
    ("A17 stable capture   ", check_a17_capture_of_an_animated_page_is_reproducible),
    ("A18 zk engine detected", check_a18_zk_engine_is_recognised_on_a_busy_page),
]

# A12, the exit-code map, has no check of its own on purpose: 0, 1, 2, 3 and 4 are each already
# asserted above (A1, A2, skip/missing-jar, usage/no-args, A3 --fail-on-layout). A separate row
# would re-run five renders to prove what is already proven.


def main():
    global JAR
    JAR = os.environ.get("ZUL_WRITER_LAUNCHER_JAR", "")
    if not JAR or not Path(JAR).is_file():
        print("ZUL_WRITER_LAUNCHER_JAR must point at a launcher jar.\n"
              "Build one with:  ./gradlew :zk-preview-launcher:releaseLauncher   (in the zkidea repo)",
              file=sys.stderr)
        return 3

    failed = 0
    for name, check in CHECKS:
        try:
            fails = check()
        except subprocess.TimeoutExpired:
            fails = [f"timed out after {RENDER_TIMEOUT}s"]
        if fails:
            failed += 1
            print(f"FAIL   {name}")
            for line in fails:
                for physical in line.splitlines():
                    print(f"         {physical}")
        else:
            print(f"ok     {name}")

    print("-" * 60)
    print(f"{len(CHECKS)} checks | {failed} failed")
    print("Result: " + ("✗ contract broken" if failed else "✓ CLI contract holds"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
