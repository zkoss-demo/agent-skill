#!/bin/bash

# Link ZK agent skills to current project via symlink
# Usage: ./link-skill.sh [--tool claude|gemini|github|all]

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

link_claude() {
    SKILL_TARGET="$(pwd)/.agent/skills/$SKILL_NAME"
    mkdir -p "$(pwd)/.agent/skills"
    
    if [ -L "$SKILL_TARGET" ]; then
        rm "$SKILL_TARGET"
    elif [ -d "$SKILL_TARGET" ]; then
        echo "Warning: Directory exists at $SKILL_TARGET. Skipping Claude link."
        return
    fi
    
    ln -s "$SKILL_SOURCE" "$SKILL_TARGET"
    echo "Successfully linked to Claude Code project: $SKILL_TARGET"
}

link_github() {
    GITHUB_DIR="$(pwd)/.github/skills"
    mkdir -p "$GITHUB_DIR"
    SKILL_TARGET="$GITHUB_DIR/$SKILL_NAME"
    
    if [ -L "$SKILL_TARGET" ]; then
        rm "$SKILL_TARGET"
    fi
    
    # We use a relative link if we are in the same repo, or absolute if outside
    if [[ "$(pwd)" == "$REPO_ROOT" ]]; then
        ln -s "../../skills/$SKILL_NAME" "$SKILL_TARGET"
    else
        ln -s "$SKILL_SOURCE" "$SKILL_TARGET"
    fi
    echo "Successfully linked for GitHub Copilot / Cursor: $SKILL_TARGET"
}

link_gemini() {
    if [[ "$(pwd)" == "$REPO_ROOT" ]]; then
        echo "Gemini CLI integration ready in root."
    else
        # Linking for Gemini in another project would typically mean installing as an extension
        echo "To use these skills in another project with Gemini CLI, install this repo as an extension:"
        echo "gemini extension install $REPO_ROOT"
    fi
}

case "$TOOL" in
    "claude")
        link_claude
        ;;
    "github")
        link_github
        ;;
    "gemini")
        link_gemini
        ;;
    "all")
        link_claude
        link_github
        link_gemini
        ;;
    *)
        echo "Error: Unknown tool '$TOOL'. Use claude, gemini, github, or all."
        exit 1
        ;;
esac
