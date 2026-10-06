"""FastAPI entrypoint — mounts Slack Bolt async app."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import engine, init_db
from app.bot.slack_app import app as bolt_app
from app.bot.overdue_daemon import run_daemon
from app.services import assetflow_api as api

handler = AsyncSlackRequestHandler(bolt_app)
logger = logging.getLogger(__name__)
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    worker = None
    if settings.enable_overdue_worker:
        worker = asyncio.create_task(
            run_daemon(interval_seconds=settings.overdue_check_interval_seconds),
            name="overdue-reminder-worker",
        )
    try:
        yield
    finally:
        if worker is not None:
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                logger.info("Overdue reminder worker stopped")
        await api.close_client()
        await engine.dispose()


app = FastAPI(title="AssetFlow Copilot", lifespan=lifespan)


@app.get("/")
async def health():
    return {"status": "ok", "service": "assetflow-copilot"}


@app.post("/slack/events")
async def slack_events(request: Request):
    return await handler.handle(request)


@app.post("/slack/interactions")
async def slack_interactions(request: Request):
    return await handler.handle(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
