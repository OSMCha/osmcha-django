# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0016_auto_20160217_1004'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userdetail',
            old_name='blocks',
            new_name='contributor_blocks',
        ),
        migrations.RenameField(
            model_name='userdetail',
            old_name='name',
            new_name='contributor_name',
        ),
        migrations.RemoveField(
            model_name='userdetail',
            name='no',
        ),
        migrations.RemoveField(
            model_name='userdetail',
            name='since',
        ),
        migrations.AddField(
            model_name='userdetail',
            name='changeset_no',
            field=models.IntegerField(help_text='Number of changesets', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='contributor_since',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
