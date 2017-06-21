import json
from os.path import join

from django.conf import settings
from django.http import HttpResponse, JsonResponse


def json_static_view(request, filename):
    data = json.loads(
        open(join(settings.STATICFILES_DIRS[0], '{}.json'.format(filename))).read()
        )
    return JsonResponse(data, safe=False)


def js_static_view(request, filename):
    data = open(join(settings.STATICFILES_DIRS[0], '{}.js'.format(filename))).read()
    return HttpResponse(data, content_type="text/javascript")


def favicon_view(request):
    return HttpResponse(
        open(join(settings.STATICFILES_DIRS[0], 'favicon.ico'), 'rb'),
        content_type='image/x-icon'
        )
