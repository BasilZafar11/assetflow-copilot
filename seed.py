"""Initialize the local schema without inserting real or demo user data."""

import asyncio

from app.db.database import init_db


async def seed() -> None:
    await init_db()
    print("Database schema initialized.")

if __name__ == "__main__":
    asyncio.run(seed())
