# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0018_auto_20160218_0218'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changeset',
            name='create',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='delete',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='is_suspect',
            field=models.BooleanField(db_index=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='modify',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='userdetail',
            name='changesets_changes',
            field=models.IntegerField(db_index=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='userdetail',
            name='changesets_no',
            field=models.IntegerField(help_text='Number of changesets', null=True, db_index=True, blank=True),
        ),
    ]
