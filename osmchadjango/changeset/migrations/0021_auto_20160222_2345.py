# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0020_auto_20160222_2342'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changeset',
            name='bbox',
            field=django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='comment',
            field=models.CharField(max_length=1000, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='create',
            field=models.IntegerField(null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='delete',
            field=models.IntegerField(null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='editor',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='imagery_used',
            field=models.CharField(max_length=1000, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='modify',
            field=models.IntegerField(null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='source',
            field=models.CharField(max_length=1000, null=True, blank=True),
        ),
    ]
