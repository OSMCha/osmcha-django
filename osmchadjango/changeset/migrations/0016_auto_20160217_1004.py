# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0015_auto_20160217_0511'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdetail',
            name='no',
            field=models.IntegerField(help_text='Number of Changesets', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='since',
            field=models.DateTimeField(help_text='Mapper since', null=True, blank=True),
        ),
    ]
