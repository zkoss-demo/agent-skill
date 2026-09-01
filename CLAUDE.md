# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@README.md

## Installing Skills (Claude Code)

Skills are installed by creating symlinks in `~/.claude/skills/`:

```bash
./install-skill.sh
```

This creates a symlink from `./zul-writer` to `~/.claude/skills/zul-writer`.

## Loading Skills (Gemini CLI)

Gemini CLI automatically discovers skills in the `skills/` directory when this extension is installed.

To install this repo as a Gemini extension:
```bash
gemini extension install .
```

## Creating New Skills

1. Create a new directory in `skills/` (e.g., `skills/new-skill`)
2. Add a `SKILL.md` file following the [Agent Skills specification](https://agentskills.io/specification)
3. Document the workflow, guidelines, and examples in the markdown body.
4. Update `marketplace.json` to include the new skill.
5. Update `install-skill.sh` and `link-skill.sh` to support the new skill.

## Versioning

Two independent version lines. Do not sync one to the other.

**A skill's version** lives in three places that must always match. Bumping a skill means editing all three:

1. `skills/<skill>/SKILL.md` — `metadata.version`
2. `marketplace.json` — that skill's `version` entry
3. the skill's scripts — the `SKILL_VERSION` constant each one sends in its usage ping

**The Gemini extension's version** is `gemini-extension.json` — the version of the packaged extension as a whole, not of any skill inside it. It moves on its own schedule and is deliberately *not* kept in step with a skill bump, so a mismatch there is not drift to fix.

## Skill Anatomy (SKILL.md)

- **Frontmatter**: `name`, `description`, `context` (fork/inline)
- **Workflow sections**: Step-by-step process the skill follows
- **Code examples**: Reference patterns and templates
- **Validation checklists**: Quality checks for generated output

## General Development Guidelines

- The user prefers to control the Python environment with `uv`.
- JavaScript coding convention: [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html).
- Commit every time a feature is complete and all tests pass.
- Only commit files related to the current work.
- Use markdown format as default for documentation.
- Always read `CLAUDE.md` for an overview when starting a new conversation.
- Don't push branches; the user will do it.

# Reference
* https://agentskills.io/home
* https://agentskills.io/specification
* https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf?hsLang=en