"""Client wrapper for bring-api with credential management."""

import json
from dataclasses import dataclass
from pathlib import Path

import aiohttp
from bring_api import Bring
from bring_api.types import BringList, Items


@dataclass
class BringCredentials:
    """Bring! account credentials."""

    email: str
    password: str

    @classmethod
    def from_file(cls, path: Path) -> "BringCredentials":
        """Load credentials from JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Credentials file not found: {path}")
        with open(path) as f:
            data = json.load(f)
        return cls(email=data["email"], password=data["password"])

    def save(self, path: Path) -> None:
        """Save credentials to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump({"email": self.email, "password": self.password}, f, indent=2)
        path.chmod(0o600)  # Secure permissions


class BringClient:
    """High-level client for Bring! shopping lists."""

    def __init__(self, credentials: BringCredentials):
        self.credentials = credentials
        self._session: aiohttp.ClientSession | None = None
        self._bring: Bring | None = None

    async def __aenter__(self) -> "BringClient":
        """Initialize session and authenticate."""
        self._session = aiohttp.ClientSession()
        self._bring = Bring(self._session, self.credentials.email, self.credentials.password)
        await self._bring.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session."""
        if self._session:
            await self._session.close()

    @property
    def bring(self) -> Bring:
        """Access underlying Bring API client."""
        if not self._bring:
            raise RuntimeError("Client not initialized — use async with context manager")
        return self._bring

    async def get_lists(self) -> list[BringList]:
        """Get all shopping lists."""
        response = await self.bring.load_lists()
        return response.lists

    async def find_list_by_name(self, name: str) -> BringList | None:
        """Find a list by name (case-insensitive partial match)."""
        lists = await self.get_lists()
        name_lower = name.lower()
        for lst in lists:
            if name_lower in lst.name.lower():
                return lst
        return None

    async def get_default_list(self) -> BringList:
        """Get the first available list (default)."""
        lists = await self.get_lists()
        if not lists:
            raise ValueError("No shopping lists found")
        return lists[0]

    async def get_list_items(self, list_uuid: str) -> Items:
        """Get items from a specific list."""
        response = await self.bring.get_list(list_uuid)
        return response.items

    async def add_item(self, list_uuid: str, item: str, specification: str = "") -> None:
        """Add an item to a list."""
        await self.bring.save_item(list_uuid, item, specification)

    async def remove_item(self, list_uuid: str, item: str) -> None:
        """Remove an item from a list."""
        await self.bring.remove_item(list_uuid, item)

    async def complete_item(self, list_uuid: str, item: str) -> None:
        """Mark an item as completed (check off)."""
        await self.bring.complete_item(list_uuid, item)

    async def clear_list(self, list_uuid: str) -> None:
        """Remove all items from a list."""
        items = await self.get_list_items(list_uuid)
        for purchase in items.purchase:
            await self.remove_item(list_uuid, purchase.itemId)
