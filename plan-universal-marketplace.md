# Universal AI Plugin Marketplace — Implementation Plan

> JSON formats verified against official documentation (March 2026).

## Background

The `agent-skill` repo currently has one skill ([zul-writer](file:///Users/hawk/Documents/workspace/DOC/agent-skill/skills/zul-writer)) wired **only for Claude Code** — skills symlinked into `.agent/skills/` or `~/.claude/skills/`. Goal: make the same skill work across Claude Code, Gemini CLI, and GitHub Copilot/Cursor.

---

## Key Findings From Official Docs

| Concern | Finding |
|---|---|
| `SKILL.md` frontmatter | Only `name` + `description` are truly required. Optional fields: `license`, `compatibility`, `metadata`, `allowed-tools`. **No `context` field in the official spec** — that was a Claude-specific extension. Source: [agentskills.io/specification](https://agentskills.io/specification) |
| Gemini CLI extensions | `gemini-extension.json` does **not** have a `skills` array. Gemini loads skills from a `skills/` subdirectory inside the extension folder via a `SKILL.md` file (same format). The primary manifest supports `contextFileName`, `excludeTools`, `settings`, `themes`. Source: [geminicli.com/docs/extensions](https://geminicli.com/docs/extensions/writing-extensions) |
| Gemini CLI skill loading | Gemini CLI reads skills from `skills/<skill-name>/SKILL.md` inside the extension directory — exactly the same `SKILL.md` spec as Claude Code. |
| GitHub Copilot / Cursor skills | Stored in `.github/skills/<skill-name>/SKILL.md`. Same `SKILL.md` format. Source: VS Code docs |

---

## Proposed Final Directory Structure

```
agent-skill/
├── marketplace.json                   ← [NEW] Human/machine-readable index of all skills
│
├── gemini-extension.json              ← [NEW] Gemini CLI extension manifest (root-level)
├── GEMINI.md                          ← [NEW] Gemini CLI equivalent of CLAUDE.md
│
├── skills/                            ← [NEW] Canonical skill location (moved from root)
│   └── zul-writer/                   ← [MOVED from ./zul-writer] real files live here
│       ├── SKILL.md
│       ├── assets/
│       ├── references/
│       └── scripts/
│
├── .github/
│   └── skills/                        ← [NEW] GitHub Copilot / Cursor
│       └── zul-writer/               ← symlink (macOS/Linux) or copy (Windows)
│
├── .claude/                           ← existing
│   └── settings.json
│
├── .agent/                            ← existing (Claude Code project-level)
│   └── skills/
│       └── zul-writer                 ← symlink → ../../skills/zul-writer
│
├── install-skill.sh                   ← [MODIFY] multi-tool setup
├── link-skill.sh                      ← [MODIFY] multi-tool setup
├── README.md                          ← [MODIFY] marketplace-level docs
└── CLAUDE.md                          ← [MODIFY] update structure section
```

> **Why move `zul-writer/` into `skills/`?**
> Symlinks to the root-level `zul-writer/` would work on macOS/Linux but not reliably on Windows (requires Developer Mode or admin rights). Making `skills/zul-writer/` the single canonical location keeps the real files in one place; install scripts create symlinks or copies from there as needed per platform.

---

## Detailed File Specifications

---

### 1. `SKILL.md` Frontmatter (Updated to Official Spec)

Per [agentskills.io/specification](https://agentskills.io/specification), the official fields are:

```yaml
---
name: zul-writer              # required: lowercase, hyphens, 1-64 chars, matches dir name
description: >                # required: 1-1024 chars, what it does + trigger keywords
  Generates ZK Framework ZUL pages via a structured workflow.
  Supports MVC and MVVM patterns, ZK 9/10, and screenshot-to-ZUL conversion.
  Use when the user asks to create a ZUL page, ZK UI, or convert a screenshot to ZUL.
license: MIT                  # optional
compatibility: >              # optional: environment requirements
  Designed for Claude Code, Gemini CLI, and GitHub Copilot.
  Requires access to zul-writer/assets/ and zul-writer/references/.
metadata:                     # optional: key-value pairs for extra info
  author: hawk
  version: "1.0.0"
allowed-tools: Bash Read      # optional, experimental
---
```

> The existing `zul-writer/SKILL.md` only needs `description` enriched with trigger keywords, and the deprecated `context: fork` field removed (it's Claude-specific, not in the official spec).

---

### 2. Marketplace Storefront

#### [NEW] `marketplace.json`

No official standard exists for `marketplace.json` — this is a **custom index file** for human readers and future tooling.

```json
{
  "name": "ZK Framework Agent Skills",
  "description": "AI agent skills for ZK Framework development. Compatible with Claude Code, Gemini CLI, and GitHub Copilot.",
  "homepage": "https://github.com/your-org/agent-skill",
  "license": "MIT",
  "compatibility": {
    "claude-code": true,
    "gemini-cli": true,
    "github-copilot": true
  },
  "skills": [
    {
      "id": "zul-writer",
      "name": "ZUL Writer",
      "version": "1.0.0",
      "description": "Generates ZK Framework ZUL pages via a structured 3-step workflow.",
      "path": "skills/zul-writer/SKILL.md",
      "tags": ["zkoss", "zul", "ui-generation", "java", "mvvm", "mvc"],
      "install": {
        "claude-code-global": "~/.claude/skills/zul-writer",
        "claude-code-project": ".agent/skills/zul-writer",
        "gemini-cli": "gemini extension install .",
        "github-copilot": ".github/skills/zul-writer"
      }
    }
  ]
}
```

---

### 3. Gemini CLI Support

#### [NEW] `gemini-extension.json` (root-level)

Based on the **official Gemini CLI extension format** ([geminicli.com/docs/extensions/writing-extensions](https://geminicli.com/docs/extensions/writing-extensions)):

```json
{
  "name": "zk-agent-skills",
  "version": "1.0.0",
  "description": "ZK Framework agent skills for Gemini CLI",
  "contextFileName": "GEMINI.md"
}
```

- `name`: lowercase + hyphens only, 1-64 chars
- `contextFileName`: loads `GEMINI.md` as repo-level context for Gemini
- Gemini CLI auto-discovers skills from the `skills/<name>/SKILL.md` subdirectory

#### [NEW] `GEMINI.md` (root-level)

Gemini CLI's equivalent of `CLAUDE.md`. High-level guidance for Gemini when working in this repo.

> **Note**: `skills/zul-writer/` is the canonical location (real files, see directory structure). Gemini CLI will discover it automatically from the `skills/` subdirectory.

**Installation (user side):**
```bash
# Install from a local path
gemini extension install /path/to/agent-skill

# Or from GitHub (once published)
gemini extension install github:your-org/agent-skill
```

---

### 4. GitHub Copilot / Cursor Support

#### [NEW] `.github/skills/zul-writer/`

GitHub Copilot (VS Code ≥ 1.108) and Cursor discover skills at `.github/skills/<name>/SKILL.md`. No additional JSON manifest is required.

- **macOS/Linux**: `install-skill.sh` creates a symlink → `../../skills/zul-writer`
- **Windows**: `install-skill.sh` copies the `skills/zul-writer/` folder here instead

---

### 5. Updated Install Scripts

#### [MODIFY] `install-skill.sh`

Add a `--tool` flag with options: `claude` (default/existing), `gemini`, `github`, `all`.

```bash
# After the existing Claude symlink section, add:

if [[ "$TOOL" == "github" || "$TOOL" == "all" ]]; then
  mkdir -p .github/skills
  ln -sf "$(pwd)/zul-writer" .github/skills/zul-writer
  echo "Linked skill to .github/skills/zul-writer (GitHub Copilot / Cursor)"
fi

if [[ "$TOOL" == "gemini" || "$TOOL" == "all" ]]; then
  mkdir -p skills
  ln -sf "$(pwd)/zul-writer" skills/zul-writer
  echo "Linked skill to skills/zul-writer (Gemini CLI extension)"
  echo "Run: gemini extension install $(pwd)"
fi
```

#### [MODIFY] `link-skill.sh`

Same additions as `install-skill.sh` but for project-local linking.

---

### 7. Documentation Updates

#### [MODIFY] `README.md`

Rewrite to introduce the marketplace concept, add a compatibility table, and per-tool install instructions.

#### [MODIFY] `CLAUDE.md`

Update the structure section to include `marketplace.json`, `gemini-extension.json`, `GEMINI.md`, `skills/`, and `.github/skills/`.

---

## Phased Execution Roadmap

### Phase 1 — Restructure: Move `zul-writer/` → `skills/zul-writer/`
- [x] Move `zul-writer/` to `skills/zul-writer/`
- [x] Update `.agent/skills/zul-writer` symlink → `../../skills/zul-writer`
- [x] Update `install-skill.sh` source path
- [x] Update `CLAUDE.md` structure section
- [ ] Commit

### Phase 2 — SKILL.md Spec Compliance
- [x] Update `skills/zul-writer/SKILL.md` frontmatter: enrich `description` with trigger keywords, add `metadata`/`compatibility`, remove non-standard `context:` field
- [ ] Commit

### Phase 3 — Marketplace Storefront
- [ ] Create `marketplace.json`
- [ ] Create `GEMINI.md`
- [ ] Update `README.md` with multi-tool install instructions
- [ ] Commit

### Phase 4 — Gemini CLI Extension
- [ ] Create `gemini-extension.json` (minimal version, no MCP server)
- [ ] Test: `gemini extension install .` and verify skill appears
- [ ] Commit

### Phase 5 — GitHub Copilot / Cursor
- [ ] Update `install-skill.sh`: symlink (macOS/Linux) or copy (Windows) to `.github/skills/zul-writer/`
- [ ] Commit

---

## Verification Plan

| Phase | Command / Action | Expected Result |
|---|---|---|
| Move skill | `ls skills/zul-writer/SKILL.md` | File exists at new canonical path |
| Claude link | `ls -la .agent/skills/` | Symlink points to `../../skills/zul-writer` |
| SKILL.md | `head -20 skills/zul-writer/SKILL.md` | `name`, `description` present; no `context: fork` |
| marketplace.json | `python3 -m json.tool marketplace.json` | Parses without error |
| gemini-extension.json | `python3 -m json.tool gemini-extension.json` | Parses without error |
| Gemini extension | `gemini extension install .` | Extension installed; skill listed |
| GitHub skills | `ls .github/skills/zul-writer/SKILL.md` | Accessible (symlink or copy) |
