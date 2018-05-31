# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0024_auto_20160226_0738'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuspiciousFeature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.IntegerField(null=True, blank=True)),
                ('osm_id', models.IntegerField()),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('geojson', models.TextField()),
                ('changeset', models.ForeignKey(to='changeset.Changeset', on_delete=models.deletion.CASCADE)),
                ('reasons', models.ManyToManyField(to='changeset.SuspicionReasons')),
            ],
        ),
    ]
