# Did the pre-write lookup and the last two checks actually work?

Measured 2026-09-01, against `--describe`, Layer 6 and Layer 7 as committed in `db3d001`.

**What could not be measured, and why.** [knowledge-roadmap.md §6](knowledge-roadmap.md) names the
intended measure: **renders per page**, re-running the six-design suite and comparing against 4, 3, 3, 3,
10, 5. That cannot be run. Every one of those six mockups now has a finished page and controller in this
repository, so a re-run measures recall of existing work, not generation
([dev-environment.md §4](dev-environment.md)), and the three unused mockups are disqualified for the same
reason ([evaluation.md §6](evaluation.md)).

So this is a **different and narrower measurement**: not *does the agent use the tool*, but **does the
tool give right answers to the questions the evaluation recorded it being asked.** A tool that answers
wrongly cannot help however often it is called, so this is the prerequisite question — and unlike
renders-per-page it needs no new material.

Corpora used, both real rather than synthetic:

- this repository's own must-pass ZUL (23 non-quarantined files, 6 quarantined)
- `DOC/zkbooks` — **558 `.zul` files and 192 resolvable zul/controller pairs**, written by ZK's own
  documentation team. Caveat from [knowledge-roadmap.md §4](knowledge-roadmap.md): that checkout is on
  branch `11.0.0` while the schema targets ZK 10, so genuine ZK 11 additions appear here as wrong
  answers. Findings are therefore reported with usage counts and triaged, never reduced to a pass/fail.

---

## 1. `--describe` — recall on the recorded failures

The six selection failures in [knowledge-roadmap.md §1](knowledge-roadmap.md) are real questions with
known-correct answers. Each was asked of the lookup as the agent would have asked it before writing.

| The recorded failure | Asked as | Answer | |
|---|---|---|---|
| `<charts sclass=…>` | `--describe charts --attr sclass` | NOT accepted, offers `zclass`, `className` | **hit** |
| `<togglebutton>` in ZK 10 | `--describe togglebutton` | NOT FOUND, offers `toolbarbutton` | **hit** |
| `<comboitem selected="true">` | `--describe comboitem --attr selected` | NOT accepted; *"valid on: listgroup, listgroupfoot, listitem, navitem, orgitem, radio, tab, treeitem"* | **hit** |
| `@Wire Label` on an `<a>` | Layer 7, not a schema question | caught with the declaration line | **hit (item B)** |
| `<label sclass="z-icon-x">` | `--describe label --attr sclass` | accepted — and correctly so | **miss** |
| `setModel()` beside literal rows | not a schema question | already mechanised in `preview-zul.py` (D18) | n/a |

**The combobox row is the most interesting result in the whole measurement.** The reverse "valid on"
list names `treeitem` — which is exactly the neighbour the zk-doc retriever returns first for that query
([knowledge-roadmap.md §3](knowledge-roadmap.md)), and exactly the wrong spelling one run tried first.
The lookup does not merely say no; it explains *why the agent's memory said yes*. That is the shape a
selection failure needs, and no prose or example in the corpus supplies it.

**The icon row is a real limit, not an oversight.** `sclass` genuinely is accepted on `<label>`; the
schema has no way to know `z-icon-*` will not draw there. This class of defect belongs to a check, and
already has one.

Cost: **0.23 s per lookup** (5 calls in 1.129 s wall). Whatever a render costs, this is not in the same
unit.

## 2. `--describe` — precision, which is the number that decides whether to trust it

Ground truth: every `(element, attribute)` pair actually used in asserted-correct ZUL. Any "NOT
accepted" or "NOT FOUND" over such a corpus is a **wrong answer the agent would act on** — the failure
mode [evaluation.md §3](evaluation.md) punished hardest.

| Corpus | pairs | elements not found | attributes rejected |
|---|---|---|---|
| this repo, non-quarantined (23 files) | 101 | 0 | **0** |
| this repo, quarantined (6 files) | 78 | 0 | 2 |
| `zkbooks` (558 files) | 967 | 17 of 169 (10.1%) | **70 (7.24%)** |

Weighted by how many files use the form, the 70 rejections cover **179 file-uses**, and one form
accounts for 48 of them: **`<attribute name="…">`, reported NOT accepted, exit 1.** That is canonical
ZUL, documented, and used in 48 of ZK's own example files.

### The cause is the lookup, not the schema

`attributeType` **does** declare `name` and `trim` — inside `xs:simpleContent`, which
`collect_type_attrs()` never traverses (it handles `xs:complexContent` only). Text-bearing elements
therefore resolve to an empty attribute set. A six-line patch adding `simpleContent` to that branch was
tested on a scratch copy:

