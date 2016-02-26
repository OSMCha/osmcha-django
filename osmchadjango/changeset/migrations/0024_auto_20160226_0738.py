# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0023_userdetail_contributor_uid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdetail',
            name='changesets_mapping_days',
            field=models.CharField(max_length=128, null=True, blank=True),
        ),
    ]
