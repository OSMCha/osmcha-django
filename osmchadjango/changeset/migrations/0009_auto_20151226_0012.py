# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0008_changeset_uid'),
    ]

    operations = [
        migrations.AddField(
            model_name='changeset',
            name='harmfull',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='powerfull_editor',
            field=models.BooleanField(default=False, verbose_name='Powerfull Editor'),
        ),
    ]
