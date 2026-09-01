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

- **Recall**: fires on the recorded defect form, naming the cause and three ways out —
  `selectedIndex="0" will throw at render time. <combobox> declares no <comboitem> and no model, so
  index 0 has nothing to point at.`
- **Precision**: run over all 558 `zkbooks` files. Layer 6 was reached on 555 (3 aborted at an earlier
  layer) and **fired on 0**. The corpus contains 8 files using `selectedIndex`, only one of them a
  literal value; the rest are `@bind`/`@load` expressions, and the rule stayed silent on all of them as
  designed.

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
