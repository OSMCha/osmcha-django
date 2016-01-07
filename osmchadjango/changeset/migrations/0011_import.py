# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0010_auto_20151227_1306'),
    ]

    operations = [
        migrations.CreateModel(
            name='Import',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('start', models.IntegerField()),
                ('end', models.IntegerField()),
                ('date', models.DateTimeField(verbose_name='Date of the import', auto_now_add=True)),
            ],
        ),
    ]
