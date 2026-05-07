"""Celery application — workers + beat scheduler."""
from __future__ import annotations
from celery import Celery
from celery.schedules import crontab
from .core.config import settings

celery = Celery("the_market_lion", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "tasks.news.*": {"queue": "news"},
        "tasks.indicators.*": {"queue": "indicators"},
        "tasks.schools.*": {"queue": "schools"},
        "tasks.flow.*": {"queue": "flow"},
        "tasks.voting.*": {"queue": "voting"},
        "tasks.execution.*": {"queue": "execution"},
    },
    beat_schedule={
        "ingest-news-every-5min": {
            "task": "tasks.news.ingest_all",
            "schedule": crontab(minute="*/5"),
        },
        "ingest-twitter-every-1min": {
            "task": "tasks.news.ingest_twitter",
            "schedule": crontab(minute="*"),
        },
        "ingest-econ-events-hourly": {
            "task": "tasks.news.ingest_econ_calendar",
            "schedule": crontab(minute=0),
        },
        "compute-confluence-1min": {
            "task": "tasks.voting.recompute_all",
            "schedule": crontab(minute="*"),
        },
        "rl-learning-after-trade": {
            "task": "tasks.voting.run_rl_loop",
            "schedule": crontab(hour="*/6"),
        },
    },
)

# auto-discover tasks
celery.autodiscover_tasks(["app.workers"])