| | rejected pairs | file-weighted |
|---|---|---|
| as committed | 70 | 179 |
| with `simpleContent` traversed | 68 | **129 (−28%)** |

`<attribute name>` and `<zscript deferred>` both become "accepted". **`build_attribute_map()` is shared
with Layer 3**, so this is also the root cause of a quarantine entry that
[knowledge-roadmap.md §7](knowledge-roadmap.md) listed as unresolved: `test/valid/zk-5793.zul`, filed
under "Layer 3 attribute-placement false-positives", uses `<attribute name="onUpload">`.

**Fixed, along with the two lookup bugs below — see §6 for the measured result.**

### Triage of the 68 that remain

| Class | rows | file-uses | Where the fix belongs |
|---|---|---|---|
| Schema declares `xs:anyAttribute` and the lookup ignores it (`custom-attributes`, `variables`) | 17 | 32 | **the lookup** — report "accepts arbitrary attribute names" |
| Pass-through parameter elements (`<apply>`, `<include>`) | 17 | 26 | **the lookup** — a small allow-list |
| Add-on or post-ZK-10 components (`chart`, `ckeditor`, `gmaps`, `rating`, `cropper`, responsive `grid`) | 19 | 47 | out of scope — the documented version trap |
| Genuine ZK 10 schema gaps (`label pre`, `panel framable`, `groupbox contentSclass`, `include enclosingTag`, event attributes such as `tab onSelect`) | 15 | 24 | the schema — [§7](knowledge-roadmap.md) whack-a-mole |

The second row is confirmed against ZK's own documentation, not assumed:
`<include type="outerPageLiteralValue" src="inner.zul"/>` is the documented way to pass an argument to
an included page, and `<?component …?>` documents `[prop1="value1"]` defaults for a named `<apply>`.
Arbitrary attribute names on those two elements are the feature.

**So half the residual wrong answers are fixable in the lookup and half are not.** The 17 elements
reported NOT FOUND are, on inspection, ZK 11 components (`avatar`, `badge`, `chip`, `breadcrumb`,
`carousel`, `confirmpopup`, `daterangebox`) and demo-local classes (`simplelabel`, `BandboxSelect`) —
the version trap behaving exactly as predicted, not a defect at the ZK 10 target.

## 3. Layer 6 — runtime semantics

- **Recall**: fires on the recorded defect form, naming the cause and the way out —
  `selectedIndex="0" will throw at render time. <combobox> applies the index before its items are
  attached and before any model is set, so neither literal items nor model="..." makes it safe --
  set value="..." on a readonly combobox, or select from the controller once the model is in place.`
- **Precision**: run over all 558 `zkbooks` files. Layer 6 was reached on 555 (3 aborted at an earlier
  layer) and **fired on 0**. The corpus contains 8 files using `selectedIndex`, only one of them a
  literal value; the rest are `@bind`/`@load` expressions, and the rule stayed silent on all of them as
  designed.
- **Precision holds after the rule was tightened.** The 2026-09-01 rewrite made the rule fire
  unconditionally on four components (see [zk-measured-behaviour.md §21b](zk-measured-behaviour.md)),
  which is exactly the change that could have cost precision. Re-measured on the same corpus: the
  rule cannot fire on a file with no `selectedIndex`, so only those 8 files were re-run, and Layer 6
  still fires on **0**. The one literal value, `<cardlayout selectedIndex="1">` with two cards, is
  cleared by the card count — the one component whose children really are attached first.

Frequency in real code cannot be measured this way — documentation examples are written correct. Layer
6's case rests on catching the recorded defect while never accusing 555 real files, and both hold.

## 4. Layer 7 — controller cross-check, the only rule that can accuse correct code

Paired each `.zul` with the controller its own markup names (`apply=` / `viewModel=`), resolved the FQCN
against every `src/main/java` root in the corpus.

| Corpus | pairs | `@Wire` fields | findings |
|---|---|---|---|
| this repository | 5 controllers | 30 | 0 |
| `zkbooks` | 192 | 140 | **1 (2 fields)** |

**The single finding is a false positive, and it has a clean signature.**
`ArticleContentViewCtrl.java` is applied to `articleContent.zul`; the two flagged fields
(`titleTxb`, `contentTxb`, lines 108 and 110) are declared inside a **nested class**,
`public class ArticleEditor extends Window`, which is its own component with its own markup. Their ids
are not expected in `articleContent.zul` at all.

- The **type-mismatch half** of the rule produced **zero** findings across 170 real `@Wire` fields.
- The **unknown-id half** produced 2 false accusations out of 170 fields (1.2%).

The repository-internal sweep could not have found this: none of its five controllers declares a nested
component class. This is the value of measuring against outside code.

