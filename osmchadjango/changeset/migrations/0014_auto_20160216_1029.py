# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0013_auto_20160125_1021'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1000)),
                ('blocks', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='changeset',
            name='user_detail',
            field=models.ForeignKey(blank=True, to='changeset.UserDetail', on_delete=models.deletion.SET_NULL, null=True),
        ),
    ]
