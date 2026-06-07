"""Celery application."""

from __future__ import annotations

from celery import Celery

from app.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "present_yourself",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
    include=[
        "app.tasks.generate",
        "app.tasks.export_pptx",
        "app.tasks.template_extract",
    ],
)

celery_app.conf.update(
    task_default_queue="generate",
    task_queues=("generate", "export", "render"),
    task_routes={
        "app.tasks.generate.*": {"queue": "generate"},
        "app.tasks.export_pptx.*": {"queue": "export"},
        "app.tasks.template_extract.*": {"queue": "render"},
    },
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)
