# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0004_auto_20150828_0128'),
    ]

    operations = [
        migrations.RenameField(
            model_name='changeset',
            old_name='created',
            new_name='create',
        ),
        migrations.RenameField(
            model_name='changeset',
            old_name='deleted',
            new_name='delete',
        ),
        migrations.RenameField(
            model_name='changeset',
            old_name='modified',
            new_name='modify',
        ),
    ]
