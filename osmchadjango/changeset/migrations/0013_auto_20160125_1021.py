# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0012_auto_20160125_1019'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changeset',
            name='user',
            field=models.CharField(max_length=1000, db_index=True),
        ),
    ]
