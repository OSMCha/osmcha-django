# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0009_auto_20151226_0012'),
    ]

    operations = [
        migrations.RenameField(
            model_name='changeset',
            old_name='harmfull',
            new_name='harmful',
        ),
    ]
