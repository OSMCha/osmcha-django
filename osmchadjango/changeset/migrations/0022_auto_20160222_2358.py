# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0021_auto_20160222_2345'),
    ]

    operations = [
        migrations.AlterField(
            model_name='suspicionreasons',
            name='name',
            field=models.CharField(max_length=255, db_index=True),
        ),
    ]
