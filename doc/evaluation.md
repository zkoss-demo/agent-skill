# The zul-writer end-to-end evaluation

Six runs, 2026-08-25, in two batches. Design mockups from `zulwriter-showcase/ui-screenshots/` were
handed to a fresh agent, which ran the whole skill (mockup → page → controller → preview self-review);
the output was then verified independently.

**The deliverable was a list of process defects, not a page score.** Whether the pages looked good was
never the question; where the process stalls, where instructions are unclear, and where the tooling made
things harder, was.

This document keeps the parts worth reusing: the methodology, the findings and their final status, and
the known blind spots. The full 900-line working record has been condensed away.

---

## 1. Methodology worth reusing

### The verification method must itself be verified

AI judging AI shares blind spots. Two mechanisms, both non-negotiable:

- **A negative control, run before the real judging.** A deliberately mismatched mockup-and-render pair
  is handed to the judge. **If the judge passes it, every verdict from that round is void.** A check
  that cannot catch a wrong answer is not a check. (It passed: the pair was called `mismatch`, all six
  required No answers correct, with the missing sections named.)
- **A human spot-check on two of the runs.** If a human's reading disagrees with the blind verdict, the
  remaining blind verdicts are not trusted and all runs go to human review.

### Cross-model asymmetry, on purpose

The judge runs on a **different and stronger** model than the examinee, which stays on the model a real
user has. The asymmetry is deliberate: the skill is for real users, so the *test* conditions must be
realistic while the *checking* conditions need not be. This lowers, but does not remove, the chance of
both sides making the same mistake — which is why the negative control and human spot-check are not
skipped just because the models differ.

### The checklist asks about structure only

Every question is yes/no and answerable by pointing at the two images. No question touches colour,
letter-spacing, spacing or shadow aesthetics. The reason: **comparing two images is exactly what the
skill does at Step 5**, so the evaluation and the thing evaluated share a failure mode.

### One scenario per session

The examinee accumulates context. In the earlier scenario suite, B1 → B2 was the worst case: both turn
on "the preview showing no data is correct, do not fake it", so an agent walked through B1 gets B2 right
for the wrong reason — and B2's failure mode was the most destructive. Opening six conversations costs
six clicks and no examiner work in between.

### Sampling was capped by conditions, not by count

Four designs in batch one, chosen by *condition* rather than number: one 2× export, one non-dashboard
layout, two dashboards. The 2× export and the non-dashboard layout each had **exactly one** mockup
supporting them, so more runs could not increase coverage; the remaining five were all dashboards, and
running them repeats the same condition at the cost of a full generate-plus-render cycle each. Stated
openly as a sampling ceiling, not as full coverage.

### Findings need two runs; one run is an anecdote

Ordered by cross-run recurrence. A single occurrence is logged as "anecdote, keep watching" and may not
be written as a conclusion.

---

## 2. Runs and mechanical results

| Run | Mockup | Condition covered | Step 1 |
|---|---|---|---|
| R1 | Feedback Dashboard 2560×2108 | the only 2× export | pre-answered |
| R2 | Data Comparison Modal | the only non-dashboard layout | pre-answered |
| R3 | Bank Reconciliation | dashboard, dense tables | pre-answered |
| R4 | Task Master | dashboard, sidebar + cards | **deliberately unanswered** |
| R5 | Data Analytics Dashboard | dashboard, charts + tables | pre-answered |
| R6 | Test Case Management | three-column app shell | **deliberately unanswered** |

| | R1 | R2 | R3 | R4 | R5 | R6 |
|---|---|---|---|---|---|---|
| Validator layers | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| Preview exit code | 0 | 0 | 0 | 0 | 0 | 0 |
| `CONTROLLERS:` | executed | executed | executed | executed | executed | executed |
| Viewport vs mockup width | 1280 vs 2560 (correctly halved) | 1600 vs 1600 | 1600 vs 1600 | 1600 vs 1600 | 1600 vs 1600 | 1600 vs 1600 |
| Renders (cap was 3) | 4 | 3 | 3 | 3 | **10** | **5** |

Blind verdicts: R1–R5 **match**, R6 **mismatch** — a sidebar tree shipped expanded with six navigation
items the mockup does not have, and a truncated button label. Neither was caught by `LAYOUT:` or by R6's
own self-review, though R6 *had* spent a round on truncated text elsewhere on the same page.

Zero occurrences of the `--`-in-XML-comment error across all six runs, confirming the source fix
(`3d485f2`) worked. The judge disclosed its own two lenient calls rather than hiding them, and never
claimed to have seen something it had not.

---

## 3. The nine repeated findings, and where they ended up

