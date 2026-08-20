# preview-zul.py — compiled-output roots, bound-`src`, and a pipeline-shaped `main()`

Three changes, driven by two zkidea commits that landed after this script was written, plus a
readability pass on `main()`.

## 1. Pass the compiled-output roots (zkidea `da45ffc`, issue #67)

The script excludes class-output directories from `--classpath` and documents that as "the isolation
guarantee". The plugin reversed exactly that: the exclusion was redundant (the launcher's
`UiFactory` hook is the real boundary — it never resolves a ViewModel/Composer class name) and it
broke every page whose `<zscript>`, `use="…"` or custom EL function names a project class.

- `_filter_entries` → `_partition_classpath`, returning `(jars, output_roots, resource_roots)`.
  Files → jars, existing directories → output roots.
- Never pass test output. The plugin gets this from a production-only module enumeration; from a
  CLI we match the conventional names (`target/test-classes`, `build/classes/java/test`).
- Maven: `dependency:build-classpath` lists *dependencies only*, so `target/classes` is added
  explicitly.
- Gradle: new `OUT` row in the init script from `sourceSets.main.output.classesDirs` — the `test`
  source set is a separate object, so production-only is structural there.
- Order handed to the launcher: **jars → output roots → resource roots**, matching
  `ZulPreviewServerService.launcherClasspath`.
- `CACHE_SCHEMA` 1 → 2, because the cached entry shape gains a key.

→ verify: a `<zscript>` page naming a project class renders instead of dying; `target/test-classes`
never appears on the launcher's `--classpath`.

## 2. A bound `src` is not placeholdered (zkidea `9b81416`, issue #69)

`PlaceholderInjector` now leaves a non-literal bound `src` **unset** rather than writing its
expression text, so an `<include src="@load(vm.page)"/>` contributes *nothing* to the image. Every
other binding still renders as dimmed expression text. The agent must not "fix" that missing
section — it is the documented behaviour.

→ SKILL.md "What you cannot judge" gains a bullet; `references/preview-guidelines.md` gains the
reading. The script's module docstring also claims "the project's own classes never loaded", which
change 1 makes false.

→ verify: the sentence appears in both files, and in the generated marketplace copy.

## 3. `main()` reads as the pipeline

`main()` currently inlines argument validation, path derivation, the docroot guard, request-path
derivation, classpath assembly, the launcher/capture pair and both report shapes. Refactor it into
one method per pipeline step, named after the step.

The header pipeline is renumbered into **execution order** and the numbers are dropped from the
section banners: the classpath must be resolved *before* the jar is downloaded (an unusable
classpath has to exit 2 without touching the network — the CI smoke test pins that), so the old
numbering never matched the real order. With `main()` as the executable form of the pipeline there
is only one place left for the order to live.

→ verify: `main()` is a flat sequence of named calls; every exit code still comes out unchanged
(exercise 0 / 1 / 2 / 3).
