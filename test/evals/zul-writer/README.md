# zul-writer behaviour evals

**These pages are deliberately broken. Do not copy from them.** They are test inputs, not
templates — the skill's own examples live in `skills/zul-writer/assets/`.

`evals.json` holds three prompts and fourteen assertions covering the DOM-probe channel
(`--probe` / `--dump-dom`), with the baseline pinned at commit `53f1050`, before the probe
existed. Each fixture carries one known defect, and the assertions check whether an agent given
the skill names the right cause:

| Fixture | Defect it carries | What the eval measures |
|---|---|---|
| `invoice-list.zul` | four `<label sclass="z-icon-*">` status icons that cannot draw, while the toolbar's `iconSclass` icons on the same page are fine | whether the cause is named correctly. This is not an invented case: in a six-run end-to-end evaluation three runs hit it and all three named the wrong cause, and one shipped the page |
| `team-settings.zul` | `.ts-item-name` is `width: 96px` with `overflow: hidden`, so two sidebar labels are cut | whether the reported CSS rule is named, rather than "the text is too long" |
| `customer-detail.zul` | bound to a ViewModel class that does not exist, so every field renders as dimmed placeholder text | whether the page is correctly judged **not** broken — an over-triggering check |

Current behaviour of the three, which the assertions describe and which should be re-checked
whenever a fixture is edited:

```
invoice-list     3 icon-not-rendered findings (4 broken carriers, deduped by class);
                 the <span> and the two iconSclass buttons stay silent
team-settings    2 clipped-text findings: 129px and 141px of text against a 96px box
customer-detail  no LAYOUT block and no WARNINGS block at all
```

All three pass all five validation layers, which is the point worth remembering:
`<label sclass="z-icon-check-circle"/>` is valid ZUL, so the validator reports the page clean and
only a render can see the defect.

## Why this lives here and not in the skill directory

Installing the skill symlinks or copies the whole of `skills/zul-writer/`, so anything under it
reaches every install. Pages with known defects do not belong there — least of all beside
`assets/`, which is the directory the skill tells the agent to take templates from.
