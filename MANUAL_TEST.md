# Manual Testing Guide

Quick verification that the CLI works end-to-end with the real Bring! API.

## Prerequisites

```bash
# Credentials already exist at ~/.config/bring/credentials.json
# If not, run: bring-cli login
```

## Basic Commands

```bash
# List all shopping lists
bring-cli lists

# Show items on default list
bring-cli list

# Show items on specific list
bring-cli list --name "Home"
```

## Add Items

```bash
# Add simple items
bring-cli add "Test Item 1" "Test Item 2"

# Add items with specifications
bring-cli add "Test Eggs:x6" "Test Butter:unsalted"

# JSON mode (agent-friendly)
bring-cli add --json '[{"item": "Test JSON Item", "spec": "from CLI"}]'

# stdin mode (pipe-friendly)
echo -e "Test Stdin 1\nTest Stdin 2:spec" | bring-cli add --stdin
```

## Check & Remove

```bash
# Mark items as completed
bring-cli check "Test Item 1" "Test Item 2"

# Remove items
bring-cli remove "Test Eggs" "Test Butter" "Test JSON Item" "Test Stdin 1" "Test Stdin 2"
```

## Verify

```bash
# List items again to confirm changes
bring-cli list
```

## Test Result (2026-03-23)

✅ All commands work correctly with real Bring! API
✅ Items appear instantly in official Bring! app
✅ Credentials loaded from ~/.config/bring/credentials.json
✅ Package installs correctly via pip
