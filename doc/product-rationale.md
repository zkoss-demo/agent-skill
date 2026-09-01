# Why zul-writer is shaped the way it is

Condensed from the planning documents that produced the skill. Everything here is *motivation* —
the reasoning that does not survive in the code, and that a reader of `SKILL.md` or
`preview-zul.py` cannot reconstruct.

---

## 1. The preview exists for the model's eyes, not the developer's

The question that nearly killed Step 5: *"IntelliJ users already have a ZUL preview pane, and
VS Code users should get a VS Code panel. How many people work purely in a terminal with an AI?"*

That question assumes the consumer of the preview is **a human's eyes**. On that axis the objection
is correct and unanswerable. But it is the wrong axis.

| | IntelliJ layout preview | `preview-zul.py` |
|---|---|---|
| Output | a JCEF browser panel inside the IDE | a PNG on disk |
| Who looks | a person | the agent (a person can too, later) |
| Who closes the loop | person looks → describes in words → pastes back | agent reads image → edits ZUL → re-renders |
| Prerequisites | IDE open, panel open, person watching | a JDK and Chrome |

**An IDE preview does not make this redundant, because the agent cannot see the IDE preview.** Even
with the developer sitting in front of an open preview pane, the agent that wrote the ZUL is blind,
and the human becomes a manual describe-the-picture proxy. This holds for our own products too: the
Claude Code JetBrains plugin is a chat panel — it cannot read what the ZUL preview tool window in
the same IDE rendered.

So the real axis is **who converges the feedback loop — the person or the agent**. On that axis the
overlap with the IDE feature is close to zero, and the audience is *every developer who lets an
agent write ZUL for them*: a superset of the IntelliJ, VS Code and terminal populations, plus
headless contexts (CI, cloud agents, scheduled runs, review bots).

### Why not build it as a VS Code extension

1. A VS Code panel renders for human eyes, so it does not solve the problem above — it copies the
   IntelliJ gap onto a second host.
2. Cost: a new TypeScript codebase, host integration, a marketplace listing and a second renderer
   hosting story — serving a *subset* of who the Python script already reaches.
3. `preview-zul.py` is host-agnostic by design. It already serves VS Code users today, through the
   agent, with nothing shipped to VS Code.

Recorded for later: **an MCP server** ("render this .zul, return an image") wraps the same
resolution logic and would serve agents in *any* host without a per-host build. That is a thin shell
on top of the launcher work, not an alternative to it. Deliberately not built yet.

### The same argument was already made once, for humans

Worth knowing before anyone re-debates it: **the capability exists in the IDE.** `FR-23 "View Rendered
HTML"` in the ZK IntelliJ plugin adds a preview-pane context-menu item that opens the browser's **live
DOM** as a read-only editor tab — shipped, with a test pinning the menu-id choice. Its specification's
rationale is word-for-word the argument above:

> The dump is the live DOM by design, not the response bytes. For a ZK page those differ completely —
> the response is mostly a `zkmx([…])` bootstrap the client engine expands into DOM — so only the DOM
> answers the question the feature exists for: *is the component missing, or present but hidden?*

The plugin's own troubleshooting table even prescribes the debugging moves the skill's agents never made
("if the component **is** in the dump, it rendered and the problem is CSS/layout") — precisely the
question three evaluation runs answered wrongly about empty icon boxes.

**It was never carried across to the CLI, and the port was not weighed and rejected — the question was
never asked.** The plan that produced `preview-zul.py` has no mention of it. It took the render pipeline
from the plugin and left the in-pane debugging behind, because "in-pane debugging" reads like a UI
affordance rather than a capability. So the correct framing of `--probe` was never *"add a new feature"*;
it was **the human using the IDE can see the rendered DOM, and the agent driving the same render pipeline
cannot.**

### The honest market risk

It was never "how many people work in a terminal". It is **how many people use the `zul-writer`
skill at all** — the same number that decides whether the skill should exist. Step 5 does not carry
the burden of proving the skill has an audience; it closes the skill's largest quality gap *if*
there is one. This is why the scripts send an anonymous, aggregate usage ping.

---

## 2. The governing principle: facts from scripts, judgement to the AI

Derived from the six-run evaluation and now the rule of thumb for every change to the skill.

> **If a measurement can answer it, do not write prose telling the agent to be careful.**
> Prose gets skipped; a measurement runs every time. Prose asks the agent to remember to look; a
> measurement puts the answer in front of it.

Three consequences that shaped real changes:

- **The `--zk-version` fix was not a sentence in Step 3.** Six runs out of six guessed at the flag's
  semantics and split 3-3 — while the answer was already on screen. The fix was to make the tool
  echo how it read the input (`major version from "10.3.0.1-Eval"`), because *documents get skipped,
  output does not*.
