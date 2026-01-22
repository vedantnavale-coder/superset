# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# OPTIMIZED FOR HIGH PERFORMANCE: 32GB RAM + 32 CORE CPU
#
import logging
import os
import sys

from celery.schedules import crontab
from flask_caching.backends.redis import RedisCache

logger = logging.getLogger()

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_DIALECT = os.getenv("DATABASE_DIALECT", "postgresql")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_DB = os.getenv("DATABASE_DB")

EXAMPLES_USER = os.getenv("EXAMPLES_USER")
EXAMPLES_PASSWORD = os.getenv("EXAMPLES_PASSWORD")
EXAMPLES_HOST = os.getenv("EXAMPLES_HOST")
EXAMPLES_PORT = os.getenv("EXAMPLES_PORT", "5432")
EXAMPLES_DB = os.getenv("EXAMPLES_DB")

# SQLAlchemy connection string with pool optimization
SQLALCHEMY_DATABASE_URI = (
    f"{DATABASE_DIALECT}://"
    f"{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DB}"
)

# Examples database URI
SQLALCHEMY_EXAMPLES_URI = os.getenv(
    "SUPERSET__SQLALCHEMY_EXAMPLES_URI",
    (
        f"{DATABASE_DIALECT}://"
        f"{EXAMPLES_USER}:{EXAMPLES_PASSWORD}@"
        f"{EXAMPLES_HOST}:{EXAMPLES_PORT}/{EXAMPLES_DB}"
    ),
)

# ============================================================================
# DATABASE POOL OPTIMIZATION (32 core system)
# ============================================================================
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,                    # Connections in pool
    "max_overflow": 40,                 # Additional overflow connections
    "pool_pre_ping": True,              # Test connections before using
    "pool_recycle": 3600,               # Recycle connections every hour
    "echo": False,                      # Disable SQL logging for performance
    "connect_args": {
        "connect_timeout": 10,
        "options": "-c work_mem=256MB",  # PostgreSQL work memory
    }
}

EXAMPLES_SQLALCHEMY_ENGINE_OPTIONS = SQLALCHEMY_ENGINE_OPTIONS

# ============================================================================
# REDIS CONFIGURATION (HIGH PERFORMANCE)
# ============================================================================
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_CELERY_DB = int(os.getenv("REDIS_CELERY_DB", "0"))
REDIS_RESULTS_DB = int(os.getenv("REDIS_RESULTS_DB", "1"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

REDIS_SOCKET_CONNECT_TIMEOUT = 5
REDIS_SOCKET_KEEPALIVE = True
REDIS_SOCKET_KEEPALIVE_INTERVAL = 30

# ============================================================================
# CACHING CONFIGURATION (Redis-based, in-memory for speed)
# ============================================================================
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 600,       # Increased from 300s
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": REDIS_RESULTS_DB,
    "CACHE_REDIS_URL": f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}",
    "CACHE_REDIS_SSL": False,
}

DATA_CACHE_CONFIG = CACHE_CONFIG
THUMBNAIL_CACHE_CONFIG = CACHE_CONFIG

# ============================================================================
# CELERY CONFIGURATION (32 cores optimization)
# ============================================================================
class CeleryConfig:
    broker_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    result_backend = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"
    
    # Imports for task modules
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
        "superset.tasks.thumbnails",
        "superset.tasks.cache",
    )
    
    # Worker configuration for 32 cores
    worker_concurrency = 32              # Match core count
    worker_prefetch_multiplier = 4       # Optimize task distribution
    worker_max_tasks_per_child = 1000    # Prevent memory bloat
    worker_disable_rate_limits = False
    task_acks_late = True                # Acknowledge after completion
    task_reject_on_worker_lost = True    # Requeue on worker loss
    task_track_started = True            # Track task progress
    
    # Performance tuning
    broker_connection_retry_on_startup = True
    broker_connection_retry = True
    broker_connection_max_retries = 10
    
    # Beat scheduler configuration
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*/5", hour="*"),  # Run every 5 minutes
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": crontab(minute=10, hour=0),       # Daily at 00:10
        },
        "cache.warming": {
            "task": "superset.tasks.cache.warm_cache",
            "schedule": crontab(minute=0, hour="*/2"),    # Every 2 hours
        },
    }

