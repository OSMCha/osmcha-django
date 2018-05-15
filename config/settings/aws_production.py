# -*- coding: utf-8 -*-
'''
Production Configurations using AWS ELB
- Use djangosecure
- Use MEMCACHE on Heroku
'''
from __future__ import absolute_import, unicode_literals

from .common import *  # noqa


# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Raises ImproperlyConfigured exception if DJANO_SECRET_KEY not in os.environ
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dont.forget-to-set-the-env-var")

# This ensures that Django will be able to detect a secure connection
# properly on Heroku.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# gunicorn
# ------------------------------------------------------------------------------
INSTALLED_APPS += ('gunicorn',)


# SITE CONFIGURATION
# ------------------------------------------------------------------------------
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.6/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]
# END SITE CONFIGURATION


# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
# DATABASES = {
#     'default': env.db('DATABASE_URL', default='postgres:///osmcha'),
# }
DATABASES = {
    'default': {
         'ENGINE': 'django.contrib.gis.db.backends.postgis',
         'NAME': 'osmcha',
         'USER': env('POSTGRES_USER'),
         'PASSWORD': env('POSTGRES_PASSWORD'),
         'HOST': env('PGHOST', default='localhost')
     }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': env('ANON_USER_THROTTLE_RATE', default='30/min'),
        'user': env('COMMON_USER_THROTTLE_RATE', default='180/min'),
        'non_staff_user': env('NON_STAFF_USER_THROTTLE_RATE', default='3/min')
        },
    'ORDERING_PARAM': 'order_by',
    }

# CACHALOT SETTINGS
CACHALOT_ENABLED = False