- **The icon defect became a measurement with no ZK knowledge in it.** The rule asks "will this glyph
  draw" (a private-use `::before` codepoint against the page's registered `@font-face` families), not
  "is this a `<label>`". The agent therefore never needs to *know* the ZK fact to avoid the mistake.
- **When no fact can decide, the script still enumerates.** Whether a `groupbox` *should* ship
  collapsed exists only in the mockup — it is intent, not fact. So `STATE:` lists the collapsible
  components and their states, and the agent's job drops from "stare at pixels and spot the
  difference" to "compare two lists". The first misses; the second mostly does not.

A corollary that removed a question rather than answering it: an early proposal wanted Step 1 to ask
*"does the controller already exist and compile?"* **That was wrong, twice over.** Running the full
workflow means writing a new page, and a ZK Composer/ViewModel is bound to its page (`apply=` /
`viewModel=`) rather than being a shared service layer — so for a new page the answer is constant, and
"already exists" never happens. Where it *can* happen, the answer need not be asked: editing an existing
`.zul` means the class name is already written in the markup, so **look at the file.** Asking the user
for a fact you can look up is using the wrong tool.

The boundary matters as much as the principle. Two findings were deliberately **not** mechanised:
the fix-round budget (a policy number, not a fact) and the data/layout-text boundary (a semantic
judgement). Forcing a script onto those produces false rigour.

---

## 3. The generation policy, and where it came from

The original instruction that set the shape of Step 1 Q4 and the two-pass rule:

> There are two policies for generating a ZUL — **static data** (data written directly in the ZUL)
> and **model-driven** (data set in a Java Composer or ViewModel). Ask the user which.
>
> - Whichever they pick, **still generate a controller** with an event listener (Composer) or a
>   `@Command` method (ViewModel) — *because the example event-listening code is useful to the user
>   regardless.*
> - If they pick model-driven and no controller class is loaded, **still write the ZUL with static
>   data first**, so layout and style can be checked against preview screenshots. That may take
>   several iterations. Only then extract the static data into the controller.

The second bullet is the origin of the whole literal-first-then-extract rule: the point of the
literal pass is that **a screenshot of literal data is the page the user will actually get**, while
a screenshot of unresolved bindings is a skeleton.

The rule's cost had to be discovered by measurement, not reasoning: a bound `model` **silently
discards** the literal children still sitting in the ZUL, even an empty one, with zero warnings.
Forgetting to delete them therefore renders perfectly and lies in the source. See
[zk-measured-behaviour.md](zk-measured-behaviour.md).

---

## 4. Design reasons behind the preview pipeline

Kept because each one is a question a future maintainer will otherwise re-ask.

**The DOM dump goes to a file, never stdout.** Measured post-mount DOM sizes: a healthy page 2.4 KB,
a real dashboard 24 KB (~6k tokens), **a 200×6 grid 231 KB (~58k tokens)** — and data grids are
exactly what this skill generates. A flag that is safe on four pages and destroys the context window
on the fifth is worse than no flag.

**The probe must carry computed styles, not just markup.** All four icon carriers request the
*identical* `::before content`. A markup-only dump would have shown four elements each carrying
`z-icon-bell` and proved nothing.

**The launcher's own HTML is nearly worthless for diagnosis.** The served response is
`zkmx([['zul.wgt.Label', …]])` — the `.zul` restated as JavaScript, which the agent already has. It
answers exactly one question the DOM answers less directly (*did the server create this component at
all* — useful when a Composer builds children conditionally or `if=` evaluated false) and nothing
about why anything looks wrong. Everything of diagnostic value is created client-side, in the DOM the
script already holds and used to throw away. **No launcher change was needed for `--probe`.**

**Class-output directories belong on `--classpath`.** An early version excluded them and called that
"the isolation guarantee". That was backwards: the launcher's `UiFactory` hook is the real boundary —
it never resolves a ViewModel/Composer class name — and the exclusion broke every page whose
`<zscript>`, `use="…"` or custom EL function names a project class. Test output roots are still
excluded, by name on the Maven path and structurally on the Gradle one.

**`main()` is the executable form of the pipeline.** The classpath must resolve *before* the jar is
downloaded, because an unusable classpath has to exit 2 without touching the network (a CI smoke test
pins this). The old numbered section banners never matched that order, so the numbering was dropped
and `main()` became the single place the order lives.

**Agents do not use what they are not told about.** Six runs each independently invented "copy the
project convention" because the skill never sanctioned it, and three runs guessed at the icon cause
rather than looking. Shipping a flag without the prose that names when to reach for it reproduces
that failure — which is also why the skill `description` gained the "work out why a rendered page
looks wrong" clause: the frontmatter is what decides whether the skill is consulted at all.

---

## 5. Two consumers share one binary, and the split is deliberate

