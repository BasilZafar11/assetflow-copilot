"""Read-only AssetFlow inventory MCP server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.core.config import get_settings  # noqa: F401 (validates config loads)
from app.services import assetflow_api as api

mcp = FastMCP("AssetFlow Copilot")


@mcp.tool()
async def lookup_asset(tag: str) -> str:
    """Look up an asset by tag without exposing holder contact details."""
    asset = await api.get_asset(tag)
    if not asset:
        return f"Asset '{tag}' not found or the inventory API is unavailable."

    category = asset.get("Category") or {}
    holder = asset.get("CurrentHolder") or {}
    lines = [
        f"Tag: {asset.get('tag', 'N/A')}",
        f"Name: {asset.get('name', 'N/A')}",
        f"Status: {asset.get('status', 'N/A')}",
        f"Category: {category.get('name', 'N/A')}",
        f"Holder: {holder.get('name', 'None') if holder else 'Unassigned'}",
        f"Location: {asset.get('location', 'N/A')}",
        f"Condition: {asset.get('condition', 'N/A')}",
    ]
    return "\n".join(lines)


@mcp.tool()
async def search_available_assets(
    category: str | None = None,
    search: str | None = None,
) -> str:
    """Search available inventory by category or search term."""
    category_id: int | None = None
    if category:
        categories = await api.get_categories()
        if not categories:
            return "Could not retrieve asset categories."
        for item in categories:
            if item.get("name", "").casefold() == category.casefold():
                category_id = item.get("id")
                break
        if category_id is None:
            return f"Category '{category}' not found."

    assets = await api.list_assets(
        status="Available", category_id=category_id, search=search
    )
    if assets is None:
        return "Could not retrieve available assets."
    if not assets:
        return "No available assets found."

    lines = []
    for asset in assets[:20]:
        category_name = (asset.get("Category") or {}).get("name", "N/A")
        lines.append(
            f"- {asset.get('tag', 'N/A')} | {asset.get('name', 'N/A')} | "
            f"{category_name} | {asset.get('location', 'N/A')}"
        )
    return f"Available assets ({len(assets)}):\n" + "\n".join(lines)
