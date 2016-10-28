# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0014_auto_20160216_1029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdetail',
            name='name',
            field=models.CharField(unique=True, max_length=1000),
        ),
    ]
