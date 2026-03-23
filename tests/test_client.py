"""Tests for client.py — credential management and BringClient wrapper."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.client import BringClient, BringCredentials


class TestBringCredentials:
    """Test credential loading and saving."""

    def test_from_file_success(self, tmp_path: Path):
        """Should load credentials from valid JSON file."""
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"email": "test@example.com", "password": "secret123"}))

        credentials = BringCredentials.from_file(creds_file)

        assert credentials.email == "test@example.com"
        assert credentials.password == "secret123"

    def test_from_file_not_found(self, tmp_path: Path):
        """Should raise FileNotFoundError if file doesn't exist."""
        creds_file = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError, match="Credentials file not found"):
            BringCredentials.from_file(creds_file)

    def test_save_creates_directory(self, tmp_path: Path):
        """Should create parent directories when saving."""
        creds_file = tmp_path / "config" / "bring" / "credentials.json"
        credentials = BringCredentials(email="test@example.com", password="secret123")

        credentials.save(creds_file)

        assert creds_file.exists()
        assert creds_file.stat().st_mode & 0o777 == 0o600  # Secure permissions

    def test_save_content(self, tmp_path: Path):
        """Should save credentials as JSON."""
        creds_file = tmp_path / "credentials.json"
        credentials = BringCredentials(email="test@example.com", password="secret123")

        credentials.save(creds_file)

        data = json.loads(creds_file.read_text())
        assert data == {"email": "test@example.com", "password": "secret123"}


