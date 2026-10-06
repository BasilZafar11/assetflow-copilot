"""
Overdue asset recovery daemon.
Checks for overdue allocations and sends Slack DM reminders.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from slack_sdk.web.async_client import AsyncWebClient

from app.core.config import settings
from app.db.database import AsyncSessionLocal, OverdueReminder, UserMapping
from app.services import assetflow_api as api
from app.bot.slack_app import build_overdue_dm

logger = logging.getLogger(__name__)


def _allocation_key(allocation: dict) -> str | None:
    allocation_id = allocation.get("id")
    if allocation_id is not None:
        return f"allocation:{allocation_id}"
    asset_tag = (allocation.get("Asset") or {}).get("tag")
    user_id = (allocation.get("User") or {}).get("id")
    due_date = allocation.get("expected_return_date")
    if asset_tag and user_id is not None and due_date:
        return f"asset:{asset_tag}|user:{user_id}|due:{due_date}"
    return None


async def _recently_notified(allocation_key: str) -> bool:
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(OverdueReminder).where(
                OverdueReminder.allocation_key == allocation_key
            )
        )
        reminder = result.scalar_one_or_none()
    if reminder is None:
        return False
    notified_at = reminder.notified_at
    if notified_at.tzinfo is None:
        notified_at = notified_at.replace(tzinfo=timezone.utc)
    cooldown = timedelta(hours=settings.overdue_reminder_cooldown_hours)
    return datetime.now(timezone.utc) - notified_at < cooldown


async def _mark_notified(allocation_key: str) -> None:
    async with AsyncSessionLocal() as session:
        await session.merge(
            OverdueReminder(
                allocation_key=allocation_key,
                notified_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()


async def check_and_notify_overdue():
    """Fetch overdue allocations from AssetFlow, send DM to each holder."""
    overdue = await api.get_overdue_allocations()
    if overdue is None:
        logger.warning("Overdue allocations could not be loaded")
        return
    if not overdue:
        logger.info("No overdue allocations found.")
        return

    client = AsyncWebClient(token=settings.slack_bot_token)
    logger.info("Found %d overdue allocation(s).", len(overdue))

    for alloc in overdue:
        reminder_key = _allocation_key(alloc)
        if not reminder_key:
            logger.warning("Skipping overdue allocation without a stable identifier")
            continue
        if await _recently_notified(reminder_key):
            continue

        user_data = alloc.get("User") or {}
        asset_data = alloc.get("Asset") or {}
        af_user_id = user_data.get("id")
        due_date = alloc.get("expected_return_date", "Unknown")

        if not af_user_id:
            continue

        # Look up Slack user ID from mapping
        from sqlalchemy import select
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserMapping).where(UserMapping.assetflow_user_id == af_user_id)
            )
            mapping = result.scalar_one_or_none()

        if not mapping:
            logger.warning("No Slack mapping for AssetFlow user %d", af_user_id)
            continue

        # Send overdue DM
        blocks = build_overdue_dm(
            asset_name=asset_data.get("name", "Unknown"),
            asset_tag=asset_data.get("tag", "?"),
            due_date=due_date,
        )

        try:
            await client.chat_postMessage(
                channel=mapping.slack_user_id,
                blocks=blocks,
                text=f"⚠️ Overdue: {asset_data.get('name', '?')} ({asset_data.get('tag', '?')}) was due {due_date}",
            )
            await _mark_notified(reminder_key)
            logger.info("Sent overdue reminder to %s for %s", mapping.slack_user_id, asset_data.get("tag"))
        except Exception:
            logger.exception("Failed to send overdue DM to %s", mapping.slack_user_id)



async def run_daemon(interval_seconds: int = 3600):
    """Run overdue check on a loop."""
    logger.info("Overdue daemon started (interval=%ds)", interval_seconds)
    while True:
        try:
            await check_and_notify_overdue()
        except Exception:
            logger.exception("Overdue daemon error")
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(check_and_notify_overdue())
