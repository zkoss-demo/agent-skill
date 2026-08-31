# Does zul-writer know it can read the rendered HTML/DOM?

**Answer: no — the skill has no such channel and never mentions one.**
**But the capability was proposed, specced and shipped years-of-thought earlier — in the
IntelliJ plugin, for human eyes only. See *Prior art* below.**

## What the skill actually gets back from a render

Every diagnostic channel `preview-zul.py` offers, and all of them are second-hand:

| Channel | What it carries |
|---|---|
| `SCREENSHOT:` + the PNG | pixels only |
| `LAYOUT:` findings | rule, a CSS locator, one measurement (`text needs 77px, box is 48px`) |
| `WARNINGS:` / `ZK client error:` | console text |
| exit 1 `PHASE:` / `MESSAGE:` / `LOCATION:` | the launcher's error page, parsed |
| `--report json` | the same lines as structured keys — explicitly "adds no information the text block lacks" |
| `--debug` (stderr) | classpath, helper command lines, renderer stdout |

`grep -n add_argument scripts/preview-zul.py` — there is **no** `--dump-html`, `--dump-dom`,
`--probe` or equivalent. `grep -rni html SKILL.md references/*.md` returns only *authoring* advice
("prefer ZK components over native HTML", `<n:div>` fallbacks). No reference file ever tells the
agent the rendered DOM is a thing it could look at.

## And the agent cannot get it on its own

- The launcher serves on `http://127.0.0.1:{launcher.port}` ([preview-zul.py:2202](skills/zul-writer/scripts/preview-zul.py#L2202)),
  but the port is ephemeral, never printed on stdout, and the process is killed when the script exits.
  There is no URL left to `curl` after the fact.
- Even with the URL, `curl` would be useless: the script's own comment at
  [preview-zul.py:1189](skills/zul-writer/scripts/preview-zul.py#L1189) says *"ZK's client engine builds the DOM
  after load; the served HTML is mostly a bootstrap script."* The interesting markup only exists
  post-mount, inside the Playwright page — which the script has, uses for its own audits, and throws away.

That last point is the sharp one: **the script already runs `page.evaluate()` against the live DOM**
for the layout audit and the ZK error-box extraction. It reads exactly the thing the agent needs,
reduces it to one line of text, and discards the rest.

## What that cost, in the eval just run

Four items in [zul-writer-eval-findings.zh-TW.md](tasks/zul-writer-eval-findings.zh-TW.md) are
downstream of this gap — every one is an agent reasoning about a DOM it was never allowed to see:

- **Finding 4 (`z-icon-*` on `<label>`, 3/6 runs).** Three runs saw empty boxes; **all three
  misdiagnosed the cause**, in three different ways (R1: font has no such glyphs → replaced every
  icon with emoji; R2: `~./` webfont 404 → shipped it broken; R5: never noticed). One look at the
  `<label>`'s rendered markup plus its computed `font-family` and `::before` settles it immediately.
  Instead, the wrong diagnosis was then *laundered through* Step 5's "cannot judge" disclaimer.
- **Finding 3 (render cap blown, 3/6).** R5 spent **six diagnostic renders** narrowing down a
  zkcharts per-series entry animation — a question about live element state, answered by
  re-screenshotting and squinting.
- **Anecdote, R6.** Sampled **pixel colours** out of the PNG to establish that ZK paints leftover
  flex space `rgb(224,225,227)`. That is a computed-style lookup performed with an eyedropper.
- **Anecdote, R6.** `hflex="min"` measuring 13–128px short — diagnosed by eye, worked around with a
  blunt CSS `min-width` floor, which R6 itself called "a hammer, not a diagnosis."

The pattern is consistent: when the PNG is not enough, agents do not conclude *"I need the DOM"* —
they burn render rounds, sample pixels, or invent an explanation and ship it.

## Prior art: this was proposed, specced and shipped — in the IDE, for humans

The capability exists. It is **FR-23 "View Rendered HTML"** in the ZK IntelliJ plugin
(`/Users/hawk/Documents/workspace/PLUGIN/zkidea`):

| Where | What it says |
|---|---|
| `doc/zul_preview_spec.md:240` | FR-23: the preview pane's context menu drops CEF's dead **View Source** and adds **View Rendered HTML**, opening the browser's **live DOM** as a read-only `<name>-rendered.html` editor tab |
| `doc/feature_overview.md:229` | `PreviewContextMenu` — calls `CefBrowser.getSource`, "which yields the **live DOM markup** rather than the response bytes" |
| `doc/zul-preview-feature.md:173-196, 294-296` | the user-facing docs, including the troubleshooting table |
| `src/main/java/org/zkoss/zkidea/preview/PreviewContextMenu.java` | shipped, with `PreviewContextMenuTest` pinning the menu-id choice |

**The spec's rationale is word-for-word the gap above.** From `zul_preview_spec.md:255`:

> The dump is the live DOM by design, not the response bytes. For a ZK page those differ completely
> — the response is mostly a `zkmx([…])` bootstrap the client engine expands into DOM — so only the
> DOM answers the question the feature exists for: *is the component missing, or present but hidden?*

And the plugin's troubleshooting table already prescribes exactly the debugging moves the skill's
agents never make:

> - *Pane is blank, but no error page* → "Right-click ▸ **View Rendered HTML** to see whether your
>   component reached the DOM."
> - *A component is missing from the render* → "if the component **is** in the dump, it rendered and
>   the problem is CSS/layout."

That second line is precisely the question R1/R2/R5 could not answer about the empty icon boxes, and
answered wrongly three different ways.

**It was never carried across to the CLI.** `tasks/zul-preview-agent-skill-plan.md` — the plan that
produced `preview-zul.py` — contains **no** match for `FR-23`, `rendered html`, `context menu` or
`devtools`. The port was not weighed and rejected; the question was never asked. The plan took the
render pipeline from the plugin and left the in-pane debugging behind, because "in-pane debugging"
reads like a UI affordance rather than a capability.

So the correct framing is not *"add a new feature"*. It is: **the human using the IDE can see the
rendered DOM; the agent driving the same render pipeline cannot.** One spec, one rationale, one
shipped implementation already argue for it.

## Recommendation

Port FR-23 to the CLI. Two changes, in this order:

1. **`--probe <css-selector>` (primary).** After `ZK_READY`, print for each match: `outerHTML`
   (truncated), the box rect, and a fixed set of computed styles (`display`, `font-family`,
   `overflow`, `width`, `flex`, `background-color`). It reuses machinery the script already has, and
   it pairs naturally with the locators `LAYOUT:` already emits — the agent gets a finding *and* a
   way to inspect it.
2. **`--dump-dom <path>` (escape hatch).** Post-mount `document.documentElement.outerHTML` to a
   **file**, never stdout. A ZK page's DOM is hundreds of KB; dumping it into the transcript would
   trade one blindness for another.

Then one line in SKILL.md Step 5 saying when to reach for it — *"the image shows something is wrong
but not why: probe the element instead of re-rendering."* Without that line the flag will go unused,
exactly as `--report json` risks doing.
