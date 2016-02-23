# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0019_auto_20160222_0726'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdetail',
            name='contributor_uid',
            field=models.IntegerField(db_index=True, null=True, blank=True),
        ),
    ]
