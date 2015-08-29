from django.contrib.gis import admin

from .models import Changeset, SuspicionReasons


class ChangesetAdmin(admin.OSMGeoAdmin):
    search_fields = ['id']
    list_display = ['id', 'user', 'create', 'modify', 'delete', 'checked',
        'date', 'check_user']
    list_filter = ['checked', 'editor', 'is_suspect']
    date_hierarchy = 'date'


admin.site.register(Changeset, ChangesetAdmin)
admin.site.register(SuspicionReasons, admin.ModelAdmin)