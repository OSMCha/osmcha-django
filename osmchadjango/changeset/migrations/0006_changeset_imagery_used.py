# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0005_auto_20150828_1942'),
    ]

    operations = [
        migrations.AddField(
            model_name='changeset',
            name='imagery_used',
            field=models.CharField(max_length=1000, blank=True),
        ),
    ]
