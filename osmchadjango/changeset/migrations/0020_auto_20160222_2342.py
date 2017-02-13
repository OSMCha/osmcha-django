# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0019_auto_20160222_0726'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changeset',
            name='bbox',
            field=django.contrib.gis.db.models.fields.PolygonField(srid=4326, blank=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='create',
            field=models.IntegerField(db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='date',
            field=models.DateTimeField(blank=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='delete',
            field=models.IntegerField(db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='editor',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='modify',
            field=models.IntegerField(db_index=True, blank=True),
        ),
    ]
