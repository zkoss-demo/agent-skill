# GEMINI.md

This file provides guidance to Gemini CLI when working with code in this repository.

## Repository Overview

This repository is an AI agent skill marketplace for ZK Framework development. Skills are stored in the `skills/` directory.

## Structure

```
agent-skill/
├── marketplace.json      # Storefront index of all skills
├── gemini-extension.json # Gemini CLI extension manifest
├── skills/               # Canonical skill location
│   └── zul-writer/       # Skill for generating ZK ZUL pages
│       └── SKILL.md      # Skill definition
└── .github/skills/       # GitHub Copilot / Cursor skills (symlinked)
```

## Loading Skills in Gemini CLI

Gemini CLI automatically discovers skills in the `skills/` directory when this extension is installed.

To install this repo as a Gemini extension:
```bash
gemini extension install .
```

## Creating New Skills

1. Create a new directory in `skills/` (e.g., `skills/new-skill`)
2. Add a `SKILL.md` file following the [Agent Skills specification](https://agentskills.io/specification)
3. Update `marketplace.json` to include the new skill
4. Update `install-skill.sh` and `link-skill.sh` to support the new skill
