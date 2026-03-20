"""
app/core/celery_app.py
Configuração central do Celery.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "df_remuneration_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

# Configurações adicionais
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=14400,  # 4 horas de limite máximo (hard limit)
    task_soft_time_limit=12600,  # 3.5 horas de limite suave (soft limit)
)

celery_app.conf.beat_schedule = {
    "sync-recent-years-daily": {
        "task": "sync_recent_years_task",
        "schedule": crontab(hour=3, minute=0),  # Diário às 03:00 AM
    },
}
