# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changeset',
            name='reasons',
            field=models.ManyToManyField(related_name='changesets', to='changeset.SuspicionReasons'),
        ),
    ]
