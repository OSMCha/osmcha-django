# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0007_auto_20150828_1947'),
    ]

    operations = [
        migrations.AddField(
            model_name='changeset',
            name='uid',
            field=models.CharField(default='00', verbose_name='User ID', max_length=255),
            preserve_default=False,
        ),
    ]
