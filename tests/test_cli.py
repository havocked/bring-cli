"""Tests for cli.py — CLI argument parsing and command handlers."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cli import build_parser, parse_item_spec


class TestParseItemSpec:
    """Test item specification parsing."""

    def test_simple_item(self):
        """Should parse simple item without specification."""
        item, spec = parse_item_spec("Eggs")
        assert item == "Eggs"
        assert spec == ""

    def test_item_with_spec(self):
        """Should parse item with colon-separated specification."""
        item, spec = parse_item_spec("Eggs:x12")
        assert item == "Eggs"
        assert spec == "x12"

    def test_item_with_spaces(self):
        """Should strip whitespace from item and spec."""
        item, spec = parse_item_spec("  Butter : unsalted  ")
        assert item == "Butter"
        assert spec == "unsalted"

    def test_item_with_multiple_colons(self):
        """Should only split on first colon."""
        item, spec = parse_item_spec("Milk:2L:organic")
        assert item == "Milk"
        assert spec == "2L:organic"


class TestArgumentParsing:
    """Test CLI argument parsing."""

    def test_login_command(self):
        """Should parse login command."""
        parser = build_parser()
        args = parser.parse_args(["login"])
        assert args.command == "login"

    def test_lists_command(self):
        """Should parse lists command."""
        parser = build_parser()
        args = parser.parse_args(["lists"])
        assert args.command == "lists"

    def test_list_command_default(self):
        """Should parse list command without arguments."""
        parser = build_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"
        assert args.name is None

    def test_list_command_with_name(self):
        """Should parse list command with --name."""
        parser = build_parser()
        args = parser.parse_args(["list", "--name", "Home"])
        assert args.command == "list"
        assert args.name == "Home"

    def test_add_command_positional(self):
        """Should parse add command with positional items."""
        parser = build_parser()
        args = parser.parse_args(["add", "Eggs", "Butter:unsalted"])
        assert args.command == "add"
        assert args.items == ["Eggs", "Butter:unsalted"]
        assert args.list is None

    def test_add_command_with_list(self):
        """Should parse add command with --list."""
        parser = build_parser()
        args = parser.parse_args(["add", "--list", "Home", "Eggs"])
        assert args.command == "add"
        assert args.list == "Home"
        assert args.items == ["Eggs"]

    def test_add_command_json_mode(self):
        """Should parse add command with --json."""
        parser = build_parser()
        json_data = '[{"item": "Eggs", "spec": "x12"}]'
        args = parser.parse_args(["add", "--json", json_data])
        assert args.command == "add"
        assert args.json == json_data

    def test_add_command_stdin_mode(self):
        """Should parse add command with --stdin."""
        parser = build_parser()
        args = parser.parse_args(["add", "--stdin"])
        assert args.command == "add"
        assert args.stdin is True

    def test_remove_command(self):
        """Should parse remove command."""
        parser = build_parser()
        args = parser.parse_args(["remove", "Eggs", "Butter"])
        assert args.command == "remove"
        assert args.items == ["Eggs", "Butter"]

    def test_check_command(self):
        """Should parse check command."""
        parser = build_parser()
        args = parser.parse_args(["check", "Eggs"])
        assert args.command == "check"
        assert args.items == ["Eggs"]

    def test_clear_command(self):
        """Should parse clear command."""
        parser = build_parser()
        args = parser.parse_args(["clear"])
        assert args.command == "clear"
        assert args.yes is False

    def test_clear_command_with_yes(self):
        """Should parse clear command with -y flag."""
        parser = build_parser()
        args = parser.parse_args(["clear", "-y"])
        assert args.command == "clear"
        assert args.yes is True

    def test_custom_credentials_path(self):
        """Should parse --credentials global option."""
        parser = build_parser()
        args = parser.parse_args(["--credentials", "/custom/path.json", "lists"])
        assert args.credentials == "/custom/path.json"
        assert args.command == "lists"


class TestCommandHandlers:
    """Test CLI command handlers (mocked API calls)."""

    @pytest.fixture
    def mock_client(self):
        """Fixture for mocked BringClient."""
        with patch("src.cli.BringClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_credentials(self, tmp_path: Path):
        """Fixture for temporary credentials file."""
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"email": "test@example.com", "password": "secret123"}))
        return creds_file

    @pytest.mark.asyncio
    async def test_cmd_lists_output(self, mock_client, mock_credentials, capsys):
        """Should list all shopping lists."""
        from src.cli import cmd_lists

        mock_list_1 = MagicMock()
        mock_list_1.name = "Home"
        mock_list_1.listUuid = "uuid-1"

        mock_list_2 = MagicMock()
        mock_list_2.name = "Work"
        mock_list_2.listUuid = "uuid-2"

        mock_client.get_lists.return_value = [mock_list_1, mock_list_2]

        args = MagicMock(credentials=str(mock_credentials))
        await cmd_lists(args)

        captured = capsys.readouterr()
        assert "Home" in captured.out
        assert "Work" in captured.out

    @pytest.mark.asyncio
    async def test_cmd_list_default(self, mock_client, mock_credentials, capsys):
        """Should show items from default list."""
        from src.cli import cmd_list

        mock_list = MagicMock()
        mock_list.name = "Home"
        mock_list.listUuid = "uuid-1"
        mock_client.get_default_list.return_value = mock_list

        mock_items = MagicMock()
        mock_items.purchase = [
            MagicMock(itemId="Eggs", specification="x12"),
            MagicMock(itemId="Butter", specification=""),
        ]
        mock_client.get_list_items.return_value = mock_items

        args = MagicMock(credentials=str(mock_credentials))
        args.name = None
        await cmd_list(args)

        captured = capsys.readouterr()
        assert "Home" in captured.out
        assert "Eggs" in captured.out
        assert "x12" in captured.out

    @pytest.mark.asyncio
    async def test_cmd_add_positional_items(self, mock_client, mock_credentials):
        """Should add items from positional arguments."""
        from src.cli import cmd_add

        mock_list = MagicMock(name="Home", listUuid="uuid-1")
        mock_client.get_default_list.return_value = mock_list

        args = MagicMock(
            credentials=str(mock_credentials), items=["Eggs:x12", "Butter"], json=None, stdin=False, list=None
        )
        await cmd_add(args)

        assert mock_client.add_item.await_count == 2
        mock_client.add_item.assert_any_await("uuid-1", "Eggs", "x12")
        mock_client.add_item.assert_any_await("uuid-1", "Butter", "")

    @pytest.mark.asyncio
    async def test_cmd_add_json_mode(self, mock_client, mock_credentials):
        """Should add items from JSON input."""
        from src.cli import cmd_add

        mock_list = MagicMock(name="Home", listUuid="uuid-1")
        mock_client.get_default_list.return_value = mock_list

        json_data = json.dumps([{"item": "Eggs", "spec": "x12"}, {"item": "Butter"}])
        args = MagicMock(credentials=str(mock_credentials), items=[], json=json_data, stdin=False, list=None)
        await cmd_add(args)

        assert mock_client.add_item.await_count == 2
        mock_client.add_item.assert_any_await("uuid-1", "Eggs", "x12")
        mock_client.add_item.assert_any_await("uuid-1", "Butter", "")

    @pytest.mark.asyncio
    async def test_cmd_add_stdin_mode(self, mock_client, mock_credentials, monkeypatch):
        """Should add items from stdin."""
        from io import StringIO

        from src.cli import cmd_add

        mock_list = MagicMock(name="Home", listUuid="uuid-1")
        mock_client.get_default_list.return_value = mock_list

        stdin_data = StringIO("Eggs:x12\nButter\nMilk:2L\n")
        monkeypatch.setattr("sys.stdin", stdin_data)

        args = MagicMock(credentials=str(mock_credentials), items=[], json=None, stdin=True, list=None)
        await cmd_add(args)

        assert mock_client.add_item.await_count == 3
        mock_client.add_item.assert_any_await("uuid-1", "Eggs", "x12")
        mock_client.add_item.assert_any_await("uuid-1", "Butter", "")
        mock_client.add_item.assert_any_await("uuid-1", "Milk", "2L")

    @pytest.mark.asyncio
    async def test_cmd_remove(self, mock_client, mock_credentials):
        """Should remove items from list."""
        from src.cli import cmd_remove

        mock_list = MagicMock(name="Home", listUuid="uuid-1")
        mock_client.get_default_list.return_value = mock_list

        args = MagicMock(credentials=str(mock_credentials), items=["Eggs", "Butter"], list=None)
        await cmd_remove(args)

        assert mock_client.remove_item.await_count == 2
        mock_client.remove_item.assert_any_await("uuid-1", "Eggs")
        mock_client.remove_item.assert_any_await("uuid-1", "Butter")

    @pytest.mark.asyncio
    async def test_cmd_check(self, mock_client, mock_credentials):
        """Should mark items as completed."""
        from src.cli import cmd_check

        mock_list = MagicMock(name="Home", listUuid="uuid-1")
        mock_client.get_default_list.return_value = mock_list

        args = MagicMock(credentials=str(mock_credentials), items=["Eggs"], list=None)
        await cmd_check(args)

        mock_client.complete_item.assert_awaited_once_with("uuid-1", "Eggs")

    @pytest.mark.asyncio
    async def test_cmd_clear_with_confirmation(self, mock_client, mock_credentials, monkeypatch):
        """Should clear list after confirmation."""
        from src.cli import cmd_clear

        mock_list = MagicMock(name="Home", listUuid="uuid-1")
        mock_client.get_default_list.return_value = mock_list

        mock_items = MagicMock()
        mock_items.purchase = [MagicMock(itemId="Eggs")]
        mock_client.get_list_items.return_value = mock_items

        # Simulate user typing "y"
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = MagicMock(credentials=str(mock_credentials), list=None, yes=False)
        await cmd_clear(args)

        mock_client.clear_list.assert_awaited_once_with("uuid-1")

    @pytest.mark.asyncio
    async def test_cmd_clear_skip_confirmation(self, mock_client, mock_credentials):
        """Should clear list without confirmation when -y flag passed."""
        from src.cli import cmd_clear

        mock_list = MagicMock()
        mock_list.name = "Home"
        mock_list.listUuid = "uuid-1"
        mock_client.get_default_list.return_value = mock_list

        mock_items = MagicMock()
        mock_items.purchase = []
        mock_client.get_list_items.return_value = mock_items

        args = MagicMock(credentials=str(mock_credentials), list=None, yes=True)
        await cmd_clear(args)

        mock_client.clear_list.assert_awaited_once_with("uuid-1")

    @pytest.mark.asyncio
    async def test_cmd_login_success(self, tmp_path, capsys):
        """Should save credentials after successful login."""
        from src.cli import cmd_login

        creds_file = tmp_path / "credentials.json"

        with (
            patch("src.cli.BringClient") as mock_cls,
            patch("builtins.input", return_value="test@example.com"),
            patch("getpass.getpass", return_value="secret123"),
        ):
            mock_instance = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_instance
            mock_instance.get_lists.return_value = [MagicMock()]

            args = MagicMock(credentials=str(creds_file))
            await cmd_login(args)

        assert creds_file.exists()
        data = json.loads(creds_file.read_text())
        assert data["email"] == "test@example.com"
        assert data["password"] == "secret123"

        captured = capsys.readouterr()
        assert "Success" in captured.out

    @pytest.mark.asyncio
    async def test_cmd_list_not_found(self, mock_client, mock_credentials, capsys):
        """Should exit with error if list name not found."""

        from src.cli import cmd_list

        mock_client.find_list_by_name.return_value = None

        args = MagicMock(credentials=str(mock_credentials))
        args.name = "Nonexistent"

        with pytest.raises(SystemExit) as exc_info:
            await cmd_list(args)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err

    @pytest.mark.asyncio
    async def test_load_credentials_missing_file(self, tmp_path, capsys):
        """Should exit with error message when credentials file missing."""
        from src.cli import load_credentials

        missing_file = tmp_path / "missing.json"

        with pytest.raises(SystemExit) as exc_info:
            load_credentials(missing_file)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No credentials found" in captured.err
        assert "bring-cli login" in captured.err
