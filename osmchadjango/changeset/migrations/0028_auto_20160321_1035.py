# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0027_auto_20160321_0605'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdetail',
            name='contributor_img',
            field=models.CharField(max_length=512, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='nodes_rank',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='notes_closed',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='notes_commented',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='notes_opened',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='relations_rank',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='ways_rank',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
