from celery import Celery

from app.config import settings

celery_app = Celery(
    "call_quality_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.analysis"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=1800,  # 30 minutes max per task
    task_soft_time_limit=1500,  # 25 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,

    # Result backend settings
    result_expires=86400,  # 24 hours

    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Rate limiting
    task_annotations={
        "app.tasks.analysis.process_single_call": {
            "rate_limit": "10/m",  # 10 per minute (respect Biztel rate limit)
        },
    },

    # Beat schedule for periodic tasks
    beat_schedule={
        "daily-biztel-sync": {
            "task": "app.tasks.analysis.daily_biztel_sync",
            "schedule": 60 * 60 * 24,  # Every 24 hours (configured via Cloud Scheduler)
        },
        "cleanup-expired-files": {
            "task": "app.tasks.analysis.cleanup_expired_files",
            "schedule": 60 * 60 * 6,  # Every 6 hours
        },
    },
)
