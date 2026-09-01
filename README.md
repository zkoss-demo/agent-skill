# Universal Agent Skill Marketplace for ZK Framework

A cross-platform AI agent skill marketplace for ZK Framework development. Supported by Claude Code, Gemini CLI, and GitHub Copilot/Cursor.

## Features

- **Multi-Tool Support**: Use the same skills across different AI assistants.
- **ZK Expertise**: Specialist guidance for ZK 9/10, MVC, and MVVM patterns.
- **Visual Analysis**: Convert UI screenshots or mockups directly into ZUL code.
- **Automated Validation**: Integrated scripts to verify ZUL structural and formatting rules.

## 📦 Marketplace Index

The [marketplace.json](marketplace.json) file provides a machine-readable index of all available skills, including their versions, tags, and installation metadata. Use this if you need to manually configure agent skills in other environments.

### Current Skills:
- **zul-writer**: Generates ZK Framework ZUL pages via a structured 5-step workflow, any step of which can be run on its own. It records **anonymous, aggregate** usage counts (only the skill name and version) to gauge how often the skill is used. No identifier is created or stored — there is no visitor ID, cookie, or per-install file — and your IP address is not logged, so events cannot be linked to you or your machine. Opt out entirely by setting `DO_NOT_TRACK=1` (or `TRACK_URL=`) in your environment.

## Repository Structure

```
agent-skill/
├── marketplace.json      # Storefront index of all skills
├── gemini-extension.json # Gemini CLI extension manifest
├── GEMINI.md             # Gemini CLI guidance file
├── CLAUDE.md             # Claude Code guidance file
├── skills/               # Canonical skill location (real files)
│   └── zul-writer/      
├── doc/                  # Design rationale, decisions, measured ZK behaviour, open items
└── .github/skills/       # GitHub Copilot / Cursor skills (symlinked)
```

See [doc/README.md](doc/README.md) for why the skill is shaped the way it is, what has been decided and
deliberately ruled out, and what is still open.

## Installation

This repository conforms to the [Agent Skills specification](https://agentskills.io/specification). You can install the agent skills using the following methods:

### Agent Skills CLI
The recommended way is using the universal Agent Skills CLI since it supports almost all AI tools (Gemini CLI, Claude Code, GitHub Copilot/Cursor). See [available agents](https://github.com/vercel-labs/skills?tab=readme-ov-file#available-agents) for more details. 

```bash
npx skills add zkoss-demo/agent-skill
```


### Gemini CLI

The fastest way is to install directly from the repository URL:

```bash
gemini extension install https://github.com/zkoss-demo/agent-skill
```


## Development & Testing

- `skills/zul-writer/assets/`: ZUL and Java templates.
- `skills/zul-writer/scripts/`: Validation tools.
- `zulwriter-showcase/`: Gallery of generated UIs.
- `test/`: Test data for validation scripts.
