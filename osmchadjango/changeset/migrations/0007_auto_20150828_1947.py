# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0006_changeset_imagery_used'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='changeset',
            name='harmful',
        ),
        migrations.AddField(
            model_name='changeset',
            name='is_suspect',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