```
┌─────────────────────────────────────┐   ┌──────────────────────────────────────┐
│ Consumer A: zul-writer agent skill  │   │ Consumer B: ZK IntelliJ plugin       │
│ github: zkoss-demo/agent-skill      │   │ github: zkoss/zkidea                 │
│ skills/zul-writer/scripts/          │   │ ZulPreviewServerService              │
│   preview-zul.py (CLI)              │   │   .launcherClasspath                 │
│   + Playwright browser capture      │   │   + IDE preview pane                 │
└──────────────┬──────────────────────┘   └──────────────┬───────────────────────┘
               │            both spawn the same jar      │
               └──────────────────┬──────────────────────┘
                                  ▼
              ┌───────────────────────────────────────────────┐
              │ zk-preview-launcher  (Java, Gradle)           │
              │ repo: zkoss/zkidea, module zk-preview-launcher│
              │ Main → PreviewHttpServer, prints PREVIEW_PORT=│
              └───────────────────────────────────────────────┘
```

**Any change must keep both consumers working**, and the two have opposite defaults: the skill
generates both the page and its controller in one session, so running the controller is safe and makes
the screenshot realistic; the plugin previews arbitrary pages in arbitrary user projects while someone
types, so isolation must stay its default. Every new capability is therefore **opt-in at the CLI**, and
the plugin's defaults never change.

| Concern | Lives in |
|---|---|
| ZK classpath / docroot resolution, launcher download, browser drive, text output contract | `preview-zul.py` |
| Booting ZK, serving the page, isolation hooks, placeholder injection, error pages | the launcher (Java) |
| Anything measured *in the rendered DOM* | `preview-zul.py`, via Playwright `page.evaluate` |
| Viewport size, `--full-page`, device scale, screenshot | `preview-zul.py` — **the launcher has no browser.** It is an HTTP server over a mock servlet container. ZK's first paint is viewport-independent and all `hflex`/`vflex` sizing is computed client-side, so the launcher neither learns nor needs these values |
| Request headers ZK reads server-side (`User-Agent` → device/browser detection) | the launcher — this is the one rendering input that is *not* the browser's business |

**How isolation actually works, since it is easy to get wrong.** `PreviewUiFactory` overrides
`UiFactory.newComposer` and always returns a no-op composer. `ComponentInfo.resolveComposer` routes
*both* `apply="user.X"` *and* the auto-applied MVVM composer (`org.zkoss.bind.BindComposer`) through
that one call, so **a single hook blocks MVC and MVVM alike**. The project's compiled output roots are
already on the launcher classpath — see §4 — so isolation comes from the UiFactory hook, **not** from
withholding classes. `PlaceholderInjector` runs from that no-op composer, which is why the dimmed
placeholder text and placeholder grid rows disappear when isolation is off.

---

## 6. When to read ZK's source, and when not to

Derived from a run that opened three resources inside the distributed `zul` jar and got two of them
right. The client sources (`.ts`) and theme CSS (`.dsp`) ship *inside* the jar, so any project that
resolves ZK through Maven or Gradle has them locally — the same precondition `preview-zul.py` already
requires. Availability is not the issue; **cost and reliability are.**

> **"Does this name or resource exist?"** → a jar or doc lookup is fair game. Cheap and decisive.
>
> **"How does this component behave at runtime?"** → do not read source. Use, in order: the `zk-doc`
> MCP, the javadoc, then just render it. **The preview loop is the cheaper and more reliable oracle,
> and it is already part of the workflow.**

The two halves, from the run that produced the rule:

- **Worth it:** grepping the jar for which `z-icon-*` names exist in this ZK version. Neither the XSD
  validator nor the parser can check an icon name, and a typo renders nothing in total silence. See
  [zk-measured-behaviour.md](zk-measured-behaviour.md) §20.
- **Waste:** reading `Hlayout.ts` to learn the widget's flex direction. It did **not** predict the
  actual bug — that ZK's client-side `hflex="min"` under-measures a group of inline children and clips
  them. Only the render showed that. A whole tool round spent on source reading, and the important
  thing was still learned empirically.

---

## 7. Deferred content and product ideas

Recorded so they are not re-derived. None of these is in progress.

- **An MCP server wrapping the render** (see §1) — serves agents in any host, one build.
- **A post on CI regression testing for ZUL layout** (`--fail-on-layout` + the JSON report). Real
  value, different audience (build engineers). Worth its own article; currently only a one-line
  mention.
- **A post: "We had an AI build six ZK dashboards, then measured where it broke."** The six-run
  evaluation with quantitative results — renders per page, which defects recur, where the agent
  misdiagnoses. Stronger standalone than as a section.
- **A post on what the agent still gets wrong, and what is next** — moving knowledge earlier (schema
  queries, deterministic source checks) so pages are right on the first write. See
  [knowledge-roadmap.md](knowledge-roadmap.md).
- **A "known limitations" table** lifted from the preview spec — deliberately skipped. The limits are
  already stated in prose, and a table reads as a defect list.
