import logging
import os
import sys
from datetime import timedelta
from celery.schedules import crontab

logger = logging.getLogger()

# --- Database Connection Settings ---
DATABASE_DIALECT = os.getenv("DATABASE_DIALECT")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_DB = os.getenv("DATABASE_DB")

SQLALCHEMY_DATABASE_URI = (
    f"{DATABASE_DIALECT}://"
    f"{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DB}"
)

# --- Redis & Caching Configuration (Optimized for Speed) ---
# We use different Redis DB numbers (0, 1, 2, 3, 4) to prevent data collision
REDIS_HOST = "superset_cache"
REDIS_PORT = "6379"

# 1. Metadata Cache (Dashboard & Slice info)
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400, # 24 hours
    'CACHE_KEY_PREFIX': 'superset_metadata_',
    'CACHE_REDIS_URL': f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
}

# 2. Chart Data Cache (The actual MySQL query results) - CRITICAL FOR SPEED
DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 3600, # 1 hour
    'CACHE_KEY_PREFIX': 'superset_data_',
    'CACHE_REDIS_URL': f'redis://{REDIS_HOST}:{REDIS_PORT}/1'
}

# 3. Filter State Cache (Speeds up dashboard interactions)
FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_',
    'CACHE_REDIS_URL': f'redis://{REDIS_HOST}:{REDIS_PORT}/2'
}

# 4. SQL Lab Results Cache
RESULTS_BACKEND_USE_REDIS = True
RESULTS_BACKEND = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_results_',
    'CACHE_REDIS_URL': f'redis://{REDIS_HOST}:{REDIS_PORT}/5'
}

# --- Celery Configuration (Async Query Execution) ---
class CeleryConfig:
    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/3"
    result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/4"
    worker_prefetch_multiplier = 10 # High value for 32 cores
    task_acks_late = True
    task_time_limit = 600
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
        "superset.tasks.thumbnails",
        "superset.tasks.cache",
        "superset.tasks.async_queries",
    )
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": crontab(minute=10, hour=0),
        },
    }

CELERY_CONFIG = CeleryConfig

# --- Feature Flags ---
FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "EMBEDDED_SUPERSET": True,
    "GLOBAL_ASYNC_QUERIES": True,
    "DASHBOARD_VIRTUALIZATION": True, # Loads charts only when visible
    "DRILL_TO_DETAIL": True,
    "ALERTS_ATTACH_REPORTS": True,
}

# --- Security & Embedding Settings ---
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "origins": ["*"],
    "allow_headers": ["*"],
    "expose_headers": ["*"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
}

# Required for Embedding
SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True 
SESSION_COOKIE_HTTPONLY = True
TALISMAN_ENABLED = False # Disabled for local/embed flexibility

# --- General Server Settings ---
SQLLAB_CTAS_NO_LIMIT = True
GUEST_ROLE_NAME = "Gamma"
SUPERSET_WEBSERVER_TIMEOUT = 300