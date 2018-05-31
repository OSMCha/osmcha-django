# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0017_auto_20160217_1102'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userdetail',
            old_name='changeset_no',
            new_name='changesets_no',
        ),
        migrations.AddField(
            model_name='userdetail',
            name='changesets_changes',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='changesets_f_tstamp',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='changesets_l_tstamp',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='changesets_mapping_days',
            field=models.CharField(default='', max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userdetail',
            name='contributor_traces',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='nodes_c',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='nodes_d',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='nodes_m',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='relations_c',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='relations_d',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='relations_m',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='ways_c',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='ways_d',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userdetail',
            name='ways_m',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