**Fixed (D26).** Both halves of the check now skip any `@Wire` field not declared in the outermost
class body — a nested class carrying `@Wire` is its own component with its own tree, so neither half can
say anything true about it. Nesting depth is counted on a copy of the source with comments *and* string
literals blanked in place, because a `{` inside `"a { brace"` would otherwise read as a nested class and
silence every field after it. Re-measured the same way: **0 findings over zkbooks' 192 pairs and 140
`@Wire` fields, and 0 over this repository's 16 pairs and 64 fields.** Layer 7 is opt-in, so the default
output is untouched — 39 of 39 corpus files byte-identical.

Not attempted, and worth knowing before trusting the render instead: **the NPE this rule predicts is
mostly invisible to a preview.** Measured with two probes that differ only in where the null field is
used:

| Where the field is used | default render | `--run-controllers` | Layer 7 |
|---|---|---|---|
| in `doAfterCompose` | `STATUS: ok`, exit 0 — nothing | `CONTROLLERS: failed → isolated` + a warning naming the field | caught |
| only in an event handler | `STATUS: ok` — nothing | **`CONTROLLERS: executed`, `STATUS: ok`, exit 0, no warning** | caught |

The second row is the point: the preview never clicks anything, so that code path never runs. The page
renders perfectly and throws on the user's first click. Controller execution is also opt-in
(`--run-controllers` defaults off), and when a controller does throw the run still reports `STATUS: ok`
with exit 0 — a warning, not a failure.

Where the render *does* fire, the message is better than expected — Java's helpful NullPointerException
names the field: `Cannot invoke "org.zkoss.zul.Label.setValue(String)" because "this.totalsLabel" is
null`. What it never says is *why* the field is null, and four different causes produce that identical
message: no component declares the id, the composer is applied somewhere else, the id is in another ID
space, or the ZUL's id is misspelled. Layer 7 distinguishes the first and names the file and line.

## 5. What this does and does not establish

Established: the lookup answers 4 of 6 recorded selection failures correctly and cheaply; it is clean on
this repository's own corpus; and it carries one high-frequency wrong answer plus a triaged tail. Layer
6 catches its defect and accuses nothing. Layer 7's type check is clean; its id check has one known
false-positive shape.

**Not established, and not measurable on this material: whether an agent reaches for any of it.** That
is what renders-per-page would have measured. A right answer nobody asks for changes nothing, and the
evaluation's plainest lesson was that a capability without prose goes unused — the instruction is in
Step 2 guideline 3, and its uptake is untested.

---

## 6. What the fix changed (D25, measured the same way)

Three changes landed: `xs:simpleContent` is traversed; an element whose own type declares
`xs:anyAttribute` is reported as taking arbitrary names instead of being judged; and `<apply>` /
`<include>` are named as pass-through elements, which no part of the XSD can express.

| | wrong answers (distinct pairs) | file-weighted |
|---|---|---|
| before | 70 of 967 (7.24%) | 179 |
| after | **33 of 967 (3.41%)** | **69 (−61%)** |

Nothing in the remaining 33 is a defect in the lookup. All of them are corpus-version or schema-coverage
facts, and they split into two groups worth naming:

- **19 rows / 47 file-uses — add-on or post-ZK-10 components**: `chart`, `ckeditor`, `gmaps`,
  `gpolyline`, `gpolygon`, `cropper`, `rating`, `rangeslider`, responsive `grid`/`column`. Out of scope
  at a ZK 10 target.
- **14 rows / 22 file-uses — genuine ZK 10 schema gaps**, and they have a shape: **five are event
  attributes** (`tree onAfterRender`, `tab onSelect`, `group onOpen`, `div onUpload`,
  `div onAnyServerEvent`) and **two are the `class` alias for `sclass`**. The rest are
  `label pre`, `panel framable`, `groupbox contentSclass`, `grid fixedLayout`, `include enclosingTag`
  and two shadow-element attributes. Those two families are systematic enough to fix as families
  rather than one at a time — the argument in [knowledge-roadmap.md §7](knowledge-roadmap.md).

On this repository's own corpus the lookup is now clean in both directions: **0 of 42 pairs in
`test/valid`, 0 elements not found.**

Side effects, both intended and both verified:

- **Quarantine 6 → 5.** `test/valid/zk-5793.zul` was fixed rather than quarantined.
- **Default output changed on exactly one file.** Diffed every corpus file against the committed
  validator: **35 of 36 byte-identical**, and the one change is that file's Layer 3 going
  `✗ FAIL → ✓ PASS`. Nothing else moved.

---

Reproduce with the three scripts in `test/measure/`; each is self-contained and takes a corpus root as
its only argument, so any ZUL tree can be swept:

