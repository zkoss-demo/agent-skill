# Plan: pre-write schema lookup + the last two Tier-1 checks

Both items come from [doc/knowledge-roadmap.md](../doc/knowledge-roadmap.md) §5, items 1 and 2 — the two
highest-leverage entries because they move knowledge *before* the write instead of detecting a defect
after it, and each costs a round today.

Governing constraint from the rest of the project: **the default output of `validate-zul.py` must stay
byte-identical.** Layer count and text are a contract the corpus job and the skill instructions both
depend on. Every new behaviour is therefore opt-in.

---

## Item A — turn the bundled `zul.xsd` into a pre-write lookup

The skill ships a 183 KB schema and only uses it as a checker, which answers *after* the mistake at the
cost of a round. Two of six evaluation runs invented "read the schema first" on their own and both said
it saved them; the skill never suggests it.

Shape: a `--describe` mode on `validate-zul.py` rather than a new script. It already owns the XSD and
already has `build_attribute_map()`, so a separate script means either duplicating ~120 lines of schema
parsing or importing across a hyphenated filename. One tool, two roles.

1. **`--describe <component>`** prints whether the component exists at the target version and what
   attributes it accepts.
   → verify: `--describe charts` lists `className` and `zclass` and **not** `sclass`;
   `--describe togglebutton` reports it does not exist.
2. **`files` becomes optional only in describe mode.**
   → verify: a bare invocation with no arguments still exits 2 with a usage error, exactly as today.
3. **No usage ping in describe mode**, for D19's reason — a lookup is not a skill run, and a third
   emitter per run breaks the trend line at the version boundary.
   → verify: `TRACK_URL` pointed at a local listener receives nothing for `--describe`.
4. **Version-aware**, reusing the existing tables rather than inventing a second source of truth:
   `REMOVED_COMPONENTS`, `REMOVED_ATTRIBUTES`, `NEW_IN_ZK10_ATTRIBUTES`.
   → verify: `--describe fragment --zk-version 9` says available; `--zk-version 10` says removed.
5. **`SKILL.md` Step 2 gains the instruction to use it.** Without the prose the flag goes unused — the
   evaluation's plainest lesson.
   → verify: the wording names the trigger ("before using a component or attribute you have not used
   before"), not just the command.

## Item B — the last two Tier-1 mechanical checks

6. **`selectedIndex` on a component that has nothing to index.** Passes all five layers today and dies
   at render with `Out of bound: 0 while size=0`. Deterministic in the ZUL alone: flag
   `selectedIndex="N"` when the component has no `model=` **and** fewer than N+1 literal item children.
   Fires in the existing Layer 3.
   → verify: `<combobox selectedIndex="0"/>` fails; one `<comboitem>` present passes; `model=` present
   passes.
7. **`@Wire` field type vs. component type.** Compiles, validates, renders, then throws
   `ClassCastException` at runtime only when the field is used — invisible to every existing layer and
   to the render. Needs the Java, so it is a new **Layer 6**, running *only* when `--controller` is
   passed, keeping default output unchanged.
   → verify: `@Wire Label x;` against `<a id="x"/>` is flagged; `@Wire A x;` is not; `@Wire Component x;`
   is not; an unresolvable case is silent.
8. **Fixtures and tests.**
   → verify: `test/run-regression.py` reports 0 drift, and a new `test/run-schema-query-tests.py` passes.

---

## Review — all eight steps done

| Step | Outcome |
|---|---|
| 1 `--describe` | `--describe charts --attr sclass` → *NOT accepted*, offering `zclass`/`className`; `--describe togglebutton` → *NOT FOUND*, offering `toolbarbutton` |
| 2 optional file arg | a bare invocation still exits **2** with `the following arguments are required: files` |
| 3 no ping | describe returns before `track_usage_async` is ever reached |
| 4 version-aware | `fragment --zk-version 9` → *existed in ZK 9, removed in ZK 10*, exit 0; `--zk-version 10` → *REMOVED*, exit 1 |
| 5 Step 2 prose | guideline 3 added, plus a routing-table row and the `zk-doc` server-name fix |
| 6 Layer 6 | fires on the empty combobox and on an index past the last item; silent for one literal item, a bound index, `-1`, and a present `model` |
| 7 Layer 7 | catches `@Wire A` on a `<label>` in a real composer, naming line 39 — the declaration, not the annotation |
| 8 tests | `run-schema-query-tests.py` **25/25**; `run-regression.py` 33 files 0 drift; `run-pattern-tests.py` 7/7 |

**Two defects found and fixed during implementation, both by testing rather than by review:**

1. **`--describe` gave a confidently wrong answer for a removed component.** `<fragment>` is absent
   from the bundled 10.x schema, so the first version reported "not a ZUL component at this version"
   — flatly wrong for a ZK 9 target, where it is valid. Absence and removal look identical in this
   file and mean opposite things, so removal is now checked *first*. This is precisely the failure
   mode the project's own evaluation punished hardest: a wrong answer is worse than no answer.
2. **Layer 7 reported the wrong line number.** Comments were being stripped, which shifted every
   offset after the first comment — a real field at line 39 was reported as line 27. Comments are now
   blanked in place, preserving offsets, and the report anchors on the *type token* rather than on
   `@Wire`, because the type is what has to change.

**False-positive check, since that is the whole risk of Layer 7:** run against every controller in the
repository that uses `@Wire` — five files, 30 fields — **zero findings**. Then one field's type was
flipped in a real composer and the rule caught it with the correct diagnosis and fix.

**Default output shape:** diffed against the committed validator over four files. Exit codes identical;
the only change anywhere is the single new `Layer 6` line.

### Silence rules for item 7 — decided before writing, not after

The rule reports only what it can establish. It stays silent when the field type is a known base class
(`Component`, `HtmlBasedComponent`, `XulElement`, `LabelElement`, `LabelImageElement`, `InputElement`,
…), when the type is generic or a collection, when the id is not in the ZUL (it may be built at
runtime), when the `@Wire` carries a selector that is not a plain `#id`, or when either side does not
resolve to a known component. Under-reporting is the safe direction for a list the agent is told to
trust — the same principle the `escapes-parent` rule already follows.
