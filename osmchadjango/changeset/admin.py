from django.contrib.gis import admin

from .models import Changeset, SuspicionReasons, Tag


class ChangesetAdmin(admin.OSMGeoAdmin):
    search_fields = ['id']
    list_display = ['id', 'user', 'create', 'modify', 'delete', 'checked',
        'date', 'check_user']
    list_filter = ['checked', 'is_suspect', 'reasons']
    date_hierarchy = 'date'


class ReasonsAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'is_visible', 'for_changeset', 'for_feature']
    list_filter = ['is_visible', 'for_changeset', 'for_feature']


admin.site.register(Changeset, ChangesetAdmin)
admin.site.register(SuspicionReasons, ReasonsAdmin)
admin.site.register(Tag, ReasonsAdmin)
