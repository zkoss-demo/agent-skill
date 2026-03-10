#!/bin/bash

# Install ZK agent skills to AI tools via symlink
# Usage: ./install-skill.sh [--tool claude|gemini|github|all]

TOOL="claude"
if [[ "$1" == "--tool" && -n "$2" ]]; then
    TOOL="$2"
fi

SKILL_NAME="zul-writer"
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILL_SOURCE="$REPO_ROOT/skills/$SKILL_NAME"

# Check if source skill directory exists
if [ ! -d "$SKILL_SOURCE" ]; then
    echo "Error: Skill directory not found at $SKILL_SOURCE"
    exit 1
fi

install_claude() {
    SKILL_TARGET="$HOME/.claude/skills/$SKILL_NAME"
    mkdir -p "$HOME/.claude/skills"
    
    if [ -L "$SKILL_TARGET" ]; then
        rm "$SKILL_TARGET"
    elif [ -d "$SKILL_TARGET" ]; then
        echo "Warning: Directory exists at $SKILL_TARGET. Skipping Claude install."
        return
    fi
    
    ln -s "$SKILL_SOURCE" "$SKILL_TARGET"
    echo "Successfully installed to Claude Code: $SKILL_TARGET"
}

install_github() {
    GITHUB_DIR="$REPO_ROOT/.github/skills"
    mkdir -p "$GITHUB_DIR"
    SKILL_TARGET="$GITHUB_DIR/$SKILL_NAME"
    
    if [ -L "$SKILL_TARGET" ]; then
        rm "$SKILL_TARGET"
    fi
    
    ln -s "../../skills/$SKILL_NAME" "$SKILL_TARGET"
    echo "Successfully linked for GitHub Copilot / Cursor: $SKILL_TARGET"
}

install_gemini() {
    # Gemini CLI auto-discovers from the skills/ directory in the extension root
    echo "Gemini CLI integration ready."
    echo "To install as a Gemini extension, run: gemini extension install $REPO_ROOT"
}

case "$TOOL" in
    "claude")
        install_claude
        ;;
    "github")
        install_github
        ;;
    "gemini")
        install_gemini
        ;;
    "all")
        install_claude
        install_github
        install_gemini
        ;;
    *)
        echo "Error: Unknown tool '$TOOL'. Use claude, gemini, github, or all."
        exit 1
        ;;
esac
