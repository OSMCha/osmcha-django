# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0025_suspiciousfeature'),
    ]

    operations = [
        migrations.AddField(
            model_name='changeset',
            name='score',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='score',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
