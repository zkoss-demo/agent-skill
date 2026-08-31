# Does the skill know when to reach for `--probe`?

Assessment of the prose shipped with `26444e6`, against the question: *the flags exist and the
script works — but will the agent actually use them, and at the right moment?*

## Short answer

**"How to use it" is covered. "When to use it" has one concrete hole and two soft spots.**

The hole is not in the Step 5 prose that was written for this feature. It is one table, 460 lines
earlier, that was never updated to match the trigger the frontmatter now advertises.

---

## The hole: the routing table has no row for the job the description now sells

`description` gained this clause in the same commit:

> …or work out why a rendered page looks wrong — a blank icon, a clipped label, an element that is
> not there, a colour or width nobody asked for.

That is a **new entry point**: a user who arrives with a defect, not with a page to build. The first
thing the agent reads in the body is *"Run only the steps the request needs"* (SKILL.md:30), whose
table routes the request to a step. It has six rows. None of them is this one.

| Row | Sends to |
|---|---|
| "Build me a page that…" | 1 → 5 |
| "Preview / screenshot / show me what `foo.zul` looks like" | 5 |
| **"Is this ZUL valid?", "why won't this page parse?"** | **3** |
| "Write the ViewModel for this page" | 4 |
| "Move this page's data into a ViewModel/Composer" | 2 → 4 → 5 |
| "Add a column to this grid", "make the sidebar narrower" | 2 → 3 → 5 |

Now read the row that a defect report lexically matches best. *"Why does this icon render as an
empty box?"* against *"why won't this page parse?"* — same interrogative, same object, adjacent
verb. The agent routes to **Step 3, validation**.

**Step 3 is structurally incapable of finding this defect.** `<label sclass="z-icon-bell"/>` is
perfectly valid ZUL. The validator passes it, the agent reports "the ZUL is valid", and the probe —
which lives in Step 5 and would have settled it in one render — is never reached. The second-best
match is the last row, which routes to Step 2: change the markup and re-render, i.e. guess.

The probe section itself is well written. It is behind a door the routing table doesn't open.

**Fix:** one row. Something like
`| "Why is this icon blank / this label clipped / this section missing?" | 5, with --probe — do not start by editing the markup |`
and a line under the table saying a defect report is a *diagnosis* request, not a fix request:
the page is already written, the question is what the browser did to it.

## Soft spot 1: the probe is gated behind the agent admitting it does not know

The section is titled *"When the image shows a defect but not its cause"* and opens by asking the
agent to notice that it cannot explain what it sees. That is exactly the self-knowledge an LLM is
worst at — the default behaviour on seeing a blank box is to produce a fluent cause, not to notice
that the cause is a guess.

There is one hard counter in the file, and it works: the narrowed 404 bullet (SKILL.md:528) names
the icon case, says in so many words that this bullet has been read as absolving it, and sends the
agent to `--probe`. That is a *specific* instruction attached to a *specific* symptom, which is why
it stands a chance. It covers icons and nothing else.

## Soft spot 2: four defect classes promised, one worked through

The section header names four: blank icon, missing component, wrong colour, wrong width. Only the
icon has an end-to-end path — symptom → selector → *what the output means* → the fix, with a
reference table and a pinned fixture behind it.

The other three get the command and stop there. An agent that probes a sidebar which came out 200px
wide against its `hflex="1"` receives a correct dump of computed styles and no instruction on which
line of it answers the question. The risk is not that it fails to probe; it is that it probes, reads
`width: 200px | flex: 0 1 auto`, and still cannot say why — because nothing told it that
`flex: 0 1 auto` on a child of an `hlayout` means the hflex never reached the widget.

## What is genuinely fine

- **How to invoke it.** Command, quoting, the `LAYOUT:` locator → `--probe` pipeline, and
  `--dump-dom` as the escape hatch for "I don't know what to ask for yet". All present.
- **Why it exists.** The `zkmx([...])` paragraph tells the agent the DOM is the *only* place the
  page exists as markup — that stops the plausible wrong move of fetching the served HTML.
- **Cost.** "It reads the render you already have, so it costs no extra round", plus the explicit
  carve-out in *How many rounds*. Without that the two-round cap would suppress the probe exactly
  when it is most needed.
- **The icon path**, as above — that one is complete.

---

## Proving it rather than asserting it

Everything above is a reading. Three prompts would settle it, each with a defined failure mode:

| # | Prompt | Passes if | The failure it is looking for |
|---|---|---|---|
| 1 | Cold entry: point at a `.zul` whose icons render as empty boxes, ask why | probes, names the `<label>` carrier, cites the font-family evidence | routes to Step 3 and reports "valid"; or blames the missing-resource 404 bullet — **the failure actually observed in `zul-writer-eval-findings.zh-TW.md`** |
| 2 | Cold entry: a page whose sidebar ignores `hflex` | probes the `LAYOUT:` locator, reads the computed flex | probes, dumps styles, cannot conclude (soft spot 2) |
| 3 | Anti-trigger: a page that renders correctly except for dimmed `vm.customer` expression text | recognises *What you cannot judge*, does **not** probe, does not "fix" it | burns a probe round on the renderer behaving correctly |

Test 3 matters as much as 1. The new prose adds a tool the agent wants to use; a skill that probes
every render has traded one waste for another.

Each runs twice — with the skill and without — into `zul-writer-workspace/iteration-1/`.

---

# Results — iteration 1

