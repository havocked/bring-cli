"""Command-line interface for Bring! shopping lists."""

import argparse
import asyncio
import getpass
import json
import sys
from pathlib import Path

from src.client import BringClient, BringCredentials

# Default credential file location
DEFAULT_CREDENTIALS_PATH = Path.home() / ".config" / "bring" / "credentials.json"


def parse_item_spec(item_str: str) -> tuple[str, str]:
    """
    Parse item string into (item, specification).

    Examples:
        "Eggs" -> ("Eggs", "")
        "Eggs:x12" -> ("Eggs", "x12")
        "Butter:unsalted" -> ("Butter", "unsalted")
    """
    if ":" in item_str:
        item, spec = item_str.split(":", 1)
        return item.strip(), spec.strip()
    return item_str.strip(), ""


def load_credentials(path: Path) -> BringCredentials:
    """Load credentials from file."""
    try:
        return BringCredentials.from_file(path)
    except FileNotFoundError:
        print(f"❌ No credentials found at {path}", file=sys.stderr)
        print("Run 'bring-cli login' first to set up your account.", file=sys.stderr)
        sys.exit(1)


async def cmd_login(args: argparse.Namespace) -> None:
    """Interactive login — prompt for credentials and save."""
    print("🔐 Bring! Login")
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ").strip()

    if not email or not password:
        print("❌ Email and password are required", file=sys.stderr)
        sys.exit(1)

    # Test credentials
    print("Validating credentials...", end="", flush=True)
    credentials = BringCredentials(email=email, password=password)
    try:
        async with BringClient(credentials) as client:
            lists = await client.get_lists()
            print(f" ✅ Success! Found {len(lists)} list(s).")
    except Exception as e:
        print(f" ❌ Login failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Save credentials
    path = Path(args.credentials)
    credentials.save(path)
    print(f"💾 Credentials saved to {path}")


async def cmd_lists(args: argparse.Namespace) -> None:
    """List all shopping lists."""
    credentials = load_credentials(Path(args.credentials))
    async with BringClient(credentials) as client:
        lists = await client.get_lists()
        if not lists:
            print("No lists found.")
            return
        print(f"📋 Shopping Lists ({len(lists)}):\n")
        for i, lst in enumerate(lists, 1):
            print(f"{i}. {lst.name} ({lst.listUuid})")


async def cmd_list(args: argparse.Namespace) -> None:
    """Show items on a specific list."""
    credentials = load_credentials(Path(args.credentials))
    async with BringClient(credentials) as client:
        if args.name:
            lst = await client.find_list_by_name(args.name)
            if not lst:
                print(f"❌ List '{args.name}' not found", file=sys.stderr)
                sys.exit(1)
        else:
            lst = await client.get_default_list()

        items = await client.get_list_items(lst.listUuid)
        print(f"🛒 {lst.name}")
        print()

        if not items.purchase:
            print("(empty)")
            return

        for purchase in items.purchase:
            spec_str = f" ({purchase.specification})" if purchase.specification else ""
            print(f"  • {purchase.itemId}{spec_str}")


async def cmd_add(args: argparse.Namespace) -> None:
    """Add items to a list."""
    credentials = load_credentials(Path(args.credentials))

    # Determine items to add
    items_to_add: list[tuple[str, str]] = []

    if args.json:
        # JSON mode: [{"item": "...", "spec": "..."}, ...]
        data = json.loads(args.json)
        for entry in data:
            items_to_add.append((entry["item"], entry.get("spec", "")))

    elif args.stdin:
        # stdin mode: one item per line, supports "Item:spec" format
        for line in sys.stdin:
            line = line.strip()
            if line:
                items_to_add.append(parse_item_spec(line))

    elif args.items:
        # Normal mode: positional arguments
        for item_str in args.items:
            items_to_add.append(parse_item_spec(item_str))

    else:
        print("❌ No items provided", file=sys.stderr)
        sys.exit(1)

    async with BringClient(credentials) as client:
        if args.list:
            lst = await client.find_list_by_name(args.list)
            if not lst:
                print(f"❌ List '{args.list}' not found", file=sys.stderr)
                sys.exit(1)
        else:
            lst = await client.get_default_list()

        print(f"+ Adding {len(items_to_add)} item(s) to '{lst.name}'...")
        for item, spec in items_to_add:
            await client.add_item(lst.listUuid, item, spec)
            spec_str = f" ({spec})" if spec else ""
            print(f"  ✓ {item}{spec_str}")


async def cmd_remove(args: argparse.Namespace) -> None:
    """Remove items from a list."""
    credentials = load_credentials(Path(args.credentials))
    async with BringClient(credentials) as client:
        if args.list:
            lst = await client.find_list_by_name(args.list)
            if not lst:
                print(f"❌ List '{args.list}' not found", file=sys.stderr)
                sys.exit(1)
        else:
            lst = await client.get_default_list()

        print(f"🗑️  Removing {len(args.items)} item(s) from '{lst.name}'...")
        for item in args.items:
            await client.remove_item(lst.listUuid, item)
            print(f"  ✓ {item}")


async def cmd_check(args: argparse.Namespace) -> None:
    """Mark items as completed (check off)."""
    credentials = load_credentials(Path(args.credentials))
    async with BringClient(credentials) as client:
        if args.list:
            lst = await client.find_list_by_name(args.list)
            if not lst:
                print(f"❌ List '{args.list}' not found", file=sys.stderr)
                sys.exit(1)
        else:
            lst = await client.get_default_list()

        print(f"✅ Checking off {len(args.items)} item(s) from '{lst.name}'...")
        for item in args.items:
            await client.complete_item(lst.listUuid, item)
            print(f"  ✓ {item}")


async def cmd_clear(args: argparse.Namespace) -> None:
    """Clear all items from a list."""
    credentials = load_credentials(Path(args.credentials))
    async with BringClient(credentials) as client:
        if args.list:
            lst = await client.find_list_by_name(args.list)
            if not lst:
                print(f"❌ List '{args.list}' not found", file=sys.stderr)
                sys.exit(1)
        else:
            lst = await client.get_default_list()

        # Confirmation
        if not args.yes:
            response = input(f"⚠️  Clear all items from '{lst.name}'? [y/N] ").strip().lower()
            if response not in ("y", "yes"):
                print("Cancelled.")
                return

        items = await client.get_list_items(lst.listUuid)
        count = len(items.purchase)
        print(f"🗑️  Clearing {count} item(s) from '{lst.name}'...")
        await client.clear_list(lst.listUuid)
        print("✅ Done.")


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="bring-cli",
        description="Command-line interface for Bring! shopping lists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--credentials", default=str(DEFAULT_CREDENTIALS_PATH), help="Path to credentials.json")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # login
    subparsers.add_parser("login", help="Login and save credentials")

    # lists
    subparsers.add_parser("lists", help="List all shopping lists")

    # list
    list_parser = subparsers.add_parser("list", help="Show items on a list")
    list_parser.add_argument("--name", help="List name (partial match, case-insensitive)")

    # add
    add_parser = subparsers.add_parser("add", help="Add items to a list")
    add_parser.add_argument("items", nargs="*", help="Items to add (format: 'Item' or 'Item:specification')")
    add_parser.add_argument("--list", help="Target list name")
    add_parser.add_argument("--json", help="JSON array: [{'item': '...', 'spec': '...'}]")
    add_parser.add_argument("--stdin", action="store_true", help="Read items from stdin (one per line)")

    # remove
    remove_parser = subparsers.add_parser("remove", help="Remove items from a list")
    remove_parser.add_argument("items", nargs="+", help="Items to remove")
    remove_parser.add_argument("--list", help="Target list name")

    # check
    check_parser = subparsers.add_parser("check", help="Mark items as completed (check off)")
    check_parser.add_argument("items", nargs="+", help="Items to check off")
    check_parser.add_argument("--list", help="Target list name")

    # clear
    clear_parser = subparsers.add_parser("clear", help="Clear all items from a list")
    clear_parser.add_argument("--list", help="Target list name")
    clear_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Map commands to handlers
    handlers = {
        "login": cmd_login,
        "lists": cmd_lists,
        "list": cmd_list,
        "add": cmd_add,
        "remove": cmd_remove,
        "check": cmd_check,
        "clear": cmd_clear,
    }

    handler = handlers.get(args.command)
    if handler:
        try:
            asyncio.run(handler(args))
        except KeyboardInterrupt:
            print("\n❌ Interrupted", file=sys.stderr)
            sys.exit(130)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
