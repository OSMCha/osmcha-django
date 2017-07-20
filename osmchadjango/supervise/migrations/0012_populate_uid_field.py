# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def get_uid(apps, username):
    Changeset = apps.get_model('changeset', 'Changeset')
    last_changeset = Changeset.objects.filter(user=username).last()
    if last_changeset is not None:
        return Changeset.objects.filter(user=username).last().uid
    else:
        return None


def populate_uid(apps, schema_editor):
    BlacklistedUser = apps.get_model('supervise', 'BlacklistedUser')
    for row in BlacklistedUser.objects.all():
        row.uid = get_uid(apps, row.username)
        row.save(update_fields=['uid'])


class Migration(migrations.Migration):

    dependencies = [
        ('supervise', '0011_auto_20170720_1914'),
        ]

    operations = [
        migrations.RunPython(
            populate_uid,
            reverse_code=migrations.RunPython.noop
            ),
        ]