Three prompts, each run twice: the current skill against the skill as of `53f1050`, before the
probe existed. Six subagents, each in its own sandbox containing the skill and the three fixtures
and **nothing else** — no `tasks/`, no findings docs, so nothing could be answered by grepping the
repo for the answer. The sandbox copies of `preview-zul.py` log their argv, so "did it probe" is
read off a file rather than off the agent's own account of itself.

## The hole was patched first

One row plus a paragraph, 10 lines, in `### Run only the steps the request needs`. Nothing else
was touched — the two soft spots were left in place deliberately, so that a change in behaviour
could be attributed to something.

## What happened

| Eval | | renders | probed | edited | tokens | tool calls | wall |
|---|---|---|---|---|---|---|---|
| 1 icon blank box | new | 3 | **yes** | yes | 71,875 | 16 | 225s |
| | old | 4 | no | yes | 97,115 | 32 | 378s |
| 2 clipped sidebar | new | 3 | **yes** | yes | 63,126 | 11 | 179s |
| | old | 2 | no | no | 63,000 | 10 | 140s |
| 3 bound values (anti-trigger) | new | 1 | **no** | no | 59,594 | 9 | 136s |
| | old | 1 | no | no | 65,362 | 13 | 149s |
| **total** | **new** | | | | **194,595** | **36** | **540s** |
| | **old** | | | | **225,477** | **55** | **667s** |

Assertions: new **14/14**, old **12/14**. But the two the old version missed are `a1` and `b2` —
*"did it use `--probe`"* — which it cannot pass by construction. Strip those and it is **12/12 vs
12/12**.

## The honest headline

**On these three prompts the feature changed how the answer was reached, not whether it was right.**
Both versions diagnosed all three correctly. The gain was cost: on the icon case, half the tool
calls, a quarter fewer tokens, 40% less wall time.

What the old version did instead of probing is the most informative artifact of the run. It
rendered, then called `--help` — looking for a DOM inspection flag and not finding one — then
**wrote its own 8-row comparison fixture**, `icon-probe.zul`, crossing `<label>` / `<span>` /
`iconSclass` against six icon names, plus `z-icon` base-class and `z-icon-solid` variants. It was
reconstructing `icon-carrier.zul` from scratch. Rows C and E2 of that fixture spell
`z-icon-circle-check` and `z-icon-clock` — deliberate misspellings, testing the competing
hypothesis that the class names were simply wrong. The probe kills that hypothesis in one line
(`::before content` is set, so the name resolved); by rendering, it costs a page and a screenshot
comparison.

It then went further than the new version did, reading ZK's own stylesheets and naming the real
mechanism: `font-awesome.css.dsp` and `norm.css.dsp` both match at specificity (0,1,0), so the
later `.z-label` rule wins on source order. That is a better *explanation* than the probe produces.
It cost 32 tool calls to get there.

## The caveat that matters most

**Eval 1's prompt does part of the diagnostic work.** It says *"The Export and New invoice icons in
the toolbar right above them come out fine"* — handing over the falsifying evidence that makes
"the webfont 404'd" untenable. In the real six-run evaluation the agent was reviewing its own page
and had to notice that contrast unprompted; **three runs out of three that met this defect named the
wrong cause.** One old-skill run getting it right here, with the contrast supplied, is not evidence
against that 0/3.

So this iteration measured *"once you know something is odd, how cheaply do you reach the cause"*.
It did **not** measure *"do you notice something is odd at all"* — which is where the documented
failures actually happened. A second iteration should drop the contrast from the prompt.

## What was genuinely settled

- **No over-triggering.** Eval 3 was the risk: a new tool the model wants to use, on a page where
  the right answer is "nothing is wrong". The new version spent **one** render, no probe, and made
  no edit — same as the old one. The *What you cannot judge* section held.
- **The probe is reached when the prose says it should be**, and with the selector the SKILL.md
  example gives (`[class*="z-icon-"]`), on the first try.
- **The evidence it yields is the right evidence.** The new version's write-up refutes the wrong
  answer explicitly — *"content present plus wrong font means wrong carrier, not a 404"* — which is
  precisely the misdiagnosis this feature was built to prevent. It then re-probed after the fix to
  confirm all four carriers had become `ZK85Icons` at 16x16.

## Soft spot 2 was wrong, and the eval says why

The assessment predicted that only the icon case having a worked end-to-end path would leave the
other defect classes stranded. Eval 2 shows the opposite for clipping: **the `LAYOUT:` block already
does that job.** It names the element, the needed width and the actual box, and the old version
reached the correct cause from those numbers alone with no probe at all. The probe added a cleaner
contrast (three intact items at 219px / `overflow: visible` against two at 96px / `overflow: hidden`)
but changed no conclusion. Clipping does not need a worked probe path; it already has `LAYOUT:`.
Whether the *colour* and *width* cases do is still untested.

## One regression the patch may have caused

Eval 2, new version: the user asked **why**, and it **edited the file**. The old version reported and
left the file alone, explicitly reasoning that "the question was why, not a request to change it" —
which is what the skill's own *"Called in for one step, report rather than rewrite"* rule asks for.
Both versions carry that rule; only the new one broke it.

The likely cause is a phrase in the patch: *"let the measurement pick the edit"* presupposes an edit.
It should presuppose a finding. Worth rewording to something closer to *"let the measurement name the
cause"*, and re-running eval 2 to see whether the behaviour follows.
