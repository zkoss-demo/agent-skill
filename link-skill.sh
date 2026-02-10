#!/bin/bash

# Link zul-writer skill to current project via symlink
# Usage: ./link-skill.sh

SKILL_NAME="zul-writer"
SKILL_SOURCE="$(cd "$(dirname "$0")/$SKILL_NAME" && pwd)"
SKILL_TARGET="$(pwd)/.agent/skills/$SKILL_NAME"

# Check if source skill directory exists
if [ ! -d "$SKILL_SOURCE" ]; then
    echo "Error: Skill directory not found at $SKILL_SOURCE"
    exit 1
fi

# Check if SKILL.md exists in source
if [ ! -f "$SKILL_SOURCE/SKILL.md" ]; then
    echo "Error: SKILL.md not found in $SKILL_SOURCE"
    exit 1
fi

# Create skills directory if it doesn't exist
mkdir -p "$(pwd)/.agent/skills"

# Remove existing symlink or directory if it exists
if [ -L "$SKILL_TARGET" ]; then
    echo "Removing existing symlink at $SKILL_TARGET"
    rm "$SKILL_TARGET"
elif [ -d "$SKILL_TARGET" ]; then
    echo "Warning: Directory exists at $SKILL_TARGET"
    read -p "Remove it and create symlink? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$SKILL_TARGET"
    else
        echo "Aborted."
        exit 1
    fi
fi

# Create symlink
ln -s "$SKILL_SOURCE" "$SKILL_TARGET"

if [ $? -eq 0 ]; then
    echo "Successfully linked $SKILL_NAME skill"
    echo "  Source: $SKILL_SOURCE"
    echo "  Target: $SKILL_TARGET"
else
    echo "Error: Failed to create symlink"
    exit 1
fi
