# Universal Agent Skill Marketplace for ZK Framework

A cross-platform AI agent skill marketplace for ZK Framework development. Supported by Claude Code, Gemini CLI, and GitHub Copilot/Cursor.

## Features

- **Multi-Tool Support**: Use the same skills across different AI assistants.
- **ZK Expertise**: Specialist guidance for ZK 9/10, MVC, and MVVM patterns.
- **Visual Analysis**: Convert UI screenshots or mockups directly into ZUL code.
- **Automated Validation**: Integrated scripts to verify ZUL structural and formatting rules.

## Marketplace Index

The [marketplace.json](marketplace.json) file provides a machine-readable index of all available skills.

### Current Skills:
- **zul-writer**: Generates ZK Framework ZUL pages via a structured 4-step workflow.

## Repository Structure

```
agent-skill/
├── marketplace.json      # Storefront index of all skills
├── gemini-extension.json # Gemini CLI extension manifest
├── GEMINI.md             # Gemini CLI guidance file
├── CLAUDE.md             # Claude Code guidance file
├── skills/               # Canonical skill location (real files)
│   └── zul-writer/      
└── .github/skills/       # GitHub Copilot / Cursor skills (symlinked)
```

## Installation

### Claude Code
Symlink skills to Claude Code's global skill directory:
```bash
./install-skill.sh
```
Or link into a specific project:
```bash
./link-skill.sh
```

### Gemini CLI
Install the entire repo as a Gemini extension:
```bash
gemini extension install .
```

### GitHub Copilot / Cursor
Skills are automatically discovered in the `.github/skills/` directory of this repository for project-local use.

---

## Development & Testing

- `skills/zul-writer/assets/`: ZUL and Java templates.
- `skills/zul-writer/scripts/`: Validation tools.
- `zulwriter-showcase/`: Gallery of generated UIs.
- `test/`: Test data for validation scripts.