CELERY_CONFIG = CeleryConfig

# ============================================================================
# ALERT & REPORTS CONFIGURATION
# ============================================================================
ALERT_REPORTS_NOTIFICATION_DRY_RUN = False  # Enable in production
REPORT_QUEUE_WORKERS = 4                     # Dedicated report processing workers

WEBDRIVER_BASEURL = f"http://superset_app{os.environ.get('SUPERSET_APP_ROOT', '/')}/"
WEBDRIVER_BASEURL_USER_FRIENDLY = (
    f"http://localhost:8888/{os.environ.get('SUPERSET_APP_ROOT', '/')}/"
)

SCREENSHOT_LOAD_TIMEOUT = 30                 # Timeout for screenshots
SCREENSHOT_SELENIUM_HEADLESS = True

# ============================================================================
# SQL LAB CONFIGURATION
# ============================================================================
SQLLAB_CTAS_NO_LIMIT = True
SQLLAB_TIMEOUT = 300                         # Query timeout in seconds
SQLLAB_DEFAULT_DBID = 1                      # Default database ID

# Query result caching
RESULTS_BACKEND = None                       # Use Redis instead of filesystem
RESULTS_BACKEND_USE_MSGPACK = True           # Faster serialization

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
log_level_text = os.getenv("SUPERSET_LOG_LEVEL", "WARNING")
LOG_LEVEL = getattr(logging, log_level_text.upper(), logging.INFO)

# ============================================================================
# FLASK & SERVER CONFIGURATION
# ============================================================================
FLASK_ENV = os.getenv("FLASK_ENV", "production")

# Gunicorn worker configuration (for 32 cores)
SUPERSET_WORKERS = 16                        # Flask app workers
SUPERSET_WORKER_CLASS = "gthread"            # Threaded workers for better concurrency
SUPERSET_THREADS = 2                         # Threads per worker
SUPERSET_TIMEOUT = 60
SUPERSET_KEEPALIVE = 5

# ============================================================================
# ENABLE CORS & EMBEDDED SUPERSET
# ============================================================================
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "origins": "*",
    "allow_headers": "*",
    "expose_headers": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
}

# ============================================================================
# SECURITY & SESSION CONFIGURATION
# ============================================================================
TALISMAN_ENABLED = False
SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
PERMANENT_SESSION_LIFETIME = 86400           # 24 hours

OVERRIDE_TALISMAN_CONFIG = {
    "content_security_policy": {
        "frame-ancestors": ["*"]
    },
    "force_https": False,
}

# ============================================================================
# FEATURE FLAGS & PERFORMANCE
# ============================================================================
FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "EMBEDDED_SUPERSET": True,
    "ENABLE_JAVASCRIPT_CONTROLS": True,
    "PRESTO_EXPAND_DATA": False,              # Reduce memory usage
    "SHARE_QUERIES_VIA_KV_STORE": True,       # Better query sharing
    "ALLOW_FULL_CSV_EXPORT": True,
}

# ============================================================================
# GUEST TOKEN CONFIGURATION
# ============================================================================
GUEST_ROLE_NAME = "Gamma"
SUPERSET_GUEST_SECRET = os.getenv("SUPERSET_GUEST_SECRET", "x3q9YVcz6RNO6vqtAJvCtld8jVSNNScS0")
GUEST_TOKEN_JWT_ALGORITHM = "HS256"
GUEST_TOKEN_JWT_EXP_SECONDS = 3600

# ============================================================================
# OPTIONAL: IMPORT CUSTOM DOCKER CONFIG (for overrides)
# ============================================================================
if os.getenv("CYPRESS_CONFIG") == "true":
    base_dir = os.path.dirname(__file__)
    module_folder = os.path.abspath(
        os.path.join(base_dir, "../../tests/integration_tests/")
    )
    sys.path.insert(0, module_folder)
    try:
        from superset_test_config import *  # noqa
    except ImportError:
        logger.warning("Cypress test config not found")
    sys.path.pop(0)

try:
    import superset_config_docker
    from superset_config_docker import *  # noqa: F403
    logger.info("Loaded Docker configuration at [%s]", superset_config_docker.__file__)
except ImportError:
    logger.info("Using optimized Docker config...")