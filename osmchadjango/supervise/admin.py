from django.contrib.gis import admin

from .models import AreaOfInterest


admin.site.register(AreaOfInterest, admin.GeoModelAdmin)
