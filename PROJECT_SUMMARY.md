# bring-cli — Project Summary

**Created:** 2026-03-23  
**Status:** ✅ Complete, CI passing, published to GitHub  
**Repository:** https://github.com/havocked/bring-cli (PUBLIC)

## What It Does

Command-line interface for the [Bring!](https://www.getbring.com/) shopping list app. Enables:
- Terminal-based grocery list management
- AI agent integration (OpenClaw, Claude, etc.)
- Bulk operations via JSON/stdin
- Automation scripts and workflows

## Quality Metrics

- **Test coverage:** 81% (42 tests, all passing)
- **CI pipeline:** ruff (lint + format), mypy, bandit, pytest
- **First CI run:** ✅ Passed (24s)
- **Lines of code:** ~1550 across 11 files
- **Documentation:** Comprehensive README with AI integration examples

## Architecture

```
bring-cli/
├── src/
│   ├── cli.py          # argparse CLI (182 LOC)
│   └── client.py       # Thin wrapper around bring-api (67 LOC)
├── tests/              # 42 tests, mocked API calls
├── .github/workflows/  # CI: ruff, mypy, pytest, bandit
├── README.md           # Public-facing docs
└── pyproject.toml      # Python 3.12+, bring-api>=1.1.1
```

**Design principles:**
- CLI-first (composable, agent-friendly)
- Async throughout (aiohttp, bring-api)
- Clean separation: CLI args → client wrapper → bring-api
- Secure credentials (0600 permissions, .gitignore)

## Key Features

### Commands
- `login` — Interactive credential setup
- `lists` — Show all shopping lists
- `list` — Show items on a list
- `add` — Add items (with specifications)
- `remove` — Remove items
- `check` — Mark items complete
- `clear` — Clear all items (with confirmation)

### Agent Integration
- **JSON input:** `--json '[{"item": "...", "spec": "..."}]'`
- **stdin mode:** `echo "Items" | bring-cli add --stdin`
- **Colon syntax:** `"Eggs:x12"` → item="Eggs", spec="x12"
- **List resolution:** By name (partial, case-insensitive) or default to first

## Testing

**42 tests:**
- 29 CLI tests (argument parsing, command handlers)
- 13 client tests (credentials, API wrapper)
- All API calls mocked (pytest-asyncio)

**Coverage gaps (19% uncovered):**
- Error handling in `cmd_login` (invalid credentials, network)
- Exception paths in CLI main loop
- Client edge cases (no lists, get_list_items errors)

These are low-risk paths that would require integration tests or real API calls to cover.

## CI Pipeline

GitHub Actions on every push/PR:
1. Lint (ruff)
2. Format check (ruff)
3. Type check (mypy)
4. Security scan (bandit -ll)
5. Tests + coverage (pytest, 75% minimum)

## Manual Testing

Verified with real Bring! API:
- ✅ Lists command shows user's lists
- ✅ List command shows current groceries
- ✅ Add/remove/check operations work instantly
- ✅ Changes reflect in official Bring! app immediately

## Reference Repos

Built to match quality standards:
- **HomeClaw** — README structure, badges, architecture diagram
- **tidal-cli** — Command table layout, quick start
- **kitacare-cli** — Python CLI patterns, pyproject.toml config
- **garmin-coach** — CI pipeline (ruff, mypy, pytest, bandit)

## Lessons

1. **MagicMock `.name` gotcha** — `.name` is a special attribute, must be set via `mock.name = "value"` not `MagicMock(name="value")`
2. **aiohttp.ClientSession mocking** — Must be AsyncMock or `.close()` fails with "object can't be awaited"
3. **bring-api types** — `get_list()` returns `BringItemsResponse.items: Items`, not `BringListItemDetails`
4. **Package structure** — Need `[build-system]` in pyproject.toml + `setup.py` with `find_packages` for pip install to work

## Next Steps (if needed)

- Publish to PyPI (`pip install bring-cli`)
- Add `--version` flag
- Support for multiple shopping lists in one command
- Watch mode for real-time sync
- Shell completion (bash/zsh)
- Docker image for containerized use

## Dependencies

- **bring-api** (1.1.1) — Unofficial Bring! API client by @miaucl
- **aiohttp** (3.9.0+) — Async HTTP
- Python 3.12+ required

## License & Legal

- **License:** MIT
- **Disclaimer:** Unofficial, not affiliated with Bring! Labs AG
- **Credits:** Built on top of `bring-api` by [@miaucl](https://github.com/miaucl)