class TestBringClient:
    """Test BringClient wrapper around bring-api."""

    @pytest.fixture
    def credentials(self) -> BringCredentials:
        """Fixture for test credentials."""
        return BringCredentials(email="test@example.com", password="secret123")

    @pytest.mark.asyncio
    async def test_context_manager_initializes_session(self, credentials: BringCredentials):
        """Should initialize aiohttp session and login via bring-api."""
        with patch("src.client.aiohttp.ClientSession") as mock_session_cls, patch("src.client.Bring") as mock_bring_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value = mock_session

            mock_bring = AsyncMock()
            mock_bring_cls.return_value = mock_bring

            async with BringClient(credentials) as client:
                assert client._session is not None
                mock_bring.login.assert_awaited_once()

            mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_lists(self, credentials: BringCredentials):
        """Should fetch all shopping lists."""
        with patch("src.client.aiohttp.ClientSession") as mock_session_cls, patch("src.client.Bring") as mock_bring_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value = mock_session

            mock_bring = AsyncMock()
            mock_bring_cls.return_value = mock_bring

            mock_list_1 = MagicMock()
            mock_list_1.name = "Home"
            mock_list_1.listUuid = "uuid-1"

            mock_list_2 = MagicMock()
            mock_list_2.name = "Work"
            mock_list_2.listUuid = "uuid-2"

            mock_response = MagicMock()
            mock_response.lists = [mock_list_1, mock_list_2]
            mock_bring.load_lists.return_value = mock_response

            async with BringClient(credentials) as client:
                lists = await client.get_lists()

            assert len(lists) == 2
            assert lists[0].name == "Home"

    @pytest.mark.asyncio
    async def test_find_list_by_name_case_insensitive(self, credentials: BringCredentials):
        """Should find list by partial case-insensitive match."""
        with patch("src.client.aiohttp.ClientSession") as mock_session_cls, patch("src.client.Bring") as mock_bring_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value = mock_session

            mock_bring = AsyncMock()
            mock_bring_cls.return_value = mock_bring

            mock_list_1 = MagicMock()
            mock_list_1.name = "Home Shopping"
            mock_list_1.listUuid = "uuid-1"

            mock_list_2 = MagicMock()
            mock_list_2.name = "Work"
            mock_list_2.listUuid = "uuid-2"

            mock_response = MagicMock()
            mock_response.lists = [mock_list_1, mock_list_2]
            mock_bring.load_lists.return_value = mock_response

            async with BringClient(credentials) as client:
                found = await client.find_list_by_name("home")

            assert found is not None
            assert found.name == "Home Shopping"

    @pytest.mark.asyncio
    async def test_find_list_by_name_not_found(self, credentials: BringCredentials):
        """Should return None if list not found."""
        with patch("src.client.aiohttp.ClientSession") as mock_session_cls, patch("src.client.Bring") as mock_bring_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value = mock_session

            mock_bring = AsyncMock()
            mock_bring_cls.return_value = mock_bring

            mock_list = MagicMock()
            mock_list.name = "Home"
            mock_list.listUuid = "uuid-1"

            mock_response = MagicMock()
            mock_response.lists = [mock_list]
            mock_bring.load_lists.return_value = mock_response

            async with BringClient(credentials) as client:
                found = await client.find_list_by_name("nonexistent")

            assert found is None

    @pytest.mark.asyncio
    async def test_get_default_list(self, credentials: BringCredentials):
        """Should return first list as default."""
        with patch("src.client.aiohttp.ClientSession") as mock_session_cls, patch("src.client.Bring") as mock_bring_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value = mock_session

            mock_bring = AsyncMock()
            mock_bring_cls.return_value = mock_bring

            mock_list_1 = MagicMock()
            mock_list_1.name = "Home"
            mock_list_1.listUuid = "uuid-1"

            mock_list_2 = MagicMock()
            mock_list_2.name = "Work"
            mock_list_2.listUuid = "uuid-2"

            mock_response = MagicMock()
            mock_response.lists = [mock_list_1, mock_list_2]
            mock_bring.load_lists.return_value = mock_response

            async with BringClient(credentials) as client:
                default = await client.get_default_list()

            assert default.name == "Home"

    @pytest.mark.asyncio
    async def test_add_item(self, credentials: BringCredentials):
        """Should add item via bring-api save_item."""
        with patch("src.client.aiohttp.ClientSession") as mock_session_cls, patch("src.client.Bring") as mock_bring_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value = mock_session

            mock_bring = AsyncMock()
            mock_bring_cls.return_value = mock_bring

            async with BringClient(credentials) as client:
                await client.add_item("uuid-1", "Eggs", "x12")

            mock_bring.save_item.assert_awaited_once_with("uuid-1", "Eggs", "x12")

    @pytest.mark.asyncio
    async def test_remove_item(self, credentials: BringCredentials):
        """Should remove item via bring-api remove_item."""
        with patch("src.client.aiohttp.ClientSession") as mock_session_cls, patch("src.client.Bring") as mock_bring_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value = mock_session

            mock_bring = AsyncMock()
            mock_bring_cls.return_value = mock_bring

            async with BringClient(credentials) as client:
                await client.remove_item("uuid-1", "Eggs")

            mock_bring.remove_item.assert_awaited_once_with("uuid-1", "Eggs")

    @pytest.mark.asyncio
    async def test_complete_item(self, credentials: BringCredentials):
        """Should mark item complete via bring-api complete_item."""
        with patch("src.client.aiohttp.ClientSession") as mock_session_cls, patch("src.client.Bring") as mock_bring_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value = mock_session

            mock_bring = AsyncMock()
            mock_bring_cls.return_value = mock_bring

            async with BringClient(credentials) as client:
                await client.complete_item("uuid-1", "Eggs")

            mock_bring.complete_item.assert_awaited_once_with("uuid-1", "Eggs")

    @pytest.mark.asyncio
    async def test_clear_list(self, credentials: BringCredentials):
        """Should remove all items from list."""
        with patch("src.client.aiohttp.ClientSession") as mock_session_cls, patch("src.client.Bring") as mock_bring_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value = mock_session

            mock_bring = AsyncMock()
            mock_bring_cls.return_value = mock_bring

            mock_items = MagicMock()
            mock_items.purchase = [
                MagicMock(itemId="Eggs"),
                MagicMock(itemId="Butter"),
            ]
            mock_response = MagicMock(items=mock_items)
            mock_bring.get_list.return_value = mock_response

            async with BringClient(credentials) as client:
                await client.clear_list("uuid-1")

            assert mock_bring.remove_item.await_count == 2
            mock_bring.remove_item.assert_any_await("uuid-1", "Eggs")
            mock_bring.remove_item.assert_any_await("uuid-1", "Butter")
