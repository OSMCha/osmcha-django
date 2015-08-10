from django.contrib.gis import admin

from .models import Changeset


class ChangesetAdmin(admin.OSMGeoAdmin):
    search_fields = ['id']
    list_display = ['id', 'user', 'created', 'modified', 'deleted', 'checked',
        'check_user']
    list_filter = ['checked', 'editor', 'harmful']
    date_hierarchy = 'date'


admin.site.register(Changeset, ChangesetAdmin)