```
uv run test/measure/describe-precision.py      <corpus-root>   # ~40 s over 558 files
python3 test/measure/layer6-false-positives.py <corpus-root>   # ~6 min over 558 files
uv run test/measure/layer7-false-positives.py  <corpus-root>   # ~2 min over 192 pairs
```

They are measurement tools, not CI checks: their output needs triage against the corpus's ZK version, so
none of them has a meaningful pass/fail exit code and none is wired into `run-regression.py`.

---

## 7. The clean-room pilot (pilot-01) — what generation outside this repository found

The six-run evaluation happened *inside* this repository, where every mockup already had its committed
`.zul` a few directories away. That measures recall as much as generation. `test/cleanroom/make-sandbox.sh`
removes the answer: a Maven webapp outside the repo holding the plumbing, one mockup and a **copy** of the
skill, and nothing else. The global skill symlink was moved aside for the duration, because resolving it
walks straight back to the showcase.

**Input:** *Data Analytics Dashboard* — deliberately the same mockup as evaluation run **R5**, which is
both the only directly comparable pair available and R5's worst-in-six result.

| | R5 (in repo, answer present, cap 3) | pilot-01 (clean room, no answer) |
|---|---|---|
| Renders | **10** | **7** — of which only **2** were fix rounds |
| Validator | 5/5 | **7/7**, Layer 7 included |
| Lookups before writing | not recorded | 12 `--describe`, 9 `javap`, 2 jar greps |

**This does not isolate the clean-room effect.** The skill changed substantially between R5 and now, and
one run cannot separate the two causes. What the pilot does establish is that the material is not used up:
the sandbox makes 8 of the 9 mockups usable again, which was the premise
[evaluation.md §6](evaluation.md) concluded against.

### Four defects the in-repo runs never surfaced

1. **`icon-not-rendered` had a false negative, and it was the rule's own core case.** Five icons rendered
   as empty boxes under a completely clean `LAYOUT:` block. The check read only the resolved
   `font-family`, which was correct; the *weight* selected a face without the glyph. Reproduced by
   deleting one CSS line from the finished page — 0 findings before the fix, 4 after, 0 on the page with
   the line restored. → [zk-measured-behaviour.md §20](zk-measured-behaviour.md)

   The prose was worse than the rule: `ui-to-component-mapping.md` told the reader to `--probe` and treat
   a correct icon `font-family` as exoneration, which is exactly the wrong conclusion here.

2. **Step 4 and the chart carve-out contradicted each other.** *"no `setModel()`, no getter backing a
   bound `model`, not yet"* is stated flatly, with the chart exception 160 lines earlier in Step 2. A
   reader following Step 4 literally strips a chart's data back out and gets an empty chart that reports
   nothing.

3. **`references/charts-guidelines.md` had no MVVM path at all** — 25 lines, zero occurrences of `MVVM`,
   `model`, `@load` or `ViewModel`, and its only data advice (`Series`) is reachable solely from a
   Composer. The skill treats MVVM as a first-class pattern everywhere else.

4. **`hflex="min"` is unsafe beside a `<style>` block that enlarges type**, which is the combination
   Step 2's own guideline pushes you into. ZK measures `min` before the page CSS applies, writes the small
   number as an inline width, and `.z-hlayout` clips it. Six `clipped-text` findings on the first render,
   one of them a navigation link that vanished entirely.

### Two things the pilot got wrong, which are findings of their own

- **It reported a contradiction that is not one.** Step 5 says the PNG belongs in the working directory
  and to pass `--out` "only when the user names a destination"; the brief named `out/`. The rule resolves
  cleanly as written.
- **It misread a capture artifact as page state.** The floating action button is `position: fixed`, so a
  `--full-page` capture paints it at the *viewport* bottom — measured at y=798 of a 1277-tall PNG. The
  pilot instead credited an unrelated edit with "lifting it clear" of a caption and carried that reading
  through two renders. This is the one place the visual self-review must be overruled, and nothing in the
  image distinguishes it from a real defect. → [zk-measured-behaviour.md §17b](zk-measured-behaviour.md)

### Reproducing

```bash
./test/cleanroom/make-sandbox.sh "Data Analytics Dashboard" pilot-02
mv ~/.claude/skills/zul-writer ~/.claude/skills/zul-writer.off      # restore afterwards
cd ~/Documents/workspace/zul-writer-cleanroom/pilot-02
claude --bg --dangerously-skip-permissions "Read BRIEF.md in this directory and follow it."
```

The sandbox script copies the skill at build time and does not track it afterwards. Pilot-01's copy was
three commits stale when the pilot was about to start, which would have measured a skill nobody ships —
check it before every run until the script stamps the version itself.
