# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Changeset',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('user', models.CharField(max_length=1000)),
                ('editor', models.CharField(max_length=255)),
                ('comment', models.CharField(max_length=255, blank=True)),
                ('date', models.DateTimeField()),
                ('created', models.IntegerField()),
                ('modified', models.IntegerField()),
                ('deleted', models.IntegerField()),
                ('bbox', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
                ('harmful', models.NullBooleanField()),
                ('checked', models.BooleanField(default=False)),
                ('check_date', models.DateTimeField(null=True, blank=True)),
                ('check_user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.deletion.SET_NULL, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='SuspicionReasons',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='changeset',
            name='reasons',
            field=models.ManyToManyField(to='changeset.SuspicionReasons'),
        ),
    ]
