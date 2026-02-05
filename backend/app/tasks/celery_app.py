"""
Celery Application Configuration
"""
import os
from celery import Celery

# Redis URLを環境変数から取得
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "call_quality_dashboard",
    broker=redis_url,
    backend=redis_url,
    include=["app.tasks.analysis"],
)

# Celery設定
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1時間
    worker_prefetch_multiplier=1,
    # スケジュール設定（毎日AM3:00にバッチ処理）
    beat_schedule={
        "fetch-daily-calls": {
            "task": "app.tasks.analysis.fetch_daily_calls",
            "schedule": {
                "hour": 3,
                "minute": 0,
            },
        },
    },
)
