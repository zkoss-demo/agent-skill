# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains Claude Code agent skills. Each skill is a self-contained directory with a `SKILL.md` file that defines the skill's behavior, workflow, and instructions.

## Structure

```
agent-skill/
├── zul-writer/           # Skill for generating ZK Framework ZUL pages
│   └── SKILL.md          # Skill definition with workflow and examples
├── install-skill.sh      # Script to symlink skills to ~/.claude/skills/
└── .claude/
    └── settings.local.json
```

## Installing Skills

Skills are installed by creating symlinks in `~/.claude/skills/`:

```bash
./install-skill.sh
```

This creates a symlink from `./zul-writer` to `~/.claude/skills/zul-writer`.

## Creating New Skills

1. Create a new directory with the skill name
2. Add a `SKILL.md` file with YAML frontmatter:
   ```yaml
   ---
   name: skill-name
   description: Brief description of what the skill does
   context: fork
   ---
   ```
3. Document the workflow, guidelines, and examples in the markdown body
4. Update `install-skill.sh` or create a new install script for the skill

## Skill Anatomy (SKILL.md)

- **Frontmatter**: `name`, `description`, `context` (fork/inline)
- **Workflow sections**: Step-by-step process the skill follows
- **Code examples**: Reference patterns and templates
- **Validation checklists**: Quality checks for generated output
