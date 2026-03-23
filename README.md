# bring-cli

> Command-line interface for the [Bring!](https://www.getbring.com/) shopping list app

[![CI](https://github.com/havocked/bring-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/havocked/bring-cli/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why?

Bring! is a popular shopping list app, but it lacks a proper API or CLI for automation. This tool bridges that gap:

- **Quick grocery additions** from the terminal — faster than opening the app
- **AI agent integration** — let Claude, OpenClaw, or other assistants manage your shopping lists
- **Scriptable workflows** — pipe lists from meal plans, recipes, or inventory tools
- **Bulk operations** — add 20 items from a text file in one command

## Quick Start

```bash
# Install
pip install bring-cli

# Login (one-time setup)
bring-cli login

# Add items
bring-cli add "Eggs" "Butter" "Milk:2L"

# List what's on your shopping list
bring-cli list

# Check off items
bring-cli check "Eggs"

# Remove items
bring-cli remove "Butter"
```

## Installation

**Requirements:** Python 3.12+

```bash
pip install bring-cli
```

Or from source:

```bash
git clone https://github.com/havocked/bring-cli.git
cd bring-cli
pip install -e .
```

## Commands

### Setup

#### `bring-cli login`

Interactive login — prompts for email and password, validates credentials, and saves them securely.

```bash
bring-cli login
# 🔐 Bring! Login
# Email: you@example.com
# Password: ********
#  ✅ Success! Found 2 list(s).
# 💾 Credentials saved to ~/.config/bring/credentials.json
```

### Lists

#### `bring-cli lists`

Show all your shopping lists.

```bash
bring-cli lists
# 📋 Shopping Lists (2):
#
# 1. Home (699e5b55-274b-499c-b995-dcefa5e5921b)
# 2. Work (abc12345-6789-0def-ghij-klmnopqrstuv)
```

#### `bring-cli list [--name LIST_NAME]`

Show items on a specific list. If no `--name` is provided, uses your first (default) list.

```bash
bring-cli list
# 🛒 Home
#
#   • Eggs (x12)
#   • Butter
#   • Milk (2L)

bring-cli list --name "Work"
# 🛒 Work
#
#   • Coffee beans
```

### Adding Items

#### `bring-cli add ITEM [ITEM ...] [--list LIST_NAME]`

Add items to your list. Use colon (`:`) to add specifications.

```bash
# Simple items
bring-cli add "Eggs" "Butter"

# With specifications
bring-cli add "Eggs:x12" "Butter:unsalted" "Milk:2L"

# Target specific list
bring-cli add --list "Work" "Coffee beans"
```

#### Bulk operations

**JSON input** (great for programmatic use):

```bash
bring-cli add --json '[{"item": "Eggs", "spec": "x12"}, {"item": "Butter"}]'
```

**stdin mode** (pipe from files or scripts):

```bash
echo -e "Eggs:x12\nButter\nMilk:2L" | bring-cli add --stdin

# From a text file
cat groceries.txt | bring-cli add --stdin
```

### Removing & Checking Off

#### `bring-cli remove ITEM [ITEM ...]`

Remove items from your list.

```bash
bring-cli remove "Eggs" "Butter"
```

#### `bring-cli check ITEM [ITEM ...]`

Mark items as completed (check them off).

```bash
bring-cli check "Eggs" "Butter"
```

#### `bring-cli clear [--list LIST_NAME] [-y]`

Remove all items from a list. Prompts for confirmation unless `-y` is passed.

```bash
bring-cli clear           # Prompts: ⚠️  Clear all items from 'Home'? [y/N]
bring-cli clear -y        # No confirmation
bring-cli clear --list "Work" -y
```

## AI Agent Integration

`bring-cli` is designed to be agent-friendly. AI assistants like [OpenClaw](https://openclaw.com), Claude, or custom workflows can use it to manage shopping lists on your behalf.

### Example: OpenClaw skill

```yaml
# skills/bring/SKILL.md
name: bring
description: Manage Bring! shopping lists

commands:
  add_groceries:
    run: |
      echo "$ITEMS" | bring-cli add --stdin
    prompt: Add these items to the shopping list
```

### Example: Claude Desktop MCP

You can wrap `bring-cli` in an MCP tool to let Claude control your lists:

```typescript
{
  "name": "add_shopping_items",
  "description": "Add items to Bring! shopping list",
  "inputSchema": {
    "type": "object",
    "properties": {
      "items": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Items to add (format: 'Item' or 'Item:specification')"
      }
    }
  }
}
```

Call from your MCP handler:

```typescript
const items = input.items.join('\n');
await exec(`echo "${items}" | bring-cli add --stdin`);
```

### Example: Automation scripts

Pipe recipe ingredients directly to your shopping list:

```bash
#!/bin/bash
# recipe-to-shopping-list.sh

RECIPE="$1"
cat "recipes/$RECIPE.txt" | grep "^-" | sed 's/^- //' | bring-cli add --stdin
```

## Credentials

Credentials are stored at `~/.config/bring/credentials.json` with `0600` permissions (readable only by you).

**Format:**
```json
{
  "email": "you@example.com",
  "password": "your-password"
}
```

**Security notes:**
- Never commit `credentials.json` to version control
- Use app-specific passwords if available
- Rotate credentials periodically
- The file is created with restrictive permissions automatically

## How It Works

This CLI wraps the excellent [`bring-api`](https://github.com/miaucl/bring-api) Python library, which reverse-engineered the Bring! app's internal API. All operations are async under the hood via `aiohttp`.

**API flow:**
1. Load credentials from `~/.config/bring/credentials.json`
2. Authenticate with Bring's servers
3. Execute commands (list, add, remove, etc.)
4. Close session

## Development

```bash
# Clone and setup
git clone https://github.com/havocked/bring-cli.git
cd bring-cli
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint & format
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/ tests/

# Security scan
bandit -r src/

# Full CI check
ruff check src/ tests/ && \
ruff format --check src/ tests/ && \
mypy src/ tests/ && \
bandit -r src/ -ll -q && \
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=75
```

## Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-thing`)
3. Make your changes and add tests
4. Ensure CI passes (`pytest`, `ruff`, `mypy`, `bandit`)
5. Submit a pull request

## Legal & Credits

**Disclaimer:** This project is **unofficial** and **not affiliated with Bring! Labs AG**. It's a community tool built for personal automation and convenience.

**Credits:**
- Built on top of [`bring-api`](https://github.com/miaucl/bring-api) by [@miaucl](https://github.com/miaucl)
- Inspired by the need for better CLI tooling in the smart home/automation space

## License

MIT — see [LICENSE](LICENSE) for details.
