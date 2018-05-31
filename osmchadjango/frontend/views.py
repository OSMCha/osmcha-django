import json
from os.path import join

from django.conf import settings
from django.http import HttpResponse, JsonResponse


def service_worker_view(request):
    data = open(join(settings.STATICFILES_DIRS[0], 'service-worker.js')).read()
    return HttpResponse(data, content_type="text/javascript")


def favicon_view(request):
    return HttpResponse(
        open(join(settings.STATICFILES_DIRS[0], 'favicon.ico'), 'rb'),
        content_type='image/x-icon'
        )