| # | Finding | Runs | Final status |
|---|---|---|---|
| 1 | Step 1 has no fallback when nobody can answer | 6/6 | **Fixed** — per-question defaults + `detect-pattern.py` |
| 2 | "Model-driven" never defined data vs. layout text; the two-pass rule was MVVM-only | 4/4 | **Fixed** — all three sub-problems |
| 3 | The render cap does not match real pages | 3/6 | **Fixed twice** — budget rebound to edits, then the cap itself replaced ([D21/D22](decisions.md)) |
| 4a | `z-icon-*` on `<label>` never draws | 3/6 | **Fixed** — `icon-not-rendered` rule + the *Icons* reference section |
| 4b | Step 5's disclaimer absorbed that real defect | — | **Fixed** — the passage was rewritten, then deleted once launcher 1.0.3 made assets real |
| 5 | `--zk-version` was given six inconsistent values | 6/6 | **Fixed** — the tool now echoes how it read the input |
| 6 | Step 5 self-review misses real visual defects | 2/6 | **Fixed** — `clipped-text` + icons + the `STATE:` enumeration |
| 7 | The ZK 10 theme takes over the mesh header, undocumented | 2/6 | **Open** — handed to the knowledge track |
| 8 | Launcher download 404'd on first preview | 2/6 | **Fixed** — version + SHA-256 pinned; asset verified live |
| 9 | The references drive the agent to read `zul.xsd` instead | 2/6 | **Open** — handed to the knowledge track |

Seven of nine closed. See [knowledge-roadmap.md](knowledge-roadmap.md) for 7 and 9.

Three findings are worth remembering for their *shape*, not their fix:

- **Finding 4b is the sharpest lesson in the whole exercise.** Step 5 carried a disclaimer saying
  missing images and fonts "404 in the preview but load fine on a real server". R2 **quoted that
  sentence to classify a genuine, one-word markup bug as an unfixable preview artifact**. A disclaimer
  that absorbs real defects is worse than no disclaimer. Its real sin was misattribution plus
  over-breadth: it blamed a guessed docroot when files *inside* the docroot failed too, and it swept two
  real defects (a missing jar, a wrong icon carrier) into "unfixable" with one phrase.
- **Finding 5 will be misread as unfixed.** `SKILL.md` still only says "pass the ZK version detected in
  Step 1", so grepping the instructions for the proposal's wording finds nothing. **The fix landed in
  the tool's output, not in the documentation** — which is the intended shape (see
  [product-rationale.md](product-rationale.md) §2).
- **Finding 3's most valuable evidence was the behaviour that worked.** One run met a defect that
  reported an identical value on every render, refused to ship a speculative fix it could not verify,
  and reported instead — under the pressure of having already spent its rounds. That half of the rule is
  effective and was kept.

---

## 4. Anecdotes still on the watch list

Eleven single-occurrence observations were logged. Three were later promoted to mechanically detectable
checks (`<combobox selectedIndex="0">` on a model-less component; `@Wire` type mismatch;
`setModel()` beside literal rows — which was also the missing half of finding 2). The eight still on
the list, none of which has an owner:

- Excess flexible height painted flat grey — **worth chasing, because the workaround changes how markup
  is written** (now attributed to ZK; see [zk-measured-behaviour.md](zk-measured-behaviour.md) §8)
- `hflex="min"` measuring 13–128px short, growing with item count (ibid. §9)
- `mvn -o compile` refusing to rebuild after a real source edit (ibid. §18)
- A constant-value `escapes-parent` finding (since judged an artefact; ibid. §10)
- ZK Charts Java API in a Composer derived by analogy from doc examples, not from
  `charts-guidelines.md`
- Three attempts to declare a default combobox selection before one worked
- No ZK layout solution for pinning a sidebar button to the bottom of a `<west>` region; fell back to a
  CSS flex column
- The extraction stage using two renders where the skill specifies one

---

## 5. Blind spots in the evaluation method itself

Both were found on pages the checklist had already passed.

1. **No question covers arrangement *within* a section.** R4's cards put description text and title on
   one line where the mockup stacks them. The questions ask which sections exist and in what order, plus
   one about truncation. A page with this defect can pass all 13 — R4 did.
2. **No question can catch a broken icon.** The judge was told to ignore "icon style", so it correctly
   filed R2's and R5's empty boxes under the truncation question as "that is an icon, not text" and
   answered Yes. **Icon *styling* is legitimately out of scope; an icon *disappearing* is a real
   defect**, and the checklist has nowhere to put it.

**Q14 and Q15 must be added before this checklist is reused.** Neither has been. Reusing it as-is
inherits both known blind spots.

---

## 6. Why it stopped here, and why it could not converge

The plan's own rule: keep adding batches until repeated findings stop increasing.

| | after batch 1 (4 runs) | after batch 2 (6 runs) |
|---|---|---|
| Repeated findings | 5 | **9** |
| Anecdotes | 10 | 11 |

Repeated findings were still increasing and single-occurrence items still outnumbered them. **The rule
said continue; the material said no.** All three remaining mockups are disqualified:

