#-*- coding: utf-8 -*-
from __future__ import absolute_import
import os

from django.conf import settings

from celery import Celery


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

app = Celery('config',
    backend='rpc://',
    broker=settings.BROKER_URL
    )

app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=10000,
)

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
