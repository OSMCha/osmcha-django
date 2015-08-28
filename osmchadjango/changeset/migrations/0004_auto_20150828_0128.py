# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0003_auto_20150804_0126'),
    ]

    operations = [
        migrations.AddField(
            model_name='changeset',
            name='powerfull_editor',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='changeset',
            name='source',
            field=models.CharField(max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='comment',
            field=models.CharField(max_length=1000, blank=True),
        ),
    ]