- `AppTracker.png` — the finished page and its composer are in the working directory.
- `Application Review.png` — the page and composer are unstaged deletions, so `git status` prints both
  filenames.
- `enterprise kanban board.png` — **the skill itself ships `assets/kanban-board.zul` and
  `assets/KanbanViewModel.java`**, and Step 2 tells the agent to look in `assets/`.

So the honest statement is: **this evaluation did not converge, and cannot on this sample.** Continuing
requires new mockups with no counterpart anywhere in this repo. That is a deliberate decision to make,
not a gap to gloss over — and the nine repeated findings stand regardless, each anchored in two or more
independent runs.

Four factual corrections to the plan were identified and never applied; the plan file has since been
removed, so they are recorded here instead: `enterprise kanban board.png` was listed as usable material
and is not; *every* candidate mockup has a committed-then-deleted counterpart in git history, not only
the two named; the validator has **five** layers, not four; and **the contract suite cannot be run with
an arbitrary interpreter** — `test/run-preview-tests.py` spawns `sys.executable`, so a Python without
`playwright` reports most checks as failures and **a healthy suite looks like a broken contract**. That
last one is the most expensive of the four.

---

## 7. The probe-trigger iteration (a smaller, later evaluation)

Three prompts, each run twice — the current skill against the skill before `--probe` existed. Six
subagents, each in its own sandbox containing only the skill and three fixtures: no working documents,
so nothing could be answered by grepping the repo for the answer. The sandbox copies of
`preview-zul.py` log their argv, so "did it probe" is read off a file rather than off the agent's own
account of itself.

| Prompt | | renders | probed | edited | tokens | tool calls | wall |
|---|---|---|---|---|---|---|---|
| 1 blank icon | new | 3 | **yes** | yes | 71,875 | 16 | 225s |
| | old | 4 | no | yes | 97,115 | 32 | 378s |
| 2 clipped sidebar | new | 3 | **yes** | yes | 63,126 | 11 | 179s |
| | old | 2 | no | no | 63,000 | 10 | 140s |
| 3 bound values (anti-trigger) | new | 1 | **no** | no | 59,594 | 9 | 136s |
| | old | 1 | no | no | 65,362 | 13 | 149s |

**On these three prompts the feature changed how the answer was reached, not whether it was right.**
Both versions diagnosed all three correctly. The gain was cost: on the icon case, half the tool calls, a
quarter fewer tokens, 40% less wall time.

What was genuinely settled:

- **No over-triggering.** Prompt 3 was the risk — a new tool the model wants to use, on a page where the
  correct answer is "nothing is wrong". The new version spent one render, no probe, and made no edit.
- **The probe is reached where the prose says it should be**, with the selector the `SKILL.md` example
  gives, on the first try.
- **A prediction was wrong, and usefully so.** The assessment expected the clipped-sidebar case to
  strand the agent, since only the icon case has a worked end-to-end path. The opposite happened:
  `LAYOUT:` already names the element, the needed width and the actual box, and the *old* version reached
  the correct cause from those numbers with no probe at all. Clipping does not need a worked probe path.
  Whether the colour and width cases do is still untested.

Two things it did **not** settle, both still open:

- **Prompt 1 did part of the diagnostic work.** It stated that other icons on the same page came out
  fine — handing over the evidence that falsifies "the webfont 404'd". In the real six-run evaluation the
  agent was reviewing its own page and had to notice that contrast unprompted; **three of three runs that
  met this defect named the wrong cause.** One old-skill run getting it right *with the contrast supplied*
  is not evidence against that 0/3. So this iteration measured *"once you know something is odd, how
  cheaply do you reach the cause"* and not *"do you notice something is odd at all"* — which is where the
  documented failures actually happened. **A second iteration should drop the contrast from the prompt.**
- **A possible regression the patch introduced.** In prompt 2 the user asked *why*, and the new version
  **edited the file**; the old version reported and left it alone, explicitly reasoning that the question
  was why, not a request to change it — which is what the skill's own *"called in for one step, report
  rather than rewrite"* rule asks for. Both versions carry that rule; only the new one broke it. Likely
  cause is a phrase in the patch: *"let the measurement pick the edit"* presupposes an edit where it
  should presuppose a finding. Suggested reword: *"let the measurement name the cause"*, then re-run
  prompt 2 to see whether the behaviour follows.

Two soft spots in the prose were left in place deliberately during this iteration, so a behaviour change
could be attributed to the one thing that was patched. The remaining one: the probe section is gated
behind the agent noticing it *cannot* explain what it sees, which is the self-knowledge an LLM is worst
at — the default on seeing a blank box is to produce a fluent cause, not to notice the cause is a guess.
The one hard counter that works is a *specific* instruction attached to a *specific* symptom, and it
covers icons only.
