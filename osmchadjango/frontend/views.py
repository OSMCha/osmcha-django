from django.shortcuts import render
from django.conf import settings
from osmchadjango.changeset.models import Changeset

def filter_view(request):
    context = {
        'FRONTEND_JS_URL': settings.FRONTEND_JS_URL
    }
    return render(request, 'frontend/index.html', context)

def changeset_view(request, pk):
    context = {
        'FRONTEND_JS_URL': settings.FRONTEND_JS_URL,
        'changeset': Changeset.objects.get(pk=pk)
    }
    return render(request, 'frontend/changeset.html', context)