"""Shared helpers for Celery tasks: sync DB session, Redis pub/sub for SSE."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_settings = get_settings()
_engine = create_engine(_settings.sync_database_url, pool_pre_ping=True, future=True)
SyncSession = sessionmaker(_engine, expire_on_commit=False, class_=Session)

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(_settings.redis_url)
    return _redis_client


@contextmanager
def db_session() -> Iterator[Session]:
    s = SyncSession()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def publish_progress(deck_id: str, stage: str, progress_pct: int = 0, **extra: Any) -> None:
    payload = {"stage": stage, "progress_pct": progress_pct, **extra}
    data = json.dumps(payload)
    r = _get_redis()
    r.publish(f"job:{deck_id}", data)
    r.setex(f"job:{deck_id}:last", 600, data)
