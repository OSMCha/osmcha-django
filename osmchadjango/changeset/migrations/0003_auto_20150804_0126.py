# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0002_auto_20150804_0119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changeset',
            name='check_user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, on_delete=models.deletion.SET_NULL, null=True),
        ),
    ]
