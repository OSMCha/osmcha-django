from django.contrib import admin

from .models import Priority


admin.site.register(Priority, admin.ModelAdmin)
