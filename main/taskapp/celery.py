# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from django.conf import settings
from django.apps import AppConfig
from celery import Celery
from celery.utils.log import get_task_logger
import os

logger = get_task_logger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

app = Celery('main', backend=REDIS_URL, broker=REDIS_URL)

DEFAULT_RETRY_DELAY = 5  # 15 seconds
MAX_RETRIES = 5
CELERY_TIMEZONE = settings.TIME_ZONE  # "Etc/GMT-3" or "Europe/Istanbul"
CELERY_ENABLE_UTC = False


@app.task(bind=True)
def debug_task(self):
	print('Request: {0!r}'.format(self.request))  # pragma: no cover


def revoke_task(task_id):
	app.control.revoke(task_id)


def clear_tasks():
	return app.control.purge()